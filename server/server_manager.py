from config.configs import MCPropertiesParser, ObsidiaConfigParser
from server.server import ServerRunner
from typing import Union, List
from datetime import datetime
import asyncio
import shutil
import time
import os


class ServerManager:
    '''
    Create and run a server given the directory.

    Parameters
    ----------
    server_directory: `str`
        The directory of the server, the server's jar and server.properties should be one layer below (e.g. server_directory/server.jar)
    config_file: `str`
        The basename of the config file for the server manager, default "obsidia.conf"

    Attributes
    ----------
    server: `ServerRunner`
        The server being run.
        Note that it is recommended to use ServerManager's write method, not ServerRunners.
    config_file: `str`
        The config file in use
    server_directory: `str`
        The absolute path to the server directory containing the jar file
    '''

    def __init__(self, server_directory: str, config_file: str = "obsidia.conf"):
        self.server_directory = os.path.abspath(server_directory)
        self.config_file = config_file
        self._server_should_be_running = False
        self._save_is_off = False
        self._doing_backup = False
        self._reset_server_startup_vars()
        self.server = ServerRunner(self.server_directory, executable=self._executable, jarname=self._server_jar, args=self._args)  # type: ignore

    def _reset_server_startup_vars(self):
        '''Initial vars are those that need to be reset every time the server is launched.'''
        self._sent_stop_signal = False
        self._is_autorestarting = False
        self._load_server_information()
        self.reload_configs()

    def write(self, command: str):
        '''Sends a command to the server.'''
        command = command.strip()
        if command == "stop":
            self._sent_stop_signal = True
            return self.server.stop()
        else:
            return self.server.write(command)

    def stop_server(self):
        '''Sends a stop command to the server.'''
        self._sent_stop_signal = True
        return self.server.stop()

    def restart_server(self):
        '''Sends a stop command to the server, but restarts.'''
        self._is_autorestarting = True
        return self.server.stop()

    async def start_server(self):
        '''
        Runs the server and monitors it for crashing/backups/etc.

        Blocks until the monitor shuts down (survives restarts, but not shut downs).

        Do not close the server with a keyboard interrupt in the monitor!
        If you must do so, call clean_up_keyboard_interrupt().
        '''
        self._server_should_be_running = True
        self._reset_server_startup_vars()
        await self._spawn_server()
        await self._running_loop()
        await self._update_server_listeners("Server shut down")

    def clean_up_keyboard_interrupt(self):
        '''
        If the server was shut down with a keyboard interrupt, call this to finish somewhat gracefully.
        Most likely the server itself caught the ctrl C and closed, but this may interfere with saving.
        It is not recommended to have to call this function in the first place, but is provided just in case.
        '''
        self.stop_server()
        self._server_should_be_running = False

    async def _spawn_server(self):
        self._server_start_time = self._get_current_time()
        await self.server.start()

    async def _running_loop(self):
        while (self.server_should_be_running()):
            time_until_restart = self._get_offset_until(self._autorestart_datetime)
            time_until_backup = self._get_offset_until(self._backup_datetime)
            while (await self.server_running()):
                await asyncio.sleep(5)  # longer causes high delay between server shutdown and server appearing shut down in _server_should_be_running

                if self._do_autorestart and not self._doing_backup:
                    new_time_until_restart = self._get_offset_until(self._autorestart_datetime)
                    if new_time_until_restart > time_until_restart:  # passed timestamp, it's sending next occurrence
                        self.write("say Restarting now!")
                        self._is_autorestarting = True
                        self.server.stop()
                    elif new_time_until_restart <= 60 and time_until_restart > 60:
                        self.write("say Restarting in 60 seconds!")
                    elif new_time_until_restart <= 300 and time_until_restart > 300:
                        self.write("say Restarting in 5 minutes.")
                    elif new_time_until_restart <= 900 and time_until_restart > 900:
                        self.write("say Restarting in 15 minutes.")
                    time_until_restart = new_time_until_restart

                if self._do_backups:
                    new_time_until_backup = self._get_offset_until(self._backup_datetime)
                    if new_time_until_backup > time_until_backup:  # passed timestamp, it's sending next occurrence
                        await self.backup_world()
                    time_until_backup = new_time_until_backup

                if self._save_is_off and not self._doing_backup:  # edge case for backing up as server shuts down
                    self.set_saving(True)

            # clean up after the server closes based on whether or not we need to restart
            if not self._doing_backup:
                if self._is_autorestarting:
                    await self._update_server_listeners("Automatically restarting")
                    self._reset_server_startup_vars()
                    await self._spawn_server()
                elif self._restart_on_crash and not self._sent_stop_signal:
                    await self._update_server_listeners("Detected server crash: Restarting")
                    self._reset_server_startup_vars()
                    await self._spawn_server()
                else:
                    self._server_should_be_running = False

    def _get_current_time(self) -> int:
        return int(time.time())

    def _get_offset_until(self, timestamp: Union[str, None]) -> int:
        '''Parse SMTWRFD HHMM timestamp and check how far away it is from now, in seconds.'''
        if timestamp == None:
            return -1
        offset = 0
        current_time = datetime.now()
        timestamp_parts = timestamp.split(" ")
        days = timestamp_parts[0]
        hour = int(timestamp_parts[1][:2])
        mins = int(timestamp_parts[1][2:])
        offset += (hour - current_time.hour) * 3600
        offset += (mins - current_time.minute) * 60
        offset -= current_time.second
        current_day_num = (current_time.weekday() + 1) % 7
        for i in range(14 - current_day_num):  # 14 not 7 because we have to account for wrapping if we skip the one day a week it runs
            # check offset < 0 because we need to skip if we already passed the timestamp on the first day checked (today)
            if "SMTWRFDSMTWRFD"[current_day_num + i] not in days or offset < 0:
                offset += 86400
            else:
                break
        return offset

    async def backup_world(self, backup_name: Union[str, None] = None):
        '''
        Creates a backup of the world in the backup directory.

        If backup_name is not set, then it will use a timestamp and delete old backups to maintain max.
        If it is set, then that name will be used (after checking that it isn't already in use!).
        '''
        # if we save-off/save-on while changing state, it's possible to permanently disable saving until the next backup
        while self.server_should_be_running() and not self.server.is_ready() and await self.server_running():
            await self._update_server_listeners("Waiting for world backup (server changing state)")
            await asyncio.sleep(3)
        self._doing_backup = True
        os.makedirs(self.backup_directory, exist_ok=True)
        # turn off autosaving while doing the backup to prevent conflicts
        self.set_saving(False)
        await self._update_server_listeners("Backing up world")
        # timestamp backup
        if backup_name == None:
            if self._max_backups > 0:
                # hacky way to check which backups were created automatically and use the timestamp name
                backup_list = self.list_backups()
                total_backups = 0
                oldest_backup = 1000000000000000000000  # eh good enough
                for backup in backup_list:
                    try:
                        backup = int(backup)
                    except:
                        pass
                    else:
                        oldest_backup = min(backup, oldest_backup)
                        total_backups += 1
                if total_backups >= self._max_backups:
                    self._delete_world(os.path.join(self.backup_directory, f"{oldest_backup}"))
            backup_dir = os.path.join(self.backup_directory, f"{self._get_current_time()}")
        # named backup
        else:
            backup_name = backup_name.strip()
            if backup_name in os.listdir(self.backup_directory):
                await self._update_server_listeners("Failed to back up world: A backup with that name already exists")
                return "Failed to back up world: A backup with that name already exists"
            else:
                backup_dir = os.path.join(self.backup_directory, backup_name)
        try:
            for world in self._worlds:
                self._copy_world(os.path.join(self.server_directory, world), os.path.join(backup_dir, world))
        except Exception as e:
            await self._update_server_listeners(f"Failed to back up world: {e}")
            return f"Failed to back up world: {e}"
        # turn back on autosaving
        # NOTE: should probably save the initial state of it and set it back to that, rather than forcing it on (config?)
        self.set_saving(True)
        self._doing_backup = False
        await self._update_server_listeners("Backup completed")

    def list_backups(self) -> Union[str, List[str]]:
        '''Returns a list of world backups.'''
        try:
            return os.listdir(self.backup_directory)
        except FileNotFoundError:
            return ""

    async def restore_backup(self, backup: str):
        '''
        Restores a backup with the specified name.

        Fails if the server is currently running, or if the specified backup does not exist (RuntimeError/FileNotFoundError).
        (Note that only the existance of the directory pointed to is checked. It may be empty.)
        '''
        if self.server_should_be_running():
            raise RuntimeError("Cannot restore backup while server is running.")
        backup_list = self.list_backups()
        if backup in backup_list:
            await self._update_server_listeners(f"Restoring backup {backup}")
            for world in os.listdir(os.path.join(self.backup_directory, backup)):
                world_dir = os.path.join(self.server_directory, world)
                backup_dir = os.path.join(self.backup_directory, os.path.join(backup, world))
                self._delete_world(world_dir)
                self._copy_world(backup_dir, world_dir)
            await self._update_server_listeners("Restoration complete")
        else:
            raise FileNotFoundError("Specified backup does not exist.")

    def delete_backup(self, backup: str):
        '''
        Deletes a backup with the specified name.

        Raises FileNotFoundError if the folder does not exist.
        '''
        backup_list = self.list_backups()
        if backup in backup_list:
            backup_dir = os.path.join(self.backup_directory, backup)
            self._delete_world(backup_dir)
        else:
            raise FileNotFoundError("Specified backup does not exist.")

    def set_saving(self, state: bool):
        if self.server.is_ready():
            try:
                if state:
                    self.write("save-on")
                else:
                    self.write("save-off")
                self._save_is_off = not state
            except Exception:
                pass

    def _copy_world(self, source, destination):
        shutil.copytree(source, destination, ignore=shutil.ignore_patterns("*.lock"))

    def _delete_world(self, world):
        shutil.rmtree(world)

    def server_should_be_running(self) -> bool:
        '''Returns true if the server should be running (but might be restarting), false otherwise.'''
        return self._server_should_be_running

    async def server_running(self) -> bool:
        '''Returns true if the server is currently running, false otherwise.'''
        if self.server == None:
            return False
        return self.server.is_active()

    def server_active(self) -> bool:
        '''Returns true if the server is active and ready to take commands.'''
        if self.server == None:
            return False
        return self.server.is_ready()

    def _load_server_information(self):
        try:
            config = MCPropertiesParser(os.path.join(self.server_directory, "server.properties"))
            self._motd = config.get("motd")
            if self._motd != None:
                self._motd = self._motd.strip()
            try:
                self._port = int(config.get("query.port"))  # type: ignore
            except TypeError:  # in case the version doesn't have a query port, such as FTB 1.7.10
                self._port = int(config.get("server-port"))  # type: ignore - further error -> crash
        except FileNotFoundError:
            raise FileNotFoundError("You must run your servers before using the server manager.")

    async def _update_server_listeners(self, message: str):
        timestamp = f"[{datetime.now().strftime('%H:%M:%S')}] [Manager]: "
        # headache: since the loop gets stuck in monitoring, it couldn't run this task
        # to fix: make sure that the monitor has an awaitable that lets other tasks go
        await self.server._update_listeners(timestamp + message)

    def reload_configs(self):
        '''Reload the configs from the current config file.'''
        config = ObsidiaConfigParser(self.config_file)

        # NOTE: the config items could be None or invalid in some cases, but crashing is fine in these circumstances
        try:
            self._server_jar = config.get("Server Information", "server_jar")
            self._executable = config.get("Server Information", "executable")
            self._args = config.get("Server Information", "args").split(" ")  # type: ignore
            self._worlds = config.get("Server Information", "world_folders").split(",")  # type: ignore
            for i in range(len(self._worlds)):
                self._worlds[i] = self._worlds[i].strip()

            self._do_autorestart = config.get("Restarts", "autorestart").lower() == "true"  # type: ignore
            self._autorestart_datetime = config.get("Restarts", "autorestart_datetime")
            self._restart_on_crash = config.get("Restarts", "restart_on_crash").lower() == "true"  # type: ignore

            self._do_backups = config.get("Backups", "backup").lower() == "true"  # type: ignore
            self._max_backups = int(config.get("Backups", "max_backups"))  # type: ignore
            self._backup_datetime = config.get("Backups", "backup_datetime")
            self.backup_directory = os.path.join(self.server_directory, config.get("Backups", "backup_folder"))  # type: ignore
        except Exception as e:
            raise RuntimeError(f"Error reading configs for server: {e}")

    async def uptime(self) -> int:
        '''Get the time the server has been running since it was last started, in seconds.'''
        if (await self.server_running()):
            return self._get_current_time() - self._server_start_time
        return 0

    def get_latest_log(self) -> List[str]:
        '''Get a list of all console logs for the latest server session.'''
        try:
            log_file = open(os.path.join(self.server_directory, "logs", "latest.log"), "r")
        except IOError:
            return ["No latest log found."]
        return log_file.readlines()

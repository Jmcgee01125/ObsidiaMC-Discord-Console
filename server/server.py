from typing import Union, List
import subprocess
import threading
import asyncio
import queue
import os


class ServerRunner:
    '''
    Create an object referencing a running server.

    Parameters
    ----------
    server_directory: `str`
        The path to the directory of this server's jar file
    executable: `str`
        The java executable to start the server with, default "java"
    jarname: `str`
        The server jar, default "server.jar"
    args: `list[str]`
        A list of console arguments, such as -Xmx2G (You may need to add -server before some options)
        These arguments are parsed as java <args> -jar <jarname> -nogui

    Attributes
    ----------
    server_directory: `str`
        The absolute path to the server directory containing the jar file
    server_name: `str`
        The name of the server being run (note that this is not necessarily read from the config file)
    '''

    def __init__(self, server_directory: str, executable: str = "java", jarname: str = "server.jar", args: List[str] = []):
        self._is_ready = False
        self.server_directory = os.path.abspath(server_directory)
        self._executable = executable
        self._jarname = jarname
        self._args = args
        self._server = None
        self._listeners = set()

    async def run(self):
        '''Alias to start.'''
        await self.start()

    async def start(self):
        '''Start the server process if not already started.'''
        if (self._server == None or not self.is_active()):
            self._server = subprocess.Popen(f"{self._executable} {' '.join(self._args)} -jar {self._jarname} -nogui",
                                            stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True, cwd=self.server_directory)
            threading.Thread(target=self._start_async_log_listener, name="ServerLogListener", daemon=True).start()

    def _start_async_log_listener(self):
        asyncio.run(self._listen_for_logs())

    async def _listen_for_logs(self):
        '''
        Monitors stdout for logs, reporting them to listeners.

        This function should only be called once per server thread.
        '''
        while (self.is_active()):
            try:
                line = self._server.stdout.readline().decode().strip()  # type: ignore - also blocks until data exists
            except ValueError:  # info->buf could be NUL
                pass
            else:
                await self._update_listeners(line)
                if not self._is_ready:
                    await self._check_if_ready(line)
        # process is dead
        self._is_ready = False
        self._server = None

    async def _check_if_ready(self, msg: str):
        if "INFO]: Done (" in msg:
            self._is_ready = True
        elif "INFO]: You need to agree to the EULA" in msg:
            self.kill()

    async def _update_listeners(self, msg: str):
        for listener in self._listeners:
            listener.update(msg)

    def add_listener(self, listener_object):
        '''
        Subscribe the given object to be notified on this thread whenever there is a new message in the server console.

        The subscriber must contain the function "update(self, message: `str`)", otherwise throws AttributeError when adding listener.
        '''
        try:
            listener_object.update(f"Subscribed to server logs.")
        except (AttributeError, TypeError):
            raise AttributeError("Listener does not contain update(self, message: str) attribute.")
        else:
            self._listeners.add(listener_object)

    def remove_listener(self, listener_object):
        '''Unsubscribes an object from updates.'''
        try:
            self._listeners.remove(listener_object)
        except KeyError:
            pass
        else:
            try:
                listener_object.update(f"Unsubscribed from server logs.")
            except (AttributeError, TypeError):
                raise AttributeError("Listener does not contain update(self, message: str) attribute.")

    def is_active(self) -> bool:
        '''Check if the server's thread is currently active (not necessarily that the server is running).'''
        return self._server != None and self._server.poll() == None

    def is_ready(self) -> bool:
        '''Check if the server is currently started, i.e. players are able to join.'''
        return self._is_ready

    def write(self, command: str):
        '''Write a single line command to the server console. Newline automatically appended.'''
        try:
            self._server.stdin.write(bytes(f"{command}\n", "utf-8"))  # type: ignore
            self._server.stdin.flush()  # type: ignore
        except Exception as e:
            return f"Write failed: {e}"

    def stop(self):
        '''
        Stop the server, ALWAYS call this before closing the server (unless you've sent stop via rcon).

        Note that is_restarting only changes the message that users see, and does not actually restart.
        '''
        try:
            self._server.stdin.flush()  # type: ignore
            self._server.communicate(b"stop\n", timeout=5)  # type: ignore
        except Exception as e:
            return f"Stop command failed: {e} \t(Server may already be offline.)"
        finally:
            self._is_ready = False

    def kill(self):
        '''Kills the server process. DO NOT RUN THIS UNLESS YOU ABSOLUTELY HAVE TO.'''
        if self._server != None:
            self._server.kill()
        self._is_ready = False

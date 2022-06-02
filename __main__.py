from server.server_manager import ServerManager
from config.configs import ObsidiaConfigParser
import bot.discord_server as discord_server
from server.server import ServerListener
import threading
import asyncio
import time
import os


class ConsolePrintListener:
    def __init__(self, manager: ServerManager, log_file: str):
        self._manager: ServerManager = manager
        self._listener: ServerListener = ServerListener(manager.server)
        self._should_shut_down: bool = False
        self._logfile: str = log_file

    def start(self):
        threading.Thread(target=self._print_queue, name="ConsolePrintListener").start()

    def _print_queue(self):
        self._listener.subscribe()
        while (not self._should_shut_down):
            asyncio.run(asyncio.sleep(0.05))
            if (self._listener.has_next()):
                self._print_and_log_entry(self._listener.next())
        self._print_and_log_entry("Closing server console listener")

    def _print_and_log_entry(self, entry: str):
        entry = f"{self._get_timestamp()} {entry}"
        print(entry)
        with open(self._logfile, "a") as log:
            log.writelines(f"{entry}\n")

    def _get_timestamp(self):
        return time.strftime("[%Y-%m-%d]", time.localtime())

    def stop(self):
        self._should_shut_down = True


if __name__ == "__main__":
    print("Starting main")

    os.chdir(os.path.dirname(__file__))  # HACK, but it works to get the directory relative to this accurately without breaking root dirs
    config_file = os.path.join("config", "obsidia.conf")
    configs = ObsidiaConfigParser(config_file)
    server_dir = configs.get("Server", "directory")
    name = configs.get("Server", "name")
    ip = configs.get("Server", "ip")

    logging_directory = "log"
    manager_log_file = os.path.join(logging_directory, f"{int(time.time())}.log")
    os.makedirs(logging_directory, exist_ok=True)

    manager = ServerManager(server_dir, config_file)
    listener = ConsolePrintListener(manager, manager_log_file)
    listener.start()

    discord_server.prep_client(manager, os.path.join("config", "operators.txt"), os.path.join("config", "owners.txt"), manager_log_file, name, ip)
    discord_server.start_client()  # block

    discord_server.cleanup_client()
    listener.stop()
    stop_server_result = manager.stop_server()
    if stop_server_result != None:
        print(stop_server_result)

    print("Closing main")

from server.server_manager import ServerManager
from config.configs import ObsidiaConfigParser
import bot.discord_server as discord_server
from typing import Union
import threading
import asyncio
import time
import os


class ConsolePrintListener:
    def __init__(self, manager: ServerManager, log_file: str):
        self._manager: ServerManager = manager
        self._logfile: str = log_file

    def start(self):
        self._manager.server.add_listener(self)

    def update(self, message: str):
        self._print_and_log_entry(message)

    def _print_and_log_entry(self, entry: Union[str, None]):
        entry = f"{self._get_timestamp()} {entry}"
        print(entry)
        with open(self._logfile, "a") as log:
            log.writelines(f"{entry}\n")

    def _get_timestamp(self):
        return time.strftime("[%Y-%m-%d]", time.localtime())


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

    if server_dir == None:
        print("Server directory not provided")
        exit(1)
    manager = ServerManager(server_dir, config_file)
    listener = ConsolePrintListener(manager, manager_log_file)
    listener.start()

    discord_server.prep_client(manager, os.path.join("config", "operators.txt"), os.path.join("config", "owners.txt"), manager_log_file, name, ip)
    discord_server.start_client()  # block

    discord_server.cleanup_client()
    stop_server_result = manager.stop_server()
    if stop_server_result != None:
        print(stop_server_result)

    print("Closing main")

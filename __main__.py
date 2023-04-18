from server.server_manager import ServerManager
from config.configs import ObsidiaConfigParser
import bot.discord_server as discord_server
from loguru import logger
from typing import Union
import time
import os


class ConsolePrintListener:
    def __init__(self, manager: ServerManager):
        self._manager: ServerManager = manager

    def start(self):
        self._manager.server.add_listener(self)

    def update(self, message: str):
        self._print_and_log_entry(message)

    def _print_and_log_entry(self, entry: Union[str, None]):
        logger.info(entry)


import sys
if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))  # HACK, but it works to get the directory relative to this accurately without breaking root dirs

    logging_directory = "log"
    manager_log_file = os.path.join(logging_directory, f"{int(time.time())}.log")
    os.makedirs(logging_directory, exist_ok=True)

    logger.remove()
    logger.add(manager_log_file, rotation="1 week", compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}")
    logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

    logger.info("Starting main")

    config_file = os.path.join("config", "obsidia.conf")
    configs = ObsidiaConfigParser(config_file)
    server_dir = configs.get("Server", "directory")
    name = configs.get("Server", "name")
    ip = configs.get("Server", "ip")

    if server_dir == None:
        logger.error("Server directory not provided")
        exit(1)
    manager = ServerManager(server_dir, config_file)
    listener = ConsolePrintListener(manager)
    listener.start()

    discord_server.prep_client(manager, os.path.join("config", "operators.txt"), os.path.join("config", "owners.txt"), manager_log_file, name, ip)
    discord_server.start_client()  # block

    discord_server.cleanup_client()
    stop_server_result = manager.stop_server()
    if stop_server_result != None:
        logger.warning(stop_server_result)

    logger.info("Closing main")

from server.server_manager import ServerManager
from config.configs import ObsidiaConfigParser
import bot.discord_server as discord_server
from server.server import ServerListener
import threading
import os


class ConsolePrintListener:
    def __init__(self, manager: ServerManager):
        self._manager: ServerManager = manager
        self._listener: ServerListener = ServerListener(manager.server)
        self._should_shut_down: bool = False

    def start(self):
        threading.Thread(target=self._print_queue, name="ConsolePrintListener").start()

    def _print_queue(self):
        self._listener.subscribe()
        while (not self._should_shut_down):
            if (self._listener.has_next()):
                print(self._listener.next())
        print("Closing server console listener")

    def stop(self):
        self._should_shut_down = True


if __name__ == "__main__":
    config_dir = os.path.join(os.path.dirname(__file__), "config")  # HACK, but it works to get the config dir accurately
    config_file = os.path.join(config_dir, "obsidia.conf")
    configs = ObsidiaConfigParser(config_file)
    server_dir = configs.get("Server", "directory")
    ip = configs.get("Server", "ip")

    manager = ServerManager(server_dir, config_file)
    listener = ConsolePrintListener(manager)
    listener.start()

    discord_server.prep_client(manager, os.path.join(config_dir, "operators.txt"), os.path.join(config_dir, "owners.txt"), ip)
    discord_server.start_client()

    listener.stop()
    stop_server_result = manager.stop_server()
    if stop_server_result != None:
        print(stop_server_result)
    print("Closing main")

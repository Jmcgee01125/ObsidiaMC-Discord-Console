from server.server_manager import ServerManager
from server.server_ping import StatusPing
from bot.servercog import ServerCog
from bot.pingcog import PingCog
from dotenv import load_dotenv
import nextcord
import asyncio
import os


load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
INTENTS = nextcord.Intents.none()
if DISCORD_TOKEN == None:
    raise RuntimeError("Could not find DISCORD_TOKEN in .env file. Did you create a bot?")


async def _presence_update_loop(pinger: StatusPing, server_name: str):
    while not _stop_presence_updater:
        response: dict = pinger.get_status()
        if response == None:
            status = "offline"
        else:
            status = f"{response['players']['online']}/{response['players']['max']}"
        await client.change_presence(activity=nextcord.Game(name=f"{server_name} | {status}"))
        await asyncio.sleep(60)


def prep_client(manager: ServerManager, operators_file: str, owners_file: str, manager_logfile: str, name: str = None, ip: str = None):
    '''Prepare the client with applicable commands'''
    if name == None and ip == None:  # neither name nor ip
        server_name = "MC Server"
        server_ip = None
    elif ip == None or ip == "":  # name, but no ip
        server_name = name
        server_ip = None
    else:  # ip, but no name
        server_name = ip
        server_ip = f"{ip}:{manager._port}"
    pinger: StatusPing = StatusPing(port=manager._port, timeout=2)

    global client
    client = nextcord.Client(intents=INTENTS)
    client.add_cog(PingCog(client))
    client.add_cog(ServerCog(client, manager, operators_file, owners_file, manager_logfile, pinger, server_name, server_ip))

    global _should_start_presence_updater, _stop_presence_updater
    _should_start_presence_updater = True
    _stop_presence_updater = False

    @client.event
    async def on_ready():
        print(f"Discord client connected as {client.user}")
        if _should_start_presence_updater:
            _should_start_presence_updater = False
            await _presence_update_loop(pinger, server_name)


def start_client():
    '''
    Run the client until it closes (blocking).

    Call prep_client before this.

    Send KeyboardInterrupt to call client.close() and return control.
    '''
    print("Starting Discord client. Don't forget to run /server start to boot your server.")
    c_run = asyncio.ensure_future(client.start(DISCORD_TOKEN))
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(c_run)
    except KeyboardInterrupt:
        print("Shutting down discord client")
        loop.run_until_complete(client.close())


def cleanup_client():
    '''
    Note that the client should first be killed by KeyboardInterrupt.

    This function exists to flag the presence updater to stop, as a cleanup function.
    '''
    global _stop_presence_updater
    _stop_presence_updater = True

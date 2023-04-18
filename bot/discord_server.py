from server.server_manager import ServerManager
from server.server_ping import StatusPing
from bot.servercog import ServerCog
from json import JSONDecodeError
from bot.pingcog import PingCog
from dotenv import load_dotenv
from loguru import logger
from typing import Union
import nextcord
import asyncio
import os


load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
INTENTS = nextcord.Intents.none()
if DISCORD_TOKEN == None:
    raise RuntimeError("Could not find DISCORD_TOKEN in .env file. Did you create a bot?")


async def _presence_update_loop(pinger: StatusPing, server_name: Union[str, None], manager: ServerManager):
    global _stop_presence_updater
    # wait until the server starts to do the first ping
    while not _stop_presence_updater and not manager.server_active():
        await asyncio.sleep(5)
    # ping every 60 seconds to update the status
    while not _stop_presence_updater:
        try:
            response = pinger.get_status()
        except JSONDecodeError:
            response = None  # possible to attempt ping during startup, would kill updater permanently
        if response == None:
            status = "offline"
        else:
            try:
                status = f"{response['players']['online']}/{response['players']['max']}"
            except KeyError:
                status = "?/?"
        try:
            await client.change_presence(activity=nextcord.Game(name=f"{server_name} | {status}"))
        except:
            pass
        await asyncio.sleep(60)


def _is_valid_value(value: Union[str, None]) -> bool:
    return value != None and value != ""


def prep_client(
        manager: ServerManager, operators_file: str, owners_file: str, manager_logfile: str,
        name: Union[str, None] = None, ip: Union[str, None] = None):
    '''Prepare the client with applicable commands'''
    valid_name = _is_valid_value(name)
    valid_ip = _is_valid_value(ip)
    if valid_name and valid_ip:  # name and ip
        server_name = name
        server_ip = f"{ip}:{manager._port}"
    elif valid_name:  # name, but no ip
        server_name = name
        server_ip = None
    elif valid_ip:  # ip, but no name
        server_name = ip
        server_ip = f"{ip}:{manager._port}"
    else:  # neither name nor ip
        server_name = "MC Server"
        server_ip = None

    pinger: StatusPing = StatusPing(port=manager._port, timeout=2)

    global client
    client = nextcord.Client(intents=INTENTS)
    client.add_cog(PingCog(client))
    client.add_cog(ServerCog(client, manager, operators_file, owners_file, manager_logfile, pinger, server_name, server_ip))

    global _should_start_presence_updater
    global _stop_presence_updater
    _should_start_presence_updater = True
    _stop_presence_updater = False

    @client.event
    async def on_ready():
        global _should_start_presence_updater
        logger.info(f"Discord client connected as {client.user}")
        # on_ready may be called multiple times, do not spawn multiple loops
        if _should_start_presence_updater:
            _should_start_presence_updater = False
            await _presence_update_loop(pinger, server_name, manager)


def start_client():
    '''
    Run the client until it closes (blocking).

    Call prep_client before this.

    Send KeyboardInterrupt to call client.close() and return control.
    '''
    logger.info("Starting Discord client. Don't forget to run /server start to boot your server.")
    c_run = asyncio.ensure_future(client.start(DISCORD_TOKEN))
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(c_run)
    except KeyboardInterrupt:
        logger.info("Shutting down discord client")
        loop.run_until_complete(client.close())


def cleanup_client():
    '''
    Note that the client should first be killed by KeyboardInterrupt.

    This function exists to flag the presence updater to stop, as a cleanup function.
    '''
    global _stop_presence_updater
    _stop_presence_updater = True

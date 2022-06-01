from server.server_manager import ServerManager
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


def prep_client(manager: ServerManager, operators_file: str, owners_file: str, manager_logfile: str, ip: str = None):
    '''Prepare the client with applicable commands'''
    if ip == None or ip == "":
        ip = "Minecraft"
        server_name = "Minecraft Server"
    else:
        server_name = f"{ip}:{manager._port}"

    global client
    client = nextcord.Client(intents=INTENTS)
    client.add_cog(PingCog(client))
    client.add_cog(ServerCog(client, manager, operators_file, owners_file, manager_logfile, server_name))

    @client.event
    async def on_ready():
        print(f"Client connected as {client.user}")
        await client.change_presence(activity=nextcord.Game(name=ip))


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

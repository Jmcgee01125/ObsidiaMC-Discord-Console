from server.server_manager import ServerManager
from bot.servercog import ServerCog
from bot.helpcog import HelpCog
from bot.pingcog import PingCog
from dotenv import load_dotenv
import nextcord
import asyncio
import os

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
INTENTS = nextcord.Intents.none()


def prep_client(manager: ServerManager, operators_file: str, owners_file: str, game_name: str = None):
    '''Prepare the client with applicable commands'''
    global client
    client = nextcord.Client(intents=INTENTS)
    client.add_cog(PingCog(client))
    client.add_cog(ServerCog(client, manager, operators_file, owners_file))
    client.add_cog(HelpCog(client))

    if game_name == None or game_name == "":
        game_name = "a game ( ͡° ͜ʖ ͡°)"

    @client.event
    async def on_ready():
        print(f"Client connected as {client.user}")
        await client.change_presence(activity=nextcord.Game(name=game_name))


def start_client():
    '''
    Run the client until it closes (blocking).

    Call prep_client before this.

    Send KeyboardInterrupt to call client.close() and return control.
    '''
    c_run = asyncio.ensure_future(client.start(DISCORD_TOKEN))
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(c_run)
    except KeyboardInterrupt:
        print("Shutting down discord client")
        loop.run_until_complete(client.close())

'''
Ping command cog

Cogs
----
PingCog
'''


from nextcord.ext import commands
from nextcord import Interaction
import nextcord


class PingCog (commands.Cog):
    '''
    Ping command cog

    Parameters
    ----------
    client: `nextcord.Client`
        Client this cog is applied to

    Commands
    --------
    ping()
    '''

    def __init__(self, client: nextcord.Client):
        self.client: nextcord.Client = client

    @nextcord.slash_command(name="ping", description="Ping the bot to get latency")
    async def _ping(self, interaction: Interaction):
        '''Ping the bot to get latency'''
        await interaction.send(f"Pong: {self.client.latency*1000} ms", ephemeral=True)

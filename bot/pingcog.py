'''
Ping command cog

Cogs
----
PingCog
'''


from bot.helpers.commandhelp import CommandHelp
from bot.helpers.embedhelper import EmbedField
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

    Methods
    -------
    report_help() -> `list[commandhelp.CommandHelp]`
        Report command help list
    '''

    def __init__(self, client: nextcord.Client):
        self.client: nextcord.Client = client

    @nextcord.slash_command(name="ping", description="Ping the bot to get latency")
    async def _ping(self, interaction: Interaction):
        '''Ping the bot to get latency'''
        await interaction.send(f"Pong: {self.client.latency*1000} ms", ephemeral=True)

    def report_help(self) -> list[CommandHelp]:
        '''Set up command help'''
        ping_general = EmbedField("ping", "Ping the bot for latency.", True)
        ping_specific = [EmbedField("ping", "Ping the bot and shows the latency.\nHidden command.")]
        ping = CommandHelp("ping", ping_general, ping_specific)
        return [ping]

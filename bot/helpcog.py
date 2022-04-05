'''
Help commands cog

Cogs
----
HelpCog
'''


from bot.helpers.embedhelper import EmbedField, build_embed
from bot.helpers.commandhelp import CommandHelp
import bot.helpers.symbols as symbols
from nextcord.ext import commands
from nextcord import Interaction
import nextcord


class HelpCog (commands.Cog):
    '''
    Help commands cog

    Should not know about other cogs, should instead rely on their helper functions

    Parameters
    ----------
    client: `nextcord.Client`
        Client this cog is applied to

    Commands
    --------
    help(command: `str`)

    Methods
    -------
    report_help() -> `list[commandhelp.CommandHelp]`
        Report command help list
    '''

    def __init__(self, client: nextcord.Client):
        self.client: nextcord.Client = client
        self.command_help_list: list[CommandHelp] = []

    @nextcord.slash_command(name="help", description="View command help")
    async def _help(self, interaction: Interaction,
                    command: str = nextcord.SlashOption(description="Specific command to get help on", required=False)):
        '''Show the help embed, including per-command help embeds'''
        # make commands report their help information if we don't already have it
        if len(self.command_help_list) == 0:
            self._load_help_from_cogs(self.client._client_cogs)
        fields = []
        title = "Help"
        # help on specific commands
        if command != None:
            command = command.strip().lower()  # user input moment
            for cmd in self.command_help_list:
                if command == cmd.name:
                    title = f"Help - {cmd.name.capitalize()}"
                    for field in cmd.sub_help:
                        fields.append(field)
                    break
            if len(fields) == 0:
                await interaction.response.send_message(f"Could not find command {command}.", ephemeral=True)
                return
        # general help list, show commands that are currently loaded
        # commands for this section should be marked as inline
        else:
            title = "Help - General"
            for cmd in self.command_help_list:
                fields.append(cmd.help)
            # since discord shows 3 per row, it gets weird if there's not a multiple of 3
            if len(fields) > 3:
                while len(fields) % 3 != 0:
                    fields.append(EmbedField(symbols.EMPTY_SPACE, symbols.EMPTY_SPACE, True))
        emb = build_embed(*fields, title=title)
        await interaction.response.send_message(embed=emb, ephemeral=True)

    def _load_help_from_cogs(self, cogs: list[nextcord.ClientCog]):
        '''Load commands from active cogs and save it to the command help list'''
        for cog in cogs:
            try:
                self.command_help_list.extend(cog.report_help())
            except AttributeError:
                print(f"Could not load help entries for cog: {cog}")

    def report_help(self) -> list[CommandHelp]:
        '''Set up command help'''
        help_general = EmbedField("help", "Show this help text.", True)
        help_specific = [EmbedField(
            "help (command:<command>)", "Shows this help text. Why are you trying to pry deeper?\nHidden command.")]
        help = CommandHelp("help", help_general, help_specific)
        return [help]

'''Contains a CommandHelp class used to embed help information for a cog'''


from bot.helpers.embedhelper import EmbedField


class CommandHelp:
    '''
    Helper class to hold details about a specific command

    Parameters
    ----------
    name: `str`
        name of the command
    help: `EmbedField` 
        field for the main command help window (simple descriptions per function), should be inline
    sub_help: `list[EmbedField]` 
        list of fields to show specific help on the command, will be presented as a single embedded block
    is_nsfw: `bool`, optional
        should this command should only be shown in nsfw channels (default: False)
    guilds: `list[int]`, optional
        guild ids that this command should be shown in (default: [] (global))
    '''

    def __init__(self, name: str, help: EmbedField, sub_help: list[EmbedField],
                 is_nsfw: bool = False, guilds: list[int] = []):
        self.name: str = name
        self.help: EmbedField = help
        self.sub_help: list[EmbedField] = sub_help
        self.is_nsfw: bool = is_nsfw
        self.guilds: list[int] = guilds

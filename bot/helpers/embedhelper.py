'''
Easier construction of Discord embeds

Methods
-------
build_embed(*fields: `EmbedHelper.EmbedField`, title: `str`, url: `str`, description: `str`,
thumbnail: `str`, image: `str`, color: Union[`int`, `nextcord.Color`]) -> `nextcord.Embed`
    Builds and returns an embeddable object

Classes
-------
EmbedField
    A field for embedding
'''

from typing import Union
import nextcord


class EmbedField:
    '''
    Create a field for embedding

    Attributes
    ----------
    name: `str`
        The title of this field
    value: `str`
        The text in this field
    inline: `bool`, optional
        Should this field be shown inline with others or on its own line?
    '''

    def __init__(self, name: str, value: str, inline: bool = False):
        self.name: str = name
        self.value: str = value
        self.inline: bool = inline


def build_embed(
        *fields: EmbedField, title: Union[str, None] = None,
        url: Union[str, None] = None,
        description: Union[str, None] = None,
        thumbnail: Union[str, None] = None,
        image: Union[str, None] = None,
        color: Union[int, nextcord.Color, None] = None) -> nextcord.Embed:
    '''
    Builds an embeddable object and returns it

    Parameters
    ----------
    *fields: `EmbedHelper.EmbedField`, optional
        Fields to put in the embed
    title: `str`, optional
        Title, empty to not show
    url: `str`, optional
        URL for the title link in https:// format, or empty for no link
    description: `str`, optional
        Description, or empty to not show
    thumbnail: `str`, optional
        URL for the thumbnail in https:// format, or empty to not show
    image: `str`, optional
        URL for the main image in https:// format, or empty to not show
    color: Union[`int`, `nextcord.Color`], optional
        Side ribbon color, or or empty to use default

    Returns
    -------
    embed: `nextcord.Embed`
        An embeddable object
    '''
    embed = nextcord.Embed(title=escape_ctrl_chars(title), url=url, description=escape_ctrl_chars(description), color=color)
    embed.set_thumbnail(url=thumbnail)
    embed.set_image(url=image)
    for field in fields:
        embed.add_field(name=escape_ctrl_chars(field.name), value=escape_ctrl_chars(field.value), inline=field.inline)
    return embed


def escape_ctrl_chars(text: Union[str, None]) -> Union[str, None]:
    '''
    Returns the provided text with any control characters prepended by a backslash

    If an nextcord.Embed.Empty or None is passed, returns unchanged
    '''
    if text == None:
        return text
    text = str(text)
    control_characters = ["*", "_", "~", "`", "|", ">"]
    escaped_str = ""
    for c in text:
        if c in control_characters:
            escaped_str += f"\\{c}"
        else:
            escaped_str += c
    return escaped_str

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
        self.inline: str = inline


def build_embed(*fields: EmbedField, title: str = nextcord.Embed.Empty, url: str = nextcord.Embed.Empty,
                description: str = nextcord.Embed.Empty, thumbnail: str = nextcord.Embed.Empty,
                image: str = nextcord.Embed.Empty, color: Union[int, nextcord.Color] = nextcord.Embed.Empty) -> nextcord.Embed:
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
    embed = nextcord.Embed(title=title, url=url, description=description, color=color)
    embed.set_thumbnail(url=thumbnail)
    embed.set_image(url=image)
    for field in fields:
        embed.add_field(name=field.name, value=field.value, inline=field.inline)
    return embed

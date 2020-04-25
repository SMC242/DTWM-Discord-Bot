"""Handles creating GUIs for users to interact with using reactions.

Inspired by Groovy"""

from discord import *
from typing import *
from datetime import datetime
from BenUtils import callbacks as ca
from asyncio import get_event_loop
from discord.ext.commands import Bot

class ReactMenu:
    """Create an interactable menu within an embedded discord.Message."""
    # ATTRIBUTES
    bound_messages: List[Tuple[datetime, 'ReactMenu']] = []

    def __init__(self, content: List[Tuple[str, Optional[str]]],
                 bot: Bot, channel: TextChannel,
                 on_select: ca.Callback = None, on_reject: ca.Callback = None,
                 **kwargs):
        """The Embed colour defaults to pink.

        ARGUMENTS
        content:
            The content to display per page.
            Format: (field_value, field_name)
        bot:
            The bot to use to maintain this menu.
        channel:
            The text channel to send the menu to.
        on_select:
            The callback to execute when the select reaction is chosen.
            A select reaction will be added if this is set.
        on_reject:
            The callback to execute when the reject reaction is chosen.
            A reject reaction will be added if this is set.
        kwargs:
            Any settings for discord.Embed.
        """
        self.content = content
        self.bot = bot
        self.on_select = on_select
        self.on_reject = on_reject

        # verify content's format
        for ele in content:
            if not isinstance(ele, (tuple, list)) or len(ele) != 2:
                raise ValueError("Incorrect content format")

        # create the Embed
        # default the colour to pink
        colour = kwargs.pop('colour', 13908894)
        embed = Embed(colour = colour,
                      **kwargs)
        embed.add_field(name = content[0][1], value = content[0][0])

        # send the initial message
        self._loop = get_event_loop()
        self._loop.create_task(channel.send(embed = embed))
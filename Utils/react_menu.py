"""Handles creating GUIs for users to interact with using reactions.

Inspired by Groovy"""

from discord import *
from typing import *
from datetime import datetime
from BenUtils import callbacks as ca
from asyncio import get_event_loop
from discord.ext.commands import Bot
from contextlib import suppress

class ReactMenu:
    """Create an interactable menu within an embedded discord.Message.
    
    ATTRIBUTES
    bound_messages: class attribute: List[Tuple[datetime, ReactMenu]]
        The messages that are currently being tracked.
        They're cleaned up every 10 minutes.
    emotes: Dict[int, str]
        The emotes' ids being used by this instance and their callback type's name.
        Callback types may be: next_content, last_content, on_select, on_reject.
        Example: 705987084535595028 : 'on_select'
    _bot: commands.Bot
        The bot instance to use.
    msg: Message
        The message bound to this instance.
    on_select: Callback
        The callback to call when the select emote is added.
    on_reject: Callback
        The callback to call when the reject emote is added.
    content: List[Tuple[str, Optional[str]]]
        The content to display per page.
        Format: (field_value, field_name)
    """
    # classtributes
    bound_messages: List[Tuple[datetime, 'ReactMenu']] = []

    def __init__(self, content: List[Tuple[str, Optional[str]]],
                 bot: Bot, channel: TextChannel,
                 on_select: ca.Callback = None, on_reject: ca.Callback = None,
                 next_emote_id: int = 705987084535595028, 
                 last_emote_id: int = 705986890787979284,
                 select_emote_id: int = 705986225206591549,
                 reject_emote_id: int = 705987303180599337,
                  **embed_settings):
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
        next_emote_id:
            The id for the emote to react to the message with
            to trigger next_content.
        last_emote_id:
            The id for the emote to react to the message with
            to trigger last_content.
        select_emote_id:
            The id for the emote to react to the message with
            to trigger select_content.
            This will be ignored if on_select is None.
        reject_emote_id:
            The id for the emote to react to the message with
            to trigger reject_content.
            This will be ignored if on_reject is None.
        embed_settings:
            Any settings for the discord.Embed.
        """
        self.content = content
        self._bot = bot
        self.on_select = on_select
        self.on_reject = on_reject

        # verify content's format
        for ele in content:
            if not isinstance(ele, (tuple, list)) or len(ele) != 2:
                raise ValueError("Incorrect content format")

        # default the colour to pink
        if "colour" not in embed_settings.keys():
            embed_settings["colour"] = 13908894

        # create the Embed with the first element of content
        embed = Embed(colour = colour,
                      **embed_settings)
        embed.add_field(name = content[0][1], value = content[0][0])

        # send the initial message
        self._loop = get_event_loop()
        self._loop.create_task(channel.send(embed = embed))

        # get the message that was just sent
        # Assumes that the bot experiences low traffic
        # since this will only be in 1 server
        self.msg = bot.user.history(limit = 1).flatten()

        # get emotes
        ids = (next_emote_id, last_emote_id,
                select_emote_id, reject_emote_id)
        emotes = [bot.get_emoji(id_) for id_ in ids]

        # set up instance's emotes
        callback_types = ("next", "last", "select", "reject")
        self.emotes = {id_ : ca_type for ca_type, id_ in 
                       zip(callback_types, ids)}

        # add the default reactions
        for emote in self.emotes[:2]:
            loop.create_task(bot.add_reaction(emote))

        # add the optional reactions
        if on_select:
            loop.create_task(bot.add_reaction(self.emotes[2]))
        if on_reject:
            loop.create_task(bot.add_reaction(self.emotes[3]))

        # add the listener after the reactions are set up
        self._bot.add_listener(self.on_reaction_add)

    async def on_reaction_add(self, reaction: Reaction, person: Member):
        """Check if the message reacted to is bound.
        If so, execute the reaction's callback if applicable."""
        # check if the message is bound
        if reaction.message in ReactMenu.bound_messages:
            # check if the reaction is valid
            with suppress(AttributeError):
                cb = getattr(self, self.emotes[reaction.id])
                # execute the reaction's callback if it exists
                if cb is not None:
                    await cb()
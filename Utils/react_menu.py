"""Handles creating GUIs for users to interact with using reactions.

Inspired by Groovy"""

from discord import *
from discord.ext import commands
from typing import *
from BenUtils import callbacks as ca
import asyncio
from contextlib import suppress
from Utils.memtils import get_title

class ReactMenu:
    """Create an interactable menu within an embedded discord.Message.
    
    ATTRIBUTES
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
    content: List[str]
        The content to display per page.
    field_names:  List[str]
        The names of each element of content.
    """

    def __init__(self, content: List[str],
                 bot: commands.Bot, channel: TextChannel,
                 field_names: List[str] = None,
                 on_select: ca.Callback = None, on_reject: ca.Callback = None,
                 last_emote_name: int = 712642258016534558,
                 next_emote_name: int = 712642257995431967,
                 select_emote_name: int = 712642257697767436,
                 reject_emote_name: int = 712642257697767458,
                  **embed_settings):
        """The Embed colour defaults to pink.

        ARGUMENTS
        content:
            The content to display per page.
        bot:
            The bot to use to maintain this menu.
        channel:
            The text channel to send the menu to.
        field_names:
            The titles of each element in content.
            Use None as a placeholder to keep the two lists parallel.
        on_select:
            The callback to execute when the select reaction is chosen.
            A select reaction will be added if this is set.
            It must take an instance of ReactMenu as its first argument.
        on_reject:
            The callback to execute when the reject reaction is chosen.
            A reject reaction will be added if this is set.
            It must take an instance of ReactMenu as its first argument.
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
        self.channel = channel
        self._bot = bot
        self.on_select = on_select
        self.on_reject = on_reject
        self._content_index = 0
        self._starting = True  # don't check its reactions until this is False

        # verify that field_names is parallel to content
        content_length = len(content)
        if field_names:
            if (content_length - len(field_names)) > 0:
                field_names + [None] * (content_length - len(field_names))
        else:
            field_names = [None] * content_length
        self.field_names = field_names

        # default the colour to pink
        if "colour" not in embed_settings:
            embed_settings["colour"] = 13908894
        self.embed_settings = embed_settings

        # create the Embed with the first element of content
        embed = Embed(**embed_settings)
        embed.add_field(name = field_names[0], value = content[0])

        asyncio.get_event_loop().create_task(self.__ainit__(channel, embed, next_emote_name,
                                                    last_emote_name, select_emote_name,
                                                    reject_emote_name, on_select, on_reject))

    async def __ainit__(self, channel, embed, next_emote_name,
                        last_emote_name, select_emote_name,
                        reject_emote_name, on_select, on_reject):
        """Send the initial message, bind to it, and set up the reactions"""
        # send the initial message
        await self.channel.send(embed = embed)

        # search for the bot's most recent message
        # and assume it's the ReactMenu
        bot_id = self._bot.user.id
        self.msg = None
        for historic_message in reversed(await self.channel.history(limit = 5).flatten()):
            if bot_id == historic_message.author.id:
                self.msg = historic_message

        # handle failure to find the message
        if not self.msg:
            return await channel.send(f"I misplaced my message. I am sorry...")

        # register the message
        handler = self._bot.get_cog("ReactMenuHandler")
        handler.bound_messages[self.msg.id] = self

        # add the default reactions
        emotes = [self._bot.get_emoji(id_) for id_ in (last_emote_name, next_emote_name,
                  select_emote_name, reject_emote_name)]
        for emote in emotes[:2]:
            await self.msg.add_reaction(emote)

        # add the optional reactions
        if on_select:
            await self.msg.add_reaction(emotes[2])
        if on_reject:
            await self.msg.add_reaction(emotes[3])

        # populate emotes dict
        await asyncio.sleep(1)
        self.msg = await self.channel.fetch_message(self.msg.id)  # refresh the Message instance once the reactions have been added
        self.emotes = {r.emoji.id: callback_type for r, callback_type in 
                       zip(self.msg.reactions, ("on_last", "on_next", "on_select", "on_reject"))}

        # mark self as ready
        self._starting = False

    @staticmethod
    async def on_next(self):
        if self._content_index < len(self.content) - 1:
            self._content_index += 1
            await self.msg.edit(embed = self.create_embed())

    @staticmethod
    async def on_last(self):
        if self._content_index > 0:
            self._content_index -= 1
            await self.msg.edit(embed = self.create_embed())

    def create_embed(self) -> Optional[Embed]:
        """Create an Embed from the content and field name
        at _content_index using embed_settings.
        
        RETURNS
        None: there is no more content
        Embed: the Embed was successfully created."""
        with suppress(IndexError):
            embed = Embed(**self.embed_settings)
            embed.add_field(name = self.field_names[self._content_index],
                            value = self.content[self._content_index])
            return embed
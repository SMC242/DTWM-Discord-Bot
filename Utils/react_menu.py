"""Handles creating GUIs for users to interact with using reactions.

Inspired by Groovy"""

from discord import *
from discord.ext import commands
from typing import *
from BenUtils import callbacks as ca
import asyncio
import random
from contextlib import suppress


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
    last_emote_id: int
        The id of the Emoji representing the back button.
    next_emote_id: int
        The id of the Emoji representing the forward button.
    select_emote_id: int
        The id of the Emoji representing the yes button.
    reject_emote_id: int
        The id of the Emoji representing the no button.
    embed_settings: dict
        The kwargs for the Embed instance.
    _channel: discord.TextChannel
        The channel that the ReactMenu is bound to.
    _content_index: int
        Which element in content is currently being displayed.

    """

    def __init__(self, content: List[str],
                 bot: commands.Bot,
                 channel: Union[TextChannel, commands.Context],
                 message_text: str = None,
                 field_names: List[str] = None,
                 on_select: ca.Callback = None, on_reject: ca.Callback = None,
                 last_emote_id: int = 712642258016534558,
                 next_emote_id: int = 712642257995431967,
                 select_emote_id: int = 712642257697767436,
                 reject_emote_id: int = 712642257697767458,
                 random_colour=False,
                 **embed_settings):
        """The Embed colour defaults to pink.

        ARGUMENTS
        content:
            The content to display per page.
        bot:
            The bot to use to maintain this menu.
        channel:
            The text channel to send the menu to.
            Contexts can be taken too as they act like
            TextChannel.
        message_text:
            What to send as the message.content.
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
        random_colour:
            Choose a random colour for the embed for each page.
        embed_settings:
            Any settings for the discord.Embed.
        """
        self.content = content
        self._channel = channel
        self._bot = bot
        self.on_select = on_select
        self.on_reject = on_reject
        self.random_colour = random_colour
        self._content_index = 0
        self._starting = True  # don't check its reactions until this is False
        self.next_emote_id = next_emote_id
        self.last_emote_id = last_emote_id
        self.select_emote_id = select_emote_id
        self.reject_emote_id = reject_emote_id
        self.msg = None

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
        embed = self.create_embed(*self.create_slice())

        asyncio.get_event_loop().create_task(self.__ainit__(embed, message_text,
                                                            next_emote_id, last_emote_id,
                                                            select_emote_id, reject_emote_id,
                                                            on_select, on_reject))

    async def __ainit__(self, embed, message_text,
                        next_emote_id, last_emote_id,
                        select_emote_id, reject_emote_id,
                        on_select, on_reject):
        """Send the initial message, bind to it, and set up the reactions"""
        # send the initial message
        self.msg = await self._channel.send(content=message_text,
                                            embed=embed)

        # register the message
        handler = self._bot.get_cog("ReactMenuHandler")
        handler.bound_messages[self.msg.id] = self

        # add the default reactions
        emotes = [self._bot.get_emoji(id_) for id_ in (last_emote_id, next_emote_id,
                                                       select_emote_id, reject_emote_id)]
        for emote in emotes[:2]:
            await self.msg.add_reaction(emote)

        # add the optional reactions
        if on_select:
            await self.msg.add_reaction(emotes[2])
        if on_reject:
            await self.msg.add_reaction(emotes[3])

        # populate emotes dict
        await asyncio.sleep(1)
        # refresh the Message instance once the reactions have been added
        self.msg = await self._channel.fetch_message(self.msg.id)
        self.emotes = {r.emoji.id: callback_type for r, callback_type in
                       zip(self.msg.reactions, ("on_last", "on_next", "on_select", "on_reject"))}

        # mark self as ready
        self._starting = False

    @staticmethod
    async def on_next(self):
        """Show the next content when the next button is clicked."""
        self._content_index += 1
        slices = self.create_slice()
        # prevent overflow
        if not slices[0]:
            self._content_index = 0
            slices = self.create_slice()
        await self.msg.edit(embed=self.create_embed(*slices))

    @staticmethod
    async def on_last(self):
        """Show the previous content when the back button is clicked."""
        self._content_index -= 1
        slices = self.create_slice()
        # prevent underflow
        if not slices[0]:
            self._content_index = len(self.content) - 1
            slices = self.create_slice()
        await self.msg.edit(embed=self.create_embed(*slices))

    def create_slice(self) -> Tuple[Optional[Any], Optional[Any]]:
        """Return a slice of self.content and self.field_names
        between self._content_index and self._content_index + 1.

        RETURNS
        The sliced list. It will be empty if the upper bound is fully out of range."""
        return (self.content[self._content_index:
                             self._content_index + 1],
                self.field_names[self._content_index:
                                 self._content_index + 1])

    def create_embed(self, content_slice: List[Any],
                     field_names_slice: List[Any]) -> Optional[Embed]:
        """Create an Embed from the content and field name
        at _content_index using embed_settings.

        RETURNS
        None: there is no more content
        Embed: the Embed was successfully created."""
        # generate a random colour
        if self.random_colour:
            self.embed_settings["colour"] = self.create_colour()

        embed = Embed(**self.embed_settings)
        embed.add_field(name=content_slice,
                        value=field_names_slice)
        return embed

    @staticmethod
    def create_colour() -> int:
        """Create a random colour and return its code"""
        digits = random.randint(1, 8)  # get a random length
        colour = "".join((str(random.randint(0, 9)) for i in range(digits)))

        # ensure that there isn't a leading 0
        i = 0
        while colour[i] == "0":
            colour = colour[i + 1:]
            i += 1

        # check that all zeroes weren't generated
        if len(colour) == 0:
            colour = ReactMenu.create_colour()

        # check that the number is in range
        # it's necessary to separate this because int doesn't have __len__
        int_colour = int(colour)
        if int_colour > 16777215:
            int_colour = ReactMenu.create_colour()
        return int_colour

    def __str__(self) -> str:
        """Converts self to a string."""
        return f"""({self.__class__} with attributes:
        _bot: {self._bot}
        msg: {self.msg}
        content: {self.content}
        field_names: {self.field_names}
        embed_settings: {self.embed_settings}
        _channel: {self._channel}
        _content_index: {self._content_index}
        next_emote_id: {self.next_emote_id}
        last_emote_id: {self.last_emote_id}
        select_emote_id: {self.select_emote_id:}
        reject_emote_id: {self.reject_emote_id}
        )"""


class ReactTable(ReactMenu):
    """Interactable tables via reactions as buttons."""

    def __init__(self, headers: Tuple[str], *args,
                 elements_per_page: int = 1, inline: bool = False,
                 **kwargs):
        """ARGUMENTS
        headers:
            The titles of each element for each row of
            content.
        elements_per_page:
            The number of elements from content to
            display per Embed.
        inline:
            Whether to display rows on one line or multiple.
        *args, **kwargs:
            See the docstring of ReactMenu.__init__"""
        self.headers = headers
        self.elements_per_page = elements_per_page
        self.inline = inline

        super().__init__(*args, **kwargs)

    def create_slice(self) -> List[List[Optional[Any]]]:
        """Return a slice of self.content between self._content_index
        and self._content_index + self.elements_per_page.
        It has to return an extra layer of list due to the design of ReactMenu.__init__

        RETURNS
        The sliced list. It will be empty if the upper bound is fully out of range."""
        return [self.content[self._content_index:
                             self._content_index + self.elements_per_page]]

    def create_embed(self, slice_: List[Any]) -> Optional[Embed]:
        """Creates a table-like Embed.

        ARGUMENTS
        slice_: the slice from self.create_slice"""
        # generate a random colour
        if self.random_colour:
            self.embed_settings["colour"] = self.create_colour()
        embed = Embed(**self.embed_settings)

        # add the rows
        inline = self.inline  # avoid the overhead of accessing attrs
        for row in slice_:
            for header, value in zip(self.headers, row):
                embed.add_field(name=header, value=value,
                                inline=inline)
            # add a break between rows
            embed.add_field(name="||\_-\_-\_-\_-\_-\_||",
                            value="||**-\_-\_-\_-\_-\_-**||")
        return embed

    @staticmethod
    async def on_next(self):
        """Show the next content when the next button is clicked.
        Iterates in sets of self.elements_per_page"""
        self._content_index += self.elements_per_page
        slice_ = self.create_slice()
        # start from 0 if at end of list
        if not slice_[0]:
            self._content_index = 0
            slice_ = self.create_slice()
        await self.msg.edit(embed=self.create_embed(*slice_))

    @staticmethod
    async def on_last(self):
        """Show the previous content when the back button is clicked.
        Iterates in sets of self.elements_per_page"""
        # go to the end of the list if at the start
        self._content_index -= self.elements_per_page
        slice_ = self.create_slice()
        # start from end if at start of list
        if not slice_[0]:
            self._content_index = len(self.content) - 1
            slice_ = self.create_slice()
        await self.msg.edit(embed=self.create_embed(*slice_))

    def __str__(self) -> str:
        """Converts self to string."""
        return super().__str__()[:-1:] + f"""
        headers: {self.headers}
        elements_per_page: {self.elements_per_page}
        inline: {self.inline}
        )"""

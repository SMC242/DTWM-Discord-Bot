from discord.ext import commands
import datetime as D
from asyncio import get_event_loop
from Utils import common
from discord import Message, TextChannel
from typing import Dict, Optional
from random import choice
from json import load
from Utils.mestils import search_word, get_eu_timezone


class ReactionParent(commands.Cog):
    """The base class for on_message handlers.
    NOTE: cooldowns are shared across all children."""

    # ATTRIBUTES
    enabled = True

    def __init__(self, bot: commands.Bot, cooldown: float = 60.0):
        """ARGUMENTS
        bot:
            The bot to use for executing commands.
        cooldown:
            The number of seconds where message events are ignored
            for after an event is handled."""
        self.bot = bot
        # all of the text channels for having a per-channel cooldown
        self.channels: Dict[int, D.datetime] = {}
        self.cooldown = cooldown

        # load the channels when the bot is ready
        get_event_loop().create_task(self.get_channels())

    async def get_channels(self):
        """Load all of the channels."""
        await common.wait_until_loaded(self.bot)

        # add all the text channels and
        # set them up with a placeholder datetime
        for chan in common.server.text_channels:
            self.channels[chan.id] = D.datetime(2020, 1, 1)

    async def on_message(self, msg: Message):
        """Activates when a message is sent"""
        raise NotImplementedError("An on_message handler must be implemented.")

    async def off_cooldown(self, msg: Message) -> bool:
        """Return whether the channel is off cooldown."""
        try:
            # only execute if the channel is off cooldown
            id_ = msg.channel.id
            if (D.datetime.today() - self.channels[id_]).total_seconds() \
                    >= self.cooldown:
                return True
            else:
                return False
        # handle the channel not being loaded
        except KeyError:
            return await self.get_channels()

    def set_cooldown(self, channel: TextChannel):
        """Put the target channel on cooldown."""
        # start cooldown
        self.channels[channel.id] = D.datetime.today()


class ReactionController(commands.Cog):
    """Handles commands relating to ReactionParent.

    This is necessary because adding these commands to ReactionParent
    would cause a double registration error when the children were added to the bot."""

    @commands.has_any_role(*common.leader_roles)
    @commands.command(aliases=["TR"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def toggle_reactions(self, ctx):
        """Enable or disable reactions to messages."""
        parent = ReactionParent
        parent.enabled = not parent.enabled
        await ctx.send(f"I will {'not' if not parent.enabled else ''} react to messages, my lord.")


class TextReactions(ReactionParent):
    """Handles sending messages in response to messages."""

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        """Send a message in response to a message event if the message contains:
            a ping for the bot or ben
        """
        # don't respond to the bot
        if self.bot.user == msg.author:
            return

        # don't respond if reactions are disabled
        if not self.enabled:
            return

        # don't respond if the channel is on cooldown
        if not await self.off_cooldown(msg):
            return

        match_name: str = None
        # react if ben or the bot is mentioned
        mentioned_ids = [person.id for person in msg.mentions]
        timezones = get_eu_timezone(msg.content)
        if self.bot.user.id in mentioned_ids or 395598378387636234 in mentioned_ids:
            match_name = "ping"

        # correct people if they use the wrong timezone
        elif timezones:
            found_zone = timezones[0]
            winter: bool = D.date.today().isocalendar()[1] > 26
            current_zone = "CET" if winter else "CEST"
            if found_zone != current_zone:
                match_name = current_zone

        # sometimes echo a message with 'DTWM' replaced with a wrong version of our tag
        elif search_word(msg.content, "DTWM"):
            weighting = [True, *[False] * 9]  # 1/10 chance
            if choice(weighting):
                match_name = "weird_DTWM"

        # send a message if a match was found
        if match_name:
            self.set_cooldown(msg.channel)
            with open("./Text Files/responses.json") as f:
                responses = load(f)
            await msg.channel.send(choice(responses[match_name]))


class ReactReactions(ReactionParent):
    """Handles adding reactions to messages on message events."""

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        """React to messages if the message contains:
            ayaya or :w_ayaya:,
            php"""

        # don't respond to the bot
        if self.bot.user == msg.author:
            return

        # don't respond if reactions are disabled
        if not self.enabled:
            return

        # don't respond if the channel is on cooldown
        if not await self.off_cooldown(msg):
            return

        content = msg.content.lower()
        # check if there is a match with regex.
        match_name: Optional[str] = None
        if search_word(content, "ayaya") or \
                search_word(content, "<:w_ayaya:622141714655870982>"):
            match_name = "ayaya"

        elif search_word(content, "php"):
            match_name = "php"

        elif search_word(content, "windows") or search_word(content, "linux"):
            match_name = "os"

        # only try to react if a match was found
        if match_name is not None:
            # get the responses
            with open("./Text Files/responses.json") as f:
                responses = load(f)

            self.set_cooldown(msg.channel)
            await msg.add_reaction(choice(responses[match_name]))


def setup(bot: commands.Bot):
    """Load the ReactionController, TextReactions, and ReactReactions Cogs.

    Args:
        bot (commands.Bot): the bot to load the Cogs to.
    """
    cogs = (
        ReactionController,
        TextReactions,
        ReactReactions,
    )

    for cog in cogs:
        bot.add_cog(cog(bot))

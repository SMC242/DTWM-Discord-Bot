"""All on_message handlers."""

import asyncio
import datetime as D
import random
from typing import List, Union
import discord
from discord.ext import commands
from .Extras.utils import searchWord
from .Extras.checks import inBotChannel, isLeader


class MessageResponses(commands.Cog):
    """Base class. Handles reacting to messages with on_message events.

    getChannels must be run upon on_ready
    """

    def __init__(self, bot: commands.Bot, cooldown: int = 60):
        """cooldown is in seconds."""

        self.bot = bot
        self.cooldown = cooldown
        self.parent = None  # will be registered to a ReactionParent

    async def getChannels(self):
        """Creates the dict of channels.

        Cannot be done before on_ready
        """

        today = D.date.today()
        # add placeholder datetime until there's a hit
        tempHit = D.datetime(today.year, today.month, today.day)

        server = self.bot.get_guild(545422040644190220)
        # for rate limiting by channel
        self.channels = {
            tChannel: tempHit for tChannel in server.text_channels}

    async def checkLastHit(self, msg: discord.Message):
        '''Check if rate limited'''

        # search for channel
        try:
            lastHit = self.channels[msg.channel]

        except KeyError:  # message in newly-created channel
            self.getChannels()  # check the channels again
            return False

        except AttributeError:  # channel list not set up yet
            return False

        # check hit
        timenow = D.datetime.now()
        if (timenow - lastHit).total_seconds() > self.cooldown:
            return True

        else:
            return False

    def on_message(self, msg: discord.Message):
        raise NotImplementedError()


class ReactionParent:
    """Handles sharing settings between all MessageResponses Cogs."""

    def __init__(self, children: List[MessageResponses]):
        self.reactionsAllowed = True

        # register children
        for child in children:
            child.parent = self

        self.children = children

    async def getChannels(self):
        """Set up the channels attribute for all children."""

        # get the channels dict
        await self.children[0].getChannels()
        channels = self.children[0].channels

        # send it to each child
        for child in self.children:
            child.channels = channels

    @commands.command(aliases=['re', 'noRe', 'reactions', 'TR', 'nR'])
    @inBotChannel()
    @commands.cooldown(1, 5, type=commands.BucketType.user)
    async def toggleReactions(self, ctx):
        '''Allow/disallow reactions to messages with terms in the white list'''

        self.reactionsAllowed = not self.reactionsAllowed

        return await ctx.send(f"I {'will' if self.reactionsAllowed else 'will not'} react to messages, My Lord")


class MessageReactions(MessageResponses):
    """Manages adding reactionst to messages"""

    def __init__(self, bot: commands.Bot, cooldown: int = 60):
        super().__init__(bot, cooldown)

    async def react(self, target: discord.Message, emote: Union[discord.Emoji, int]):
        '''Wrapper for Message.add_reaction.

        Updates self.lastHit'''

        if not isinstance(emote, discord.Emoji):
            emote = self.bot.get_emoji(emote)

        return await target.add_reaction(emote)

    @commands.Cog.listener()
    async def on_message(self, inputMsg: discord.Message):
        if inputMsg.author == self.bot.user:  # don't respond to self
            return

        if not (await self.checkLastHit(inputMsg) and self.parent.reactionsAllowed):
            return

        msg = inputMsg.content.lower()

        # check for whitelisted emotes
        if searchWord("php", msg):
            emoteID = 662430179129294867

        elif searchWord("ayaya", msg) or "<:w_ayaya:622141714655870982>" in msg:
            emoteID = 622141714655870982

        else:
            return

        # if matched
        channel = inputMsg.channel
        async with channel.typing():
            self.channels[channel] = D.datetime.now()
            await self.react(inputMsg, emoteID)
            # to end the typing
            return await channel.send("_", delete_after=0.0000000000001)


class MessageResponseMessages(MessageResponses):
    """Handles sending messages in response to users."""

    def __init__(self, bot: commands.Bot, cooldown: int = 300):
        super().__init__(bot, cooldown)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author == self.bot.user:  # don't respond to self
            return

        if not (await self.checkLastHit(msg) and self.parent.reactionsAllowed):
            return

        pingResponses = [
            "Who ping?",
            "Stop ping",
            "What do you want?",
            "Stop pinging me, cunt",
            "<:w_all_might_ping:590815766895656984>",
            "<:ping_wake_up_magi:597537421046841374>",
            "<:ping6:685193730709389363>",
            "<:ping5:685193730965504043>",
            "<a:ping4:685194385511678056>",
            "<a:ping3:685193731611295778>",
            "<a:ping2:685193730877423727>",
            "<a:ping1:685193730743074867>",
            "<:ping:685193730701000843>",
        ]

        # get angry if ben was pinged
        mentioned = [mention.id for mention in msg.mentions]
        if 395598378387636234 in mentioned or 507206805621964801 in mentioned:
            output = random.choice(pingResponses)

        # respond to princess sheep
        elif 326713068451004426 == msg.author.id:
            output = "Here's your bot function. BAAAAAAAAAAAAAAAAAAAA!"

        else:
            return

        # if matched
        channel = msg.channel
        async with channel.typing():
            self.channels[channel] = D.datetime.now()
            return await channel.send(output)

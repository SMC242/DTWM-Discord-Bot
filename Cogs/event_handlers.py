"""Handlers for events sent by Discord."""

from discord import *
from discord.ext import commands
from typing import *
from Utils import common, memtils
import datetime as D, traceback, re
from asyncio import get_event_loop
from json import load
from random import choice

# errors, message reactions
# custom error types
class CommandNotImplementedError(commands.CommandError):
    """Raise this if a command is a work in progress"""
    pass

class ErrorHandler(commands.Cog):
    """Handles responding to erorrs raised by commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, 
                               error: Union[commands.CommandError,
                                           commands.CheckFailure]):
        """Handle an exception raised during command invokation."""
        # Only use this error handler if the current context does not provide its
        # own error handler
        if hasattr(ctx.command, 'on_error'):
            return

        # Only use this error handler if the current cog does not implement its
        # own error handler
        if ctx.cog and commands.Cog._get_overridden_method(
                ctx.cog.cog_command_error) is not None:
            return

        # decide on their title
        title = memtils.get_title(ctx.author)

        #if command on cooldown
        if isinstance(error, commands.CommandOnCooldown):
          await ctx.send(f"Hold on, {title}. " + 
                                "I must gather my energy before another\n" +
                                f"Try again in {int(error.retry_after)} seconds!")
        #if command is unknown
        elif isinstance(error, commands.CommandNotFound):
            if '@' in ctx.invoked_with :
                await ctx.send("How dare you try to use me to annoy others!")
            else:
                await ctx.send(f'Sorry {title}, the archives do not know of this' +
                                    f'"{ctx.invoked_with}" you speak of')

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Your command is incomplete, {title}! You must tell me my target")

        elif isinstance(error, commands.MissingAnyRole):
            # create a grammatically correct list of the required roles
            missing_roles = list(error.missing_roles)  # ensure it's a list for join()
            await ctx.send("You need to be " +
                           f"{'an ' if missing_roles[0][0].lower() in 'aeiou' else 'a '}" +
                           f"{', '.join(missing_roles[:-2] + [' or '.join(missing_roles[-2:])])}" +
                           "to use that command!")

        elif isinstance(error, commands.DisabledCommand):
            await ctx.send(f"I cannot do that, {title}. The Adepts are doing maintenance on this coroutine.")

        elif isinstance(error, commands.NotOwner):
            await ctx.send("Only my alter-ego can do that!")

        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"I don't understand your orders, {title}")

        elif isinstance(error, commands.UnexpectedQuoteError):
            await ctx.send(f"Your orders are garbled, {title}")

        elif isinstance(error, CommandNotImplementedError):
            await ctx.send(f"The Adepts are yet to complete that command, {title}")

        #if bot can't access the channel
        elif isinstance(error, Forbidden):
            await ctx.send("I can't access one or more of those channels TwT")

        # custom checks will handle their own failures
        elif isinstance(error, commands.CheckFailure):
            pass

        # if the error hasn't been handled
        else:
            # tell the user
            await ctx.send(f"Warp energies inhibit me... I cannot do that, {title}")

            # get the original error from the CommandError
            # and convert its traceback to a string
            root_error = error.original
            tb_lines = traceback.format_exception(type(root_error), root_error,
                                                 root_error.__traceback__)
            tb = "\n".join(tb_lines) + f"Occured at: {D.datetime.now().time()}"

            # log to a text file
            with open("./Text Files/errorLog.txt", "a+") as f:
                f.write(tb)

            # log to Bot Testing.errors
            await self.bot.get_channel(697746979782000680).send(f"```\n{tb}```")


# on_message handlers
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
        self.channels: Dict[int, D.datetime] = {}  # all of the text channels for having a per-channel cooldown
        self.cooldown = cooldown

        # load the channels when the bot is ready
        get_event_loop().create_task(self.get_channels())

    async def get_channels(self):
        """Load all of the channels."""
        await self.bot.wait_until_ready()
        common.load_bot(self.bot)

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
                # start cooldown
                self.channels[id_] = D.datetime.today()

                return True
            else:  return False

        # handle the channel not being loaded
        except KeyError:
            return await self.get_channels()

    @staticmethod
    def search_word(contents: str, target_word: str) -> bool:
        """Return whether the target_word was found in contents.
        Not case-sensitive."""
        return (re.compile(r'\b({0})\b'.format( target_word.lower() ), flags=re.IGNORECASE).search(
            contents.lower() )) is not None


class ReactionController(commands.Cog):
    """Handles commands relating to ReactionParent.
    
    This is necessary because adding these commands to ReactionParent
    would cause a double registration error when the children were added to the bot."""

    @common.in_bot_channel()
    @commands.has_any_role(*common.leader_roles)
    @commands.command(aliases = ["TR"])
    async def toggle_reactions(self, ctx):
        """Enable or disable reactios to messages."""
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

        # react if ben or the bot is mentioned
        to_send: str = None
        mentioned_ids = [person.id for person in msg.mentions]
        if self.bot.user.id in mentioned_ids or 395598378387636234 in mentioned_ids:
            with open("./Text Files/responses.json") as f:
                responses = load(f)

            to_send = choice(responses["ping"])

        # only try to send if a match was found
        if to_send is not None:
            await msg.channel.send(to_send)


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

        # load responses if there might be a match
        # in checks for a sequence of chars rather than an exact match
        # so this doesn't guarentee a match
        targets = (
            "ayaya",
            "php",
            )
        content = msg.content
        for target in targets:
            if target in content:
                with open("./Text Files/responses.json") as f:
                    responses = load(f)

        # ensure there is a match with reg. ex.
        to_send: str = None
        if self.search_word(content, "ayaya") or \
            self.search_word(content, "<:w_ayaya:622141714655870982>"):
            to_send = responses["ayaya"]

        elif self.search_word(content, "php"):
            to_send = responses["php"]

        # only try to react if a match was found
        if to_send is not None:
            await msg.add_reaction(to_send)

def setup(bot):
    cogs = (
        ErrorHandler,
        ReactReactions,
        TextReactions,
        ReactionController,
        )
    for cog in cogs:
        bot.add_cog( cog(bot) )

if __name__ == "__main__":
    setup(commands.Bot("test"))
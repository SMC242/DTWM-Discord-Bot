"""Handlers for events sent by Discord."""

from discord import *
from discord.ext import commands, tasks
from typing import *
from Utils import common, memtils, mestils
import datetime as D, traceback
from asyncio import get_event_loop
from json import load
from random import choice
from Utils.mestils import list_join, search_word
from inspect import iscoroutinefunction as iscorofunc

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
                await ctx.send(f'Sorry {title}, the archives do not know of this ' +
                                    f'"{ctx.invoked_with}" you speak of')

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Your command is incomplete, {title}! You must tell me my target")

        elif isinstance(error, commands.MissingAnyRole):
            # create a grammatically correct list of the required roles
            missing_roles = list(error.missing_roles)  # ensure it's a list for join()
            await ctx.send("You need to be " +
                           f"{'an ' if missing_roles[0][0].lower() in 'aeiou' else 'a '}" +
                           f"{list_join(missing_roles, 'or')}" +
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

        # if a command is malfunctioning
        elif isinstance(error.original, AssertionError):
            await ctx.send(f"My diagnostics report a failure in {ctx.command.name}" + 
                           "Please inform the Adepts soon.")

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
            try:
                await common.error_channel.send(f"```\n{tb}```")
            # handle tb being too large for a Discord message
            except errors.HTTPException:
                await common.error_channel.send("The tracebaceback was too large. " +
                                                "Check `Text Files/errorLog.txt`")


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
            else:  return False
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
    @commands.command(aliases = ["TR"])
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

        # react if ben or the bot is mentioned
        to_send: str = None
        mentioned_ids = [person.id for person in msg.mentions]
        if self.bot.user.id in mentioned_ids or 395598378387636234 in mentioned_ids:
            with open("./Text Files/responses.json") as f:
                responses = load(f)

            to_send = choice(responses["ping"])

        # only try to send if a match was found
        if to_send is not None:
            self.set_cooldown(msg.channel)
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

        content = msg.content.lower()
        # check if there is a match with regex.
        match_name: str = None
        if search_word(content, "ayaya") or \
            search_word(content, "<:w_ayaya:622141714655870982>"):
            match_name = "ayaya"

        elif search_word(content, "php"):
            match_name = "php"

        # only try to react if a match was found
        if match_name is not None:
            # get the responses
            with open("./Text Files/responses.json") as f:
                responses = load(f)

            self.set_cooldown(msg.channel)
            await msg.add_reaction(responses[match_name])


class ReactMenuHandler(commands.Cog):
    """Manages all of the active ReactMenus.
    
    ATTRIBUTES
    bound_messages: Dict[Tuple[int, ReactMenu]]
        The messages that are currently being tracked.
        They're cleaned up every 10 minutes.
        Format: Message.id : ReactMenu"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bound_messages: Dict[int, 'ReactMenu'] = {}
        self.message_cleanup.start()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction_: Reaction, person: Member):
        """Check if the message reacted to is bound.
        If so, execute the reaction's callback if applicable."""
        # don't respond to self
        if person == self.bot.user:  return

        # check if the message is bound
        msg = reaction_.message
        if msg.id not in self.bound_messages:  return

        # check if the reaction is valid
        menu = self.bound_messages[msg.id]
            
        # check that it's ready
        if menu._starting:  return

        # execute the reaction's callback if it exists
        cb = getattr(menu,
                        menu.emotes[reaction_.emoji.id], None)
        if cb is not None:
            # allow coroutines
            if iscorofunc(cb):
                await cb(menu)
            else:
                cb(menu)

        # clean up the user's reactions
        for r in msg.reactions:
            await r.remove(person)

    @tasks.loop(minutes = 10)
    async def message_cleanup(self):
        """Stop tracking messages that are older than 10 minutes."""
        for menu in self.bound_messages.values():
            msg = menu.msg
            now = D.datetime.utcnow()
            # check if it was last interacted wtih >10 minutes ago
            if (msg.edited_at and ((now - msg.edited_at).seconds / 60) > 10) \
                or ((now - msg.created_at).seconds / 60) > 10:
                menu.unregister()


class InstagramHandler(commands.Cog):
    """Responds to Instagam links"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_msg = None

    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        """Warns the user if they post a private Instagram link."""
        # don't respond to the bot
        if self.bot.user == msg.author:
            return

        # check if there was an Instagram link
        links = mestils.get_instagram_links(msg.content)
        
        # parse links
        # private links have a longer id whereas public
        # ones have a fixed size of 11
        for link in links:
            if len(link[28:]) > 11:  # https://www.instagram.com/p/ is 28 characters
                await msg.channel.send("That link was private, brother. I will remove it " + "<:s_40k_adeptus_mechanicus_shocked:585598378721673226>")
                self.last_msg = msg  # cache the message in case of a false-positive
                await msg.delete(delay = 2)

    @commands.command(aliases = ["RS", "resummon", "come_back", "false_positive"
                                 "false_hit", "resummon_msg"])
    async def resummon_message(self, ctx):
        """Repost the last deleted message."""
        if self.last_msg is None:
            return await ctx.send("I have not deleted anything today, my lord.")
        await ctx.send(self.last_msg.content, 
                        # I can't pass the whole list :/
                       embed = self.last_msg.embeds[0] if self.last_msg.embeds else None,
                       )

def setup(bot):
    cogs = (
        ErrorHandler,
        ReactReactions,
        TextReactions,
        ReactionController,
        ReactMenuHandler,
        InstagramHandler,
        )
    for cog in cogs:
        bot.add_cog( cog(bot) )

if __name__ == "__main__":
    setup(commands.Bot("test"))

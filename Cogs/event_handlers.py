"""Handlers for events sent by Discord."""

from discord import *
from discord.ext import commands
from typing import *
from Utils import common, memtils
import datetime as D, traceback

# errors, message reactions
# custom error types
class RateLimited(commands.CommandError):
    """Raise this if an action is on cooldown."""
    pass

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

        #if command on cooldown
        if isinstance(error, commands.CommandOnCooldown):
          await ctx.send(f"Hold on, {'my lord' if memtils.has_role(common.leader_roles) else 'brother'}" + 
                                ". I must gather my energy before another\n" +
                                "Try again in {int(error.retry_after)} seconds!")
        #if command is unknown
        elif isinstance(error, commands.CommandNotFound):
            if '@' in ctx.invoked_with :
                await ctx.send("How dare you try to use me to annoy others!")
            else:
                await ctx.send('Sorry My Lord, the archives do not know of this' +
                                    f'"{ctx.invoked_with}" you speak of')

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Your command is incomplete, brother! You must tell me my target")

        elif isinstance(error, commands.MissingAnyRole):
            # create a grammatically correct list of the required roles
            missing_roles = list(*error.missing_roles)  # ensure it's a list for join()
            await ctx.send("You need to be " +
                           f"{'an ' if missing_roles[0][0].lower() in 'aeiou' else 'a '}" +
                           f"{', '.join(missing_roles[:-2] + [' or '.join(missing_roles[-2:])])}")

        elif isinstance(error, commands.DisabledCommand):
            await ctx.send("I cannot do that, brother. The Adepts are doing maintenance on this coroutine.")

        elif isinstance(error, commands.NotOwner):
            await ctx.send("Only my alter-ego can do that!")

        elif isinstance(error, commands.BadArgument):
            await ctx.send("I don't understand your orders, brother")

        elif isinstance(error, commands.UnexpectedQuoteError):
            await ctx.send("Your orders are garbled, brother")

        elif isinstance(error, RateLimited):
            await ctx.send("Please give me room to think, Brother")

        elif isinstance(error, CommandNotImplementedError):
            await ctx.send("The Adepts are yet to complete that command, brother")

        #if bot can't access the channel
        elif isinstance(error, Forbidden):
            await ctx.send("I can't access one or more of those channels TwT")

        # custom checks will handle their own failures
        elif isinstance(error, commands.CheckFailure):
            pass

        # if the error hasn't been handled
        else:
            # tell the user
            await ctx.send("Warp energies inhibit me... I cannot do that, My Lord")

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


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
from typing import Union
from discord.ext import commands
from discord import errors, Forbidden
import traceback
from Utils.mestils import list_join
from Utils import memtils
from Utils import common
import datetime as D
from fuzzywuzzy.process import extractOne


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

        # if command on cooldown
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Hold on, {title}. " +
                           "I must gather my energy before another\n" +
                           f"Try again in {int(error.retry_after)} seconds!")
        # if command is unknown
        elif isinstance(error, commands.CommandNotFound):
            if '@' in ctx.invoked_with:
                await ctx.send("How dare you try to use me to annoy others!")
            else:
                # get close matches
                cmd_names = [cmd.name for cmd in self.bot.walk_commands()]
                suggestion = extractOne(ctx.invoked_with, cmd_names)[0]
                await ctx.send(f'Sorry {title}, the archives do not know of this '
                               f'"{ctx.invoked_with}" you speak of. '
                               f"Did you mean `{ctx.prefix}{suggestion}`?")

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Your command is incomplete, {title}! You must tell me my target")

        elif isinstance(error, commands.MissingAnyRole):
            # create a grammatically correct list of the required roles
            # ensure it's a list for join()
            missing_roles = list(error.missing_roles)
            await ctx.send("You need to be " +
                           f"{'an ' if missing_roles[0][0].lower() in 'aeiou' else 'a '}" +
                           f"{list_join(missing_roles, 'or')}" +
                           " to use that command!")

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

        # if bot can't access the channel
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


def setup(bot: commands.Bot):
    """Load the ErrorHandler Cog.

    Args:
        bot (commands.Bot): the bot to load the Cog to.
    """

    cogs = (
        ErrorHandler,
    )

    for cog in cogs:
        bot.add_cog(cog(bot))

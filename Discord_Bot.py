# authors: benmitchellmtb, ScreaminSteve, FasterNo1
"""Main bot class and launch script.

Run as a script to start the bot.
"""

import asyncio
import datetime
import json
import random
import sys
import traceback
import discord
from typing import Dict
from discord.ext import commands, tasks
from cogs.attendance import Attendance
from errors import NotLeaderError, CommandNotImplementedError, RateLimited


class BotOverride(commands.Bot):
    """Custom bot subclass with extra functionality."""

    @tasks.loop(seconds=0.0, minutes=0.0, hours=1.0)
    async def chooseStatus(self):
        """Switch to a new status.

        The list of statuses is retrieved at every execution, allowing
        addition of new statuses without downtime.
        """
        statuses_data: Dict[str, str] = json.load('data/statuses.json')
        statuses = [discord.Activity(name=s, type=discord.ActivityType.playing)
                    for s in statuses_data['playing']]
        statuses.extend(
            discord.Activity(name=s, type=discord.ActivityType.watching)
            for s in statuses_data['watching'])
        await self.change_presence(activity=random.choice(statuses))

    async def on_command_error(self, ctx: commands.Context,
                               exception: Exception):
        """Handle an exception raised during command invokation."""
        # Only use this error handler if the current context does not provide
        # its own error handler
        if hasattr(ctx.command, 'on_error'):
            return
        # Only use this error handler if the current cog does not implement its
        # own error handler
        if ctx.cog and commands.Cog._get_overridden_method(
                ctx.cog.cog_command_error) is not None:
            return

        if isinstance(exception, commands.CommandOnCooldown):
            return await ctx.send(
                'Hold on, My Lord. I must gather my energy before another\n'
                f'Try again in {int(exception.retry_after)} seconds!')

        elif isinstance(exception, commands.CommandNotFound):
            if '@' in ctx.invoked_with:
                return await ctx.send(
                    'How dare you try to use me to annoy others!')

            else:
                return await ctx.send(
                    'Sorry My Lord, the archives do not know of this '
                    f'"{ctx.invoked_with}"" you speak of')

        elif isinstance(exception, commands.MissingRequiredArgument):
            return await ctx.send('Your command is incomplete, My Lord! '
                                  'You must tell me my target')

        elif isinstance(exception, commands.CheckFailure):
            # the handling for this is done in the checking decorators
            pass

        elif isinstance(exception, NotLeaderError):
            return await ctx.send('Only leaders may do that, brother. '
                                  'Go back to your company')

        elif isinstance(exception, commands.DisabledCommand):
            return await ctx.send(
                'I cannot do that, My Lord. The Adepts are doing maintenance '
                'on this coroutine.')

        elif isinstance(exception, commands.BadArgument):
            return await ctx.send('I don\'t understand your orders, My Lord')

        elif isinstance(exception, RateLimited):
            return await ctx.send('Please give me room to think, Brother')

        elif isinstance(exception, CommandNotImplementedError):
            return await ctx.send(
                'The Adepts are yet to complete that command, Brother')

        elif isinstance(exception, discord.Forbidden):
            return await ctx.send(
                'I can\'t access one or more of those channels TwT')

        else:
            # If none of the previous checks were able to handle the error,
            # print it to stdout like in the default implementation.
            print(f'Ignoring exception in command {ctx.command}:',
                  file=sys.stderr)
            traceback.print_exception(type(exception), exception,
                                      exception.__traceback__,
                                      file=sys.stderr)
            print(f'Occured at: {datetime.datetime.now().time()}')

            # give user feedback if internal error occurs
            return await ctx.send(
                'Warp energies inhibit me... I cannot do that, My Lord')

    async def on_ready(self):
        print('\nLogged in as')
        print(f"Username: {bot.user.name}")
        print(f"User ID: {bot.user.id}")
        print('------')

        # Acknowledge startup
        botChannel = bot.get_channel(545818844036464670)
        await botChannel.send('I have awoken... I am at your service')

        # Start looping tasks
        self.chooseStatus.start()


if __name__ == '__main__':
    # Load the bot token
    from private import BOT_TOKEN

    # Instantiate the custom bot
    bot = BotOverride(command_prefix='ab!', case_insensitie=True)

    # Add cogs
    bot.add_cog(Attendance(bot))

    # Run the bot
    bot.run(BOT_TOKEN)

"""This modules handles any functions or variables that all modules will access."""

from discord import *
from discord.ext import commands
import asyncio
from typing import *

bot = commands.Bot(None)  # temporarily defining the bot
BOT_LOADED = False  # flag for raising an error if the bot wasn't loaded already
# channels
bot_channel = None
server = None

async def load_bot(target_bot: commands.Bot):
    """
    Allow this module to use the Bot instance.
    The functions won't work and the variables will be None unless this has been called.

    This is due to needing access to the bot for some checks.
    """
    global bot, bot_channel, server

    # unlock all of the functions that need the bot
    bot = target_bot
    BOT_LOADED = True

    # set up common variables
    bot_channel = bot.get_channel(545818844036464670)
    server = bot.get_guild(545422040644190220)

def in_bot_channel():
    """Check if the command was invoked in the bot channel."""
    async def inner(ctx):
        # require a bot instance
        if not BOT_LOADED:
            raise ValueError("This check requires a bot. Use load_bot to unlock it.")

        # check if the bot is in #servitors
        return ctx.channel == bot.get_channel()
    return commands.check(inner)
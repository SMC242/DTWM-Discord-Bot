"""This modules handles any functions or variables that all modules will access.

DEV_VERSION can be set to True to use the bot testing server."""

from discord import *
from discord.ext import commands
import unicodedata, discord
from typing import *
from string import ascii_letters

# common variables
DEV_VERSION = False
bot = commands.Bot(None)  # temporarily defining the bot
bot_loaded = False  # flag for raising an error if the bot wasn't loaded already
member_roles = ("Astartes", "Champion", "Watch Leader")
leader_roles = member_roles[1:]
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
    bot_loaded = True

    # set up common variables
    # use the bot testing server if it's a dev version
    if DEV_VERSION:
        bot_channel = bot.get_channel(660950914202599427)  # bot testing.general
        server = bot.get_guild(660950914202599424)  # bot testing
    else:
        bot_channel = bot.get_channel(545818844036464670)  # DTWM.servitors
        server = bot.get_guild(545422040644190220)  # DTWM

def in_bot_channel() -> commands.check:
    """Check if the command was invoked in the bot channel."""
    async def inner(ctx):
        # require a bot instance
        if not bot_loaded:
            raise ValueError("This check requires a bot. Use load_bot to unlock it.")

        # check if the bot is in #servitors
        return ctx.channel == bot.get_channel()
    return commands.check(inner)
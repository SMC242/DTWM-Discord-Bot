"""This modules handles any functions or variables that all modules will access.

DEV_VERSION can be set to True to use the bot testing server."""

from discord import *
from discord.ext.commands import Bot
from typing import *

# common variables
DEV_VERSION = False
bot = Bot(None)  # temporarily defining the bot
bot_loaded: bool = False  # flag for raising an error if the bot wasn't loaded already
member_roles = ("Astartes", "Champion", "Chaplain", "Watch Leader")
leader_roles = member_roles[1:]
extra_roles = (
    "Heretic",
    "Tech Priest",
    "Adeptus Arbites",
    "Chrono-gladiator",
    "Remembrancer",
    "Null Maiden",
    "Noise Marine",
    "Adeptus Custodes",
)
# channels
bot_channel = None
server = None
error_channel = None


async def wait_until_loaded(wait_for: Bot):
    """Wait until the bot is ready, then load it."""
    global bot_loaded
    # avoid reloading the bot
    if bot_loaded:
        return

    await wait_for.wait_until_ready()
    _load_bot(wait_for)


def _load_bot(target_bot: Bot):
    """
    Allow this module to use the Bot instance.
    The functions won't work and the variables will be None unless this has been called.

    This is due to needing access to the bot for some checks.
    """
    global bot, bot_channel, server, bot_loaded, error_channel

    # don't load the bot twice
    if bot_loaded:
        return

    # unlock all of the functions that need the bot
    bot = target_bot
    bot_loaded = True

    # set up common variables
    # use the bot testing server if it's a dev version
    if DEV_VERSION:
        bot_channel = bot.get_channel(
            660950914202599427)  # bot testing.general
        server = bot.get_guild(660950914202599424)  # bot testing
    else:
        bot_channel = bot.get_channel(545818844036464670)  # DTWM.servitors
        server = bot.get_guild(545422040644190220)  # DTWM
    error_channel = bot.get_channel(697746979782000680)

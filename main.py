"""This module handles starting the bot instance, global behaviour changes, and running it."""

from discord import *
from discord.ext import commands
from typing import *
import os
from Utils import common
from datetime import datetime
from traceback import print_exc
from BenUtils.searching import binarySearch

# dev settings
DEV_VERSION = False
common.DEV_VERSION = DEV_VERSION
LOG_LOAD_ERROR = True

# instantiate the bot
description = """This bot was designed for the DTWM discord by [DTWM] benmitchellmtbV5.
Special thanks to:
    My mentors: Auroram, Stalkopat
    The host, admin, and debugging helper: [DTWM] ScreaminSteve
    Profile picture: [DTWM] BoeruChan"""
bot = commands.Bot(
    f"{'dev' if DEV_VERSION else 'ab'}!",
    description = description,
    owner_ids = (395598378387636234, 515163362062237716),
    activity = Activity(name = "Waking up...", url = "https://joindtwm.net",
        type = ActivityType.playing, state = "Powering on...",
        details = "The adepts have summoned me from my slumber."),
    case_insensitive = True
    )

# check that there is a token to run from
if not os.path.exists("./Text Files/token.txt"):
    # wait for the user to read the message, then exit
    input("There is no token in Text Files/\nPress any key to exit.")
    import sys
    sys.exit(0)

# ensure that the Images directory exists
if not os.path.exists("./Images"):
    os.mkdir(("./Images"))

# load all of the Cogs. Credit to https://youtu.be/vQw8cFfZPx0?t=424
for file in os.listdir("./Cogs"):
    # ensure it's a Python file and ignore modules that aren't Cogs
    if file.endswith(".py"):
        cog_name = file[:-3]
        # ignore __init__ because it's not a Cog but it must be in the directory
        if cog_name == "__init__":
            continue

        try:
            bot.load_extension(f"Cogs.{cog_name}")
            print(f"Cog ({cog_name}) loaded sucessfully")

        except:
            print(f"Cog ({cog_name}) failed to load")
            # log loading tracebacks if lod_load_error is True or if it's not set but dev_version is True
            if (LOG_LOAD_ERROR is not None and LOG_LOAD_ERROR) or (LOG_LOAD_ERROR is None and DEV_VERSION):
                print_exc()

@bot.before_invoke
async def log_command_info(ctx):
    """Log information about each command call."""
    # get time info
    today = datetime.today()
    day = today.strftime("%d.%m.%Y")
    time = today.strftime("%H:%M")
    print(f'Command: {ctx.command.qualified_name} called in "{ctx.guild.name}".{ctx.channel} on {day} at {time}')

@bot.command()
@commands.is_owner()
async def close(ctx):
    """End me rightly."""
    # shut down the bot
    await ctx.send("Power core depleted. Shutting down...")
    print(f"Ow! That hurt @{ctx.author}")
    await bot.logout()

@bot.command(aliases = ["TC"])
@commands.is_owner()
async def toggle_command(ctx, name: str):
    """Deactivate or activate a faulty command."""
    commands = list(set([cmd for cmd in bot.walk_commands()]))  # filter out duplicates
    command = binarySearch(name, sorted(commands, key = lambda cmd: cmd.name),
                           return_type = "item",
                           key = lambda cmd: cmd.name)
    if command:
        command.enabled = False
        await ctx.send(f"I have {'en' if command.enabled else 'dis'}abled" +
                       f" {command.name}")
    else:
        await ctx.send("I cannot find that command, my lord")

@bot.listen()
async def on_ready():
    """Control the behaviour when the bot starts."""
    # acknowledge startup in the terminal
    print("I am ready.\n---")

    # load common
    common.load_bot(bot)

    #acknowledge startup in #servitors
    await common.bot_channel.send(f'{"`[DEV VERSION]` " if DEV_VERSION else ""}I have awoken... I am at your service.')

    # warn user if they're on the dev version
    if DEV_VERSION:
        print("WARNING: you are on the dev version. Change main.DEV_VERSION to False if you're a user")

if __name__ == "__main__":
    # get the token and start the bot
    with open("Text Files/token.txt") as f:
        token = f.readline().strip("\n")
    bot.run(token)
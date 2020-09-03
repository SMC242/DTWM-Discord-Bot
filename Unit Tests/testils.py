import unittest
import discord
import main
from Utils import common
from typing import *
from discord.ext import commands
from time import sleep


def create_bot(cog_name: str) -> commands.Bot:
    """Create a Bot instance for testing."""
    main.DEV_VERSION = False
    common.DEV_VERSION = False
    return commands.Bot("mock!",
                        activity=discord.Activity(
                            name=f"Adepts running diagnostics on {cog_name}...",
                            type=discord.ActivityType.playing,
                        ),
                        case_insensitive=True,
                        allowed_mentions=discord.AllowedMentions(everyone=False,
                                                                 roles=False),
                        )


""" def create_ctx(bot: commands.Bot, command: commands.Command,
               msg: str = "Placeholder",
               args: Tuple[Any] = tuple(),
               kwargs: dict = {},
               command_failed: bool = False,
               channel_id: int = None,
               author_id: int = 395598378387636234,  # ben
               guild_id: int = None,
               me: Union[discord.Member, discord.ClientUser] = None,
               valid: bool = True
               ) -> commands.Context:
    '''DEFAULTS:
    prefix: bot.command_prefix
    channel: common.bot_channel
    guild: common.server
    invoked_subcommand: None
    subcommand_passed: None
    voice_client: None
    '''
    # make sure the bot is ready
    while not bot.is_ready():
        sleep(0.5)

    # derieved variables
    prefix = bot.command_prefix
    if not channel_id:
        channel_id = common.bot_channel.id
    if not guild_id:
        guild_id = common.server.id
    invoked_with = command.name
    cog = command.cog

    # get objects from their ids
    channel: discord.TextChannel = bot.get_channel(channel_id)
    guild = bot.get_guild(guild_id)
    author = guild.get_member(author_id)
    message = (await channel.history(limit=1).flatten())[0]
    # TODO create message object
    if not me:
        me = guild.me

    return commands.Context(
        message=message,
        bot=bot,
        args=args,
        kwargs=kwargs,
        prefix=prefix,
        command=command,
        invoked_with=invoked_with,
        invoked_subcommand=None,
        subcommand_passed=None,
        command_failed=command_failed,
        valid=valid,
        cog=cog,
        guild=guild,
        channel=channel,
        author=author,
        me=me,
        voice_client=None,
    )
 """
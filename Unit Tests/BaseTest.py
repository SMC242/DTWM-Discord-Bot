import unittest, discord
from Utils import common
from typing import *
from discord.ext import commands
from time import sleep
from asyncio import get_event_loop

class BaseTest(object):
    """Base class for bot tests"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        loop = get_event_loop()
        loop.create_task(self.test_ctx())

    async def create_ctx(self, command: commands.Command,
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
        """DEFAULTS:
        prefix: self.bot.command_prefix
        channel: common.bot_channel
        guild: common.server
        invoked_subcommand: None
        subcommand_passed: None
        voice_client: None
        """
        # make sure the bot is ready
        while not self.bot.is_ready():
            sleep(0.5)

        # derieved variables
        prefix = self.bot.command_prefix
        if not channel_id:
            channel_id = common.bot_channel.id
        if not guild_id:
            guild_id = common.server.id
        invoked_with = command.name
        cog = command.cog

        # get objects from their ids
        channel = self.bot.get_channel(channel_id)
        guild = self.bot.get_guild(guild_id)
        author = guild.get_member(author_id)
        message = await channel.fetch_message(748796704832356423)
        # TODO create message object
        if not me:
            me = guild.me

        return commands.Context(
            message = message,
            bot = self.bot,
            args = args,
            kwargs = kwargs,
            prefix = prefix,
            command = command,
            invoked_with = invoked_with,
            invoked_subcommand = None,
            subcommand_passed = None,
            command_failed = command_failed,
            valid = valid,
            cog = cog,
            guild = guild,
            channel = channel,
            author = author,
            me = me,
            voice_client = None,
            )

    async def test_ctx(self):
        ctx = await self.create_ctx(list(self.bot.commands)[0])
        await ctx.send("Dummy Context test")
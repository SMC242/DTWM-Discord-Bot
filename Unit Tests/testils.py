import discord
from typing import *
from discord.ext import commands


def create_bot(cog_name: str) -> commands.Bot:
    """Create a Bot instance for testing."""
    return commands.Bot("mock!",
                        activity=discord.Activity(
                            name=f"Adepts running diagnostics on {cog_name}...",
                            type=discord.ActivityType.playing,
                        ),
                        case_insensitive=True,
                        allowed_mentions=discord.AllowedMentions(everyone=False,
                                                                 roles=False),
                        )

"""Bot-specific error definitions."""

from discord.ext import commands


class NotLeaderError(commands.CommandError):
    """If the Member is not >=Champion."""


class RateLimited(commands.CommandError):
    """For the custom on_message rate limiter."""


class CommandNotImplementedError(commands.CommandError):
    """Command partially complete but not disabled for testing."""

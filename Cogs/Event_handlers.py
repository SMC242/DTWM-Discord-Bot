"""This module collects all of the event_handler_modules into one namespace"""

from discord.ext import commands
from .event_handler_modules import error_handler, moderators, reaction_handlers, react_menu_handling


def setup(bot):
    modules = (
        error_handler,
        moderators,
        react_menu_handling,
        reaction_handlers,
    )
    for module in modules:
        module.setup(bot)


def teardown(bot):
    modules = (
        error_handler,
        moderators,
        react_menu_handling,
        reaction_handlers,
    )

    for module in modules:
        module.teardown(bot)


if __name__ == "__main__":
    setup(commands.Bot("test"))

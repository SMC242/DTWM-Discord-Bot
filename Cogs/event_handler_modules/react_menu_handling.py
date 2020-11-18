from discord import Reaction, Member
from discord.ext import commands, tasks
from typing import Dict
from inspect import iscoroutinefunction as iscorofunc
from json import dumps
from Utils.mestils import send_as_chunks
import datetime as D


class ReactMenuHandler(commands.Cog):
    """Manages all of the active ReactMenus.

    ATTRIBUTES
    bound_messages: Dict[Tuple[int, ReactMenu]]
        The messages that are currently being tracked.
        They're cleaned up every 10 minutes.
        Format: Message.id : ReactMenu"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bound_messages: Dict[int, 'ReactMenu'] = {}
        self.message_cleanup.start()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction_: Reaction, person: Member):
        """Check if the message reacted to is bound.
        If so, execute the reaction's callback if applicable."""
        # don't respond to self
        if person == self.bot.user:
            return

        # check if the message is bound
        msg = reaction_.message
        if msg.id not in self.bound_messages:
            return

        # check if the reaction is valid
        menu = self.bound_messages[msg.id]

        # check that it's ready
        if menu._starting:
            return

        # execute the reaction's callback if it exists
        cb = getattr(menu,
                     menu.emotes[reaction_.emoji.id], None)
        if cb is not None:
            # allow coroutines
            if iscorofunc(cb):
                await cb(menu)
            else:
                cb(menu)

        # clean up the user's reactions
        for r in msg.reactions:
            await r.remove(person)

    @tasks.loop(minutes=10)
    async def message_cleanup(self):
        """Stop tracking messages that are older than 10 minutes."""
        # check if it was last interacted wtih >10 minutes ago
        now = D.datetime.utcnow()
        new_bound_messages = {menu.msg.id: menu for menu in self.bound_messages.values()
                              if (menu.msg.edited_at and ((now - menu.msg.edited_at).seconds / 60) < 10)
                              or ((now - menu.msg.created_at).seconds / 60) < 10}
        self.bound_messages = new_bound_messages

    @commands.command(aliases=["SRM"])
    @commands.is_owner()
    async def show_react_menus(self, ctx):
        """Show all of the bound react menus. Debugging tool."""
        await send_as_chunks(
            dumps(self.bound_messages, indent=4, default=str),
            ctx, code_block=True)


def setup(bot: commands.Bot):
    """Load ReactMenuHandler.

    Args:
        bot (commands.Bot): the bot to load the Cogs to
    """
    cogs = (
        ReactMenuHandler,
    )

    for cog in cogs:
        bot.add_cog(cog(bot))


def teardown(bot):
    cogs = (
        "ReactMenuHandler",
    )
    for cog in cogs:
        bot.remove_cog(cog)

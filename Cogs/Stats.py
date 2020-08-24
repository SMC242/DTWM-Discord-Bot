"""Statistic getters"""

from discord import * 
from discord.ext import commands
from typing import *
import datetime as D
from Utils import common, memtils

# count messages, count reactions
class TrainingWeeks(commands.Cog):
    """Handles the bi-weekly trainings.
    
    Commands and their alias:
        get_training_week, week"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def training_type(self) -> str:
        """
        Get whether the week will be air or armour.

        RETURNS
        'Aerial Superiority': it's an air week
        'Aerial Superiority': it's an armour week
        """
        #credit to auroram for rewrite
        #find this week's monday
        today = D.date.today()
        
        topics = ['combined arms control', 'armour support']

        _, week_num, _ = today.isocalendar()
        # NOTE: 1st week: air, 2nd week: armour, 3rd week: air, etc.
        # This scales with the number of actual topics, no changes needed!
        topic = topics[week_num % len(topics) - 1]

        return topic

    @commands.command(aliases = ["week"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def get_training_week(self, ctx):
        """Get the training types for this week"""
        await ctx.send(f"This week we will train {self.training_type}, {memtils.get_title(ctx.author)}")


class ServerStats(commands.Cog):
    """Displays stats about the server."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command(aliases = ["CM"])
    async def count_messages(self, ctx,
                             target_channel: Union[TextChannel, str] = "global",
                             hours: float = 24):
        """Count the number of messages in the target channel in the last 24 hours by default.
        Pass 'global' to count the entire server."""
        async def count_channel_messages(channel: TextChannel, after: D.datetime) -> int:
            """Return the number of messages in the target channel.
            Limited to 5k messages."""
            return len( await channel.history(limit = 5000, after = after).flatten() )

        async with ctx.typing():
            # verify the arguement
            if target_channel != "global" and not isinstance(target_channel, TextChannel):
                return await ctx.send("You must mention a channel or pass 'global'.")

            # get the datetime for 24 hours ago
            after = D.datetime.today() - D.timedelta(hours = hours)

            # count all channels if global was passed
            is_global = target_channel == "global"
            if is_global:
                count = 0
                for chan in common.server.text_channels:
                    count += await count_channel_messages(chan, after)
            else:
                count = await count_channel_messages(target_channel, after)

            await ctx.send(f"{count} messages were sent {'aboard the Erioch ' if is_global else ''}" +
                           f"today, {memtils.get_title(ctx.author)}.")

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command(aliases = ["CR"])
    async def count_reactions(self, ctx,
                              target_channel: Union[TextChannel, str] = "global",
                              hours: float = 24):
        """Count the number of reactions in the target channel in the last 24 hours by default.
        Pass 'global' to count the entire server."""
        async def count_channel_reacts(channel: TextChannel, after: D.datetime) -> int:
            """Return the number of reactions in the target channel.
            Limited to 5k messages."""
            count = 0
            async for msg in channel.history(limit = 5000, after = after):
                for react in msg.reactions:
                    count += react.count

            return count

        async with ctx.typing():
            # verify the arguement
            if target_channel != "global" and not isinstance(target_channel, TextChannel):
                return await ctx.send("You must mention a channel or pass 'global'.")

            # get the datetime for 24 hours ago
            after = D.datetime.today() - D.timedelta(days = 1)

            # count all channels if global was passed
            is_global = target_channel == "global"
            if is_global:
                count = 0
                for chan in common.server.text_channels:
                    count += await count_channel_reacts(chan, after)
            else:
                count = await count_channel_reacts(target_channel, after)

            await ctx.send(f"{count} reactions were given {'aboard the Erioch ' if is_global else ''}" +
                           f"today, {memtils.get_title(ctx.author)}.")

def setup(bot: commands.Bot):
    cogs = (
        TrainingWeeks,
        ServerStats,
        )
    for cog in cogs:
        bot.add_cog( cog(bot) )

if __name__ == "__main__":
    setup(commands.Bot("test"))

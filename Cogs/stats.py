"""Statistic getters"""

from discord import * 
from discord.ext import commands
from typing import *
import datetime as D
from Utils import common

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
        
        topics = ['aerial superiority', 'armour support']

        _, week_num, _ = today.isocalendar()
        # NOTE: 1st week: air, 2nd week: armour, 3rd week: air, etc.
        # This scales with the number of actual topics, no changes needed!
        topic = topics[week_num % len(topics) - 1]

        return topic

    @commands.command(aliases = ["week"])
    @common.in_bot_channel()
    async def get_training_week(self, ctx):
        """Get the training types for this week"""
        await ctx.send(f"This week we will train {self.training_type}, brother")


class ServerStats(commands.Cog):
    """Displays stats about the server."""
def setup(bot: commands.Bot):
    bot.add_cog(TrainingWeeks(bot))

if __name__ == "__main__":
    setup(commands.Bot("test"))
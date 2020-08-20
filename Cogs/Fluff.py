"""Any extra commands"""

from discord import *
from discord.ext import commands
from typing import *
from Utils.common import leader_roles
from datetime import datetime
from asyncio import sleep as async_sleep
from Utils.memtils import get_title, NameParser
from Utils.react_menu import ReactTable

class DTWMChanWorship(commands.Cog):
    """This Cog handles chanting 'DTWM'"""
    Chant = namedtuple("chant", ("person", "timestamp"))

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.chants: List[self.Chant] = []
        self.silenced_at: datetime = None  # when the bot was last silenced

    @commands.command(aliases = ["SC", "silence", "shut_up", "clear_comms"])
    @commands.has_any_role(*leader_roles)
    async def silence_chanting(self, ctx):
        """Clear the current chants and prevent chanting for five minutes."""
        self.chants = []
        self.silenced_at = datetime.now()
        await ctx.send("I shall keep the rabble quiet for five minutes, my lord")

    @commands.command(aliases = ["pray", "hail", "heil", "praise"])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def chant(self, ctx):
        """Join the chorus of chanting in the name of DTWM-chan."""
        from Utils.common import bot_channel  # this was sometimes None so it had to be imported here
        # check if in the bot channel
        if bot_channel and ctx.channel != bot_channel:
            return await ctx.send(f"You may only pray with the sevitors in {bot_channel.mention}")

        # check if silenced
        if self.silenced_at and (datetime.now() - self.silenced_at).total_seconds() // 60 < 5:
            return await ctx.send("The Watch Leaders wish you to be quiet to respect a fallen soul. " +
                                  "Please revere DTWM-chan silently")

        # record the chant
        self.chants.append(self.Chant(person = ctx.author, timestamp = datetime.now()))

        # create the DTWM chant and split it into chunks that can be sent
        CHARACTER_CAP = 2000
        msg = " ".join(["DTWM"] * (len(self.chants) + 1))
        if len(msg) > CHARACTER_CAP:
            msgs = [msg[chunk_num: chunk + CHARACTER_CAP]
                    for chunk_num in range(0, len(msg), CHARACTER_CAP)]
        else:
            msgs = [msg]

        # send the messages
        for msg in msgs:
            await ctx.send(msg)
            await async_sleep(1.5)
        await ctx.send("DTWM-chan's light has reached us all. " + 
                        "Thank you for your reverance " + get_title(ctx.author),
                        delete_after = 10)

    @commands.command(aliases = ["leaderboard", "TCu"])
    async def top_cultists(self, ctx):
        """List the 5 most devout worshippers of DTWM-chan."""
        # check if there has been no chants
        if not self.chants:
            return await ctx.send("The servitor bay is silent. We need more brothers to pray")

        # create typing prompt without indenting as the search is already pretty deep
        typing_indicator = await ctx.typing().__aenter__()
        # get each unqiue person and prepare to count their chants
        leaderboard = [[person, 0] for person in
                                                set((chant.person for chant in self.chants))]
        # for each message, find its author and increment their points
        for chant in self.chants:
            for index, row in enumerate(leaderboard):
                if row[0] == chant.person:
                    leaderboard[index][1] += 1
                    break

        # convert people to string and sort by points
        string_leaderboard = sorted([(person.display_name, points) for person, points in leaderboard],
                                    key = lambda record: record[1], reverse = True)
    
        ReactTable(("Name", "Number of Chants"), 
                   string_leaderboard,
                   self.bot,
                   ctx,
                   f"Our brothers have chanted {len(self.chants)} times in total. " + 
                   "Here are DTWM-chan's most loyal worshippers:",
                   elements_per_page = 5,
                    )
        await typing_indicator.__aexit__(*[None] * 3)  # pretend that no errors happened

    @commands.command(aliases = ["my_chants", "GC", "chants"])
    async def get_chants(self, ctx, target: Union[Member, str] = None, days: int = None):
        """Get the number of chants a person has done. Invoke without a name to get your own count.
        Defaults to their lifetime count, but you can pass a number of days (E.G today = 0)."""
        # check that there have been some chants
        if not self.chants:
            return await ctx.send("The servitor bay is silent. We need more brothers to pray")

        # get the Member object of the person
        if isinstance(target, str):
            target_member = ctx.guild.query_members(target)
        else:
            target_member = target if target else ctx.author

        lifetime_check = days is None  # used for overriding the time check if it's a lifetime count
        now = datetime.now()
        count = 0
        for chant in self.chants:
            if chant.person == target_member and (lifetime_check or \
                (now - chant.timestamp).days <= period):  # check that it falls within the period
                count += 1
        await ctx.send(f"{target_member.display_name} has chanted {count} times")

    
def setup(bot: commands.Bot):
    cogs = (
        DTWMChanWorship(bot),
        )

    for cog in cogs:
        bot.add_cog(cog)
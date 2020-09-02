"""Any extra commands"""

from discord import *
from discord.ext import commands
from typing import *
from Utils.common import leader_roles
from datetime import datetime
from asyncio import sleep as async_sleep
from Utils.memtils import get_title, NameParser
from Utils.mestils import send_as_chunks
from Utils.react_menu import ReactTable
from json import dumps
from functools import wraps

def has_chanted():
    """Check if the person has chanted before.
    If they haven't, initialise their list"""
    async def inner(ctx):
        cog = ctx.bot.get_cog("DTWMChanWorship")
        name = ctx.author.display_name
        if name not in cog.chants:
            cog.chants[name] = []
        return True
    return commands.check(inner)
    
class DTWMChanWorship(commands.Cog):
    """This Cog handles chanting 'DTWM'"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.chants: Dict[str, List[datetime]] = {} # format: {name: List of chant timestamps[]}
        self.silenced_at: datetime = None  # when the bot was last silenced

    @commands.command(aliases = ["silence", "shut_up", "clear_comms"])
    @commands.has_any_role(*leader_roles)
    @commands.cooldown(1, 300, commands.BucketType.user)  # 5 minute cooldown
    async def silence_chanting(self, ctx):
        """Clear the current chants and prevent chanting for five minutes."""
        self.chants = {}
        self.silenced_at = datetime.now()
        await ctx.send("I shall keep the rabble quiet for five minutes, my lord")

    @property
    def chants_number(self) -> int:
        """Get the total number of chants"""
        total = 0
        for person_chants in self.chants.values():
            total += len(person_chants)
        return total
    
    @commands.command(aliases = ["pray", "hail", "praise"])
    @commands.cooldown(1, 30, commands.BucketType.user)
    @has_chanted()
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
        self.chants[ctx.author.display_name].append(datetime.now())

        # create the DTWM chant
        msg = " ".join(["DTWM"] * self.chants_number)

        # send the messages
        await send_as_chunks(msg, ctx)
        await ctx.send("DTWM-chan's light has reached us all. " + 
                        "Thank you for your reverance " + get_title(ctx.author),
                        delete_after = 10)

    @commands.command(aliases = ["leaderboard", "TCu"])
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def top_cultists(self, ctx):
        """List the most devout worshippers of DTWM-chan."""
        # check if there has been no chants
        if not self.chants:
            return await ctx.send("The servitor bay is silent. We need more brothers to pray")

        async with ctx.typing():
            # get each person's chants
            leaderboard = [(name, len(person_chants)) for name, person_chants
                           in self.chants.items()]
    
            ReactTable(("Name", "Number of Chants"), 
                       sorted(leaderboard,  # sort by points
                              key = lambda record: record[1], reverse = True),
                       self.bot,
                       ctx,
                       f"Our brothers have chanted {self.chants_number} times in total. " + 
                       "Here are DTWM-chan's most loyal worshippers:",
                       elements_per_page = 3,
                        )

    @commands.command(aliases = ["my_chants", "GC", "chants"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def get_chants(self, ctx, target: Union[Member, str] = None, days: int = None):
        """Get the number of chants a person has done. Invoke without a name to get your own count.
        Defaults to their lifetime count, but you can pass a number of days (E.G today = 0)."""
        # check that there have been some chants
        if not self.chants:
            return await ctx.send("The servitor bay is silent. We need more brothers to pray")

        # get the name of the person
        if not isinstance(target, str):
            target_name = target.display_name if target else ctx.author.display_name
        else:  # check that the person exists
            matches = await ctx.guild.query_members(target)
            if matches:
                target_name = matches[0].display_name
            else:
                return await ctx.send("That person does not exist, " + get_title(ctx.author))

        # check if the person has chanted
        if target_name not in self.chants:
            return await ctx.send(f"{target_name} has not joined our choir!")

        # count chants within the period
        lifetime_check = days is None  # used for overriding the time check if it's a lifetime count
        now = datetime.now()
        count = 0
        for timestamp in self.chants[target_name]:
            # check that it falls within the period
            if (lifetime_check or (now - timestamp).days <= days):
                count += 1
        await ctx.send(f"{target_name} has chanted {count} time{'s' if count > 1 else ''}")

    @commands.command(aliases = ["SCC"])
    @commands.is_owner()
    @has_chanted()
    async def set_chant_count(self, ctx, count: int):
        """Add a number of dummy chants to self.chants. Debugging tool."""
        self.chants[ctx.author.display_name].extend([datetime.now()] * count)
        await ctx.send(f"I have added {count} chants, Adept {ctx.author.display_name}.")

    @commands.command(aliases = ["PC"])
    @commands.is_owner()
    async def print_chants(self, ctx):
        """Output self.chants. Debugging tool."""
        await send_as_chunks(
                             dumps(self.chants, indent = 4, default = str),
                             ctx, code_block = True)

    
def setup(bot: commands.Bot):
    cogs = (
        DTWMChanWorship(bot),
        )

    for cog in cogs:
        bot.add_cog(cog)
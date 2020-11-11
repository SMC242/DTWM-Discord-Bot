"""Any extra commands"""

from discord import *
from discord.ext import commands, tasks
from typing import *
from Utils.common import leader_roles
from datetime import datetime
from Utils.memtils import get_title
from Utils.mestils import send_as_chunks, chunk_message
from Utils.react_menu import ReactTable
from json import dumps
from collections import namedtuple


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
        # format: {name: List of chant timestamps[]}
        self.chants: Dict[str, List[datetime]] = {}
        self.silenced_at: datetime = None  # when the bot was last silenced

    @commands.command(aliases=["silence", "shut_up", "clear_comms"])
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

    @commands.command(aliases=["pray", "hail", "praise"])
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

        # send the messages
        await send_as_chunks(self._chant_inner(), ctx)
        await ctx.send("DTWM-chan's light has reached us all. " +
                       "Thank you for your reverance " + get_title(ctx.author),
                       delete_after=10)

    def _chant_inner(self) -> Tuple[str]:
        """Create the list of messages to send for ab!chant. Unit testable"""
        # create the DTWM chant
        msg = " ".join(["DTWM"] * self.chants_number)
        # split into chunks
        return chunk_message(msg)

    @commands.command(aliases=["leaderboard", "TCu"])
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def top_cultists(self, ctx):
        """List the most devout worshippers of DTWM-chan."""
        # check if there has been no chants
        if not self.chants:
            return await ctx.send("The servitor bay is silent. We need more brothers to pray")

        async with ctx.typing():
            ReactTable(("Name", "Number of Chants"),
                       self.leaderboard,
                       self.bot,
                       ctx,
                       f"{len(self.chants)} brothers have chanted "
                       f"{self.chants_number} times in total. " +
                       "Here are DTWM-chan's most loyal worshippers:",
                       elements_per_page=3,
                       )

    @property
    def leaderboard(self) -> List[Tuple[str, int]]:
        """Generate the leaderboard for chanting"""
        return sorted(
            [(name, len(person_chants)) for name, person_chants
             in self.chants.items()],
            key=lambda record: record[1], reverse=True)

    @commands.command(aliases=["my_chants", "GC", "chants"])
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
            if not matches:
                return await ctx.send("That person does not exist, " + get_title(ctx.author))
            target_name = matches[0].display_name

        # count the number of chants within the period
        count = self.count_person_chants(target_name, days)
        if count is None:
            return await ctx.send(f"{target_name} has not joined our choir!")
        await ctx.send(f"{target_name} has chanted {count} time{'s' if count > 1 else ''}")

    def count_person_chants(self, target_name: str, days: int = None) -> Optional[int]:
        """Get the number of chants for a person with a given period of days."""
        # check if the person has chanted
        if target_name not in self.chants:
            return None

        # count lifetime chants
        if days is None:
            return len(self.chants[target_name])

        # count chants within the period
        now = datetime.now()
        count = 0
        for timestamp in self.chants[target_name]:
            # check that it falls within the period
            if (now - timestamp).days <= days:
                count += 1
        return count

    @ commands.command(aliases=["SCC"])
    @ commands.is_owner()
    @ has_chanted()
    async def set_chant_count(self, ctx, count: int):
        """Add a number of dummy chants to self.chants. Debugging tool."""
        self.chants[ctx.author.display_name].extend([datetime.now()] * count)
        await ctx.send(f"I have added {count} chants, Adept {ctx.author.display_name}.")

    @ commands.command(aliases=["PC"])
    @ commands.is_owner()
    async def print_chants(self, ctx):
        """Output self.chants. Debugging tool."""
        await send_as_chunks(
            dumps(self.chants, indent=4, default=str),
            ctx, code_block=True)


class Trains(commands.Cog):
    class Train:
        channel_id: int
        msg_id: int
        period: float
        started: datetime
        text: str
        name: str
        content: str
        DEFAULT_TEMPLATE = """🚅*chugga chugga \|choo choo!*
**{content}**
*chugga chugga \|choo choo!*🚋"""

        def __init__(self, channel_id: int, msg_id: int, content: str,
                     name: str, period: float = 24, started: datetime = None,
                     text: str = None):
            self.channel_id = channel_id
            self.msg_id = msg_id
            self.period = period
            self.content = content
            self.name = name
            self.started = started or datetime.now()
            self.text = text or self.create_text(content)

        def create_text(self, content: str, template: str = None) -> str:
            """
            ### (method) create_text(content, template)
            Create a new text train.
            NOTE: seek the "/|" substrings to find where to insert the chuggas before.

            ### Parameters
                - `content`: `str`
                    The text to put in the middle of the train
                - `template`: `str`
                    The f-string template to create the train with.
                    This should contain `{content}` at least once

            ### Returns
                - `str`: The text train
            """
            if not template:
                template = self.DEFAULT_TEMPLATE

            if "{content}" not in template:
                raise ValueError("Invalid template format")

            self.text = template.format(content=content)
            return self.text

        def grow_train(self) -> str:
            """
            ### (method) grow_train(train, )
            Add some 'chugga chugga's to the train

            ### Returns
                - `str`: The new text train
            """
            """portions = msg.content.split("choo")
            text_portions = list(filter(lambda x: len(x) > 2, portions))
            chuggas = "chugga chugga "
            new_portions = [text_portions[0] + chuggas,
                            text_portions[1] + chuggas, text_portions[2]]
            new_content = (new_portions[0] + "choo choo" +
                           new_portions[1] + "choo choo" + new_portions[2])"""

            # find the `\|`s
            portions = self.text.split("\|")
            # NOTE: the split removes the delimiter so it must be added again
            to_insert = "chugga chugga \|"
            portions[0] = portions[0] + to_insert
            portions[1] = portions[1] + to_insert
            self.text = "\|".join(portions)
            return self.text

        @property
        def sendable(self) -> str:
            """
            ### (method) sendable()
            Get the train as a single message.
            This will return an error string if the train gets too big or it has expired.

            ### Returns
                `str`:
                    The string to send.
            """
            ERROR_STRING = "👮‍♂️The train has reached the station👮‍♂️"
            return self.text if len(self.text) < 2000 else ERROR_STRING

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # format: train name: TrainInfo
        self.active_trains: Dict[str, self.TrainInfo] = {}

    async def create_train_msg(self, ctx, msg_content: str, name: str, period: float = 24.0):
        """Create a train message that has `msg_content` in the middle of it.
        The train will get progressively bigger over the next `period` hours"""
        if name in self.active_trains:
            return await ctx.send("That name is already in use.")

        train = self.Train(ctx.channel.id, ctx.msg.id,
                           msg_content, name, period,
                           ctx.msg.created_at,
                           )
        self.active_trains[name] = train
        await ctx.send(train.sendable)

    async def edit_train(self, train: Train) -> Optional[Train]:
        """
        ### (method) edit_train(train, )
        Update the train with more chuggas

        ### Parameters
            - `train`: `TrainInfo`
                The train to edit

        ### Returns
            `Optional[TrainInfo]`:
                The train if it was edited successfully.
        """
        # handle the message being deleted
        try:
            msg = await self.bot.get_channel(train.channel_id).fetch_message(train.msg_id)
        except (HTTPException, AttributeError):
            return False

        train_text = self.grow_train(train.text)
        await msg.edit(content=train_text)

    @tasks.loop(hours=2)
    async def update_trains(self):
        """
        ### (method) update_trains()
        Grow all of the active trains every 2 hours
        """
        pass


def setup(bot: commands.Bot):
    cogs = (
        DTWMChanWorship(bot),
    )

    for cog in cogs:
        bot.add_cog(cog)

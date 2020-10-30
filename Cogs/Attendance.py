"""The database interface."""

from discord import Member, File, Forbidden, Embed
from discord.ext import commands
from typing import *
from contextlib import suppress
import datetime as D
from Utils import common, memtils, AttendanceDB as db, react_menu
from asyncio import sleep as async_sleep, get_event_loop
from Utils.mestils import create_table
from .event_handler_modules.error_handler import CommandNotImplementedError


class KickSuggestionMenu(react_menu.ReactTable):
    """A specialised reaction table for kicking people."""

    def __init__(self, table_rows: Tuple[
            List[Tuple[str, int, str, str, str]],
            str, str],
            ctx: commands.Context, percent_warned: str,
            percent_kicked: str):
        self._att_cog = ctx.bot.get_cog("Attendance")
        headers = ("Name", "Attendance Ratio (%)", "Recommended Action",
                   "Away (True/False)", "Join Date")

        # give information about how to interact with the menu
        # and the warn/kick stats
        self.stats = (percent_warned, percent_kicked)
        info = ("This is my opinion, my lord. " +
                f"{self.stats[0]} of the outfit would be warned " +
                f"and {self.stats[1]} would be kicked. " +
                "Click the ban hammer to kick the currently selected member " +
                "or click the X to skip them.")

        # initialise the ReactMenu
        super().__init__(headers, table_rows, ctx.bot,
                         ctx.channel, on_select=self.kick,
                         on_reject=self.skip, message_text=info,
                         select_emote_id=594462835082526721)

    @staticmethod
    async def kick(self):
        """Kick someone from the outfit
        when the yes button is clicked."""
        # get the Member instance
        name = self.content[self._content_index][0]
        person = await memtils.search_member(self.channel.guild, name)

        # kick them
        if person:
            await self._att_cog.kick_member(person)

        # remove them from content and move to the next index
        await self.skip(self)

    @staticmethod
    async def skip(self):
        """Pass on kicking someone
        when the no button is clicked."""
        # remove them from content and move to the next index
        if self._content_index < len(self.content) - 1:
            # this order is necessary to avoid the length check of on_next
            await self.on_next(self)
            del self.content[self._content_index - 1]
            self._content_index -= 1
        # display nothing left when all members have been
        # kicked or rejected
        else:
            embed = Embed(**self.embed_settings)
            embed.add_field(name="All done", value="No suggested actions left")
            await self.msg.edit(embed=embed)

            # remove all the reactions
            for reaction in self.msg.reactions:
                await reaction.remove(self._bot.user)

            # remove self from the tracked instances
            self.unregister()


class Attendance(commands.Cog):
    """Commands relating to attendance.

    Commands and their alias:
        add_all_members, AAM
        add_member, AM
        remove_member, RM
        remove_member_by_id, RMI
        do_attendance, DATT
        list_members, LM
        get_att, att
        get_event_att, Eatt
        joined_at, JA
        joined_at_by_ID, JAI

    New Scouts are automatically registered to the database."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = db.AttendanceDBWriter()

    @commands.Cog.listener()
    @commands.has_any_role(*common.leader_roles)
    async def on_member_update(self, before: Member, after: Member):
        """Add new scouts to the Members table automatically"""
        # get the roles that were added
        new_role_names = [
            role_.name for role_ in after.roles if role_ not in before.roles]
        if "Scout" in new_role_names:
            # get their name
            name = memtils.NameParser(after.display_name).parsed

            # only register them if they're not already registered
            if not await memtils.is_member(name,
                                           [r[1] for r in self.db.get_all_members()]):
                self.db.add_member(name)
                print(f"New member detected: {name}")

    @commands.command(aliases=["AAM"])
    @commands.has_any_role(*common.leader_roles)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def add_all_members(self, ctx):
        """Add all current members to the Members table."""
        async with ctx.typing():
            in_outfit = await memtils.get_in_outfit()
            registered = [r[1] for r in self.db.get_all_members()]

            # register them if they're not already in the DB
            count = 0  # count every person added to the DB
            for name in in_outfit:
                if not await memtils.is_member(name, registered):
                    self.db.add_member(name)
                    count += 1

            # give feedback
            await ctx.send(f"{count} new brothers have been registered, my lord.")

    @commands.command(aliases=["AM"])
    @commands.has_any_role(*common.leader_roles)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def add_member(self, ctx, name: str):
        """Register a member with their name."""

        # check that the name isn't registered
        if not await memtils.is_member(name,
                                       [r[1] for r in self.db.get_all_members()]):
            self.db.add_member(name)
            await ctx.send(f"Welcome to the chapter, brother {name}!")
        else:
            await ctx.send(f"{name} is already registered!")

    @commands.command(aliases=["RM"])
    @commands.has_any_role(*common.leader_roles)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def remove_member(self, ctx, name: str):
        """Unregister a member by their name."""
        # parse the name
        name = memtils.NameParser(name).parsed

        # validate the name
        if not memtils.is_member(name, [r[1] for r in self.db.get_all_members()]):
            return await ctx.send("That person is not in our chapter!")

        self.db.delete_member(name)
        await ctx.send("Another brother lost to the warp...")

    @commands.command(aliases=["RMI"])
    @commands.has_any_role(*common.leader_roles)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def remove_member_by_id(self, ctx, id: int):
        """Unregister a member by their id"""
        # validate the id
        if id not in [r[0] for r in self.db.get_all_members()]:
            return await ctx.send("I cannot find a brother of that number, my lord")

        self.db.delete_member_by_id(id)
        await ctx.send("Another brother lost to the warp...")

    @commands.command(aliases=["DATT"])
    @commands.has_any_role(*common.leader_roles)
    @commands.cooldown(1, 5400, commands.BucketType.user)
    async def do_attendance(self, ctx):
        """Get the names of all people in the event voice channels
        then send it to the DB in 90 minutes."""
        # calculate when attendance_inner will finish
        return_time = (D.datetime.today() +
                       D.timedelta(minutes=90)).strftime("%H:%M")
        await ctx.send(f"I will return at {return_time}, my lord")
        attendees = await self.attendance_inner()
        return await ctx.send(f"Our men have been counted.\nAttendees: {list(attendees)}")

    async def attendance_inner(self) -> List[str]:
        """Get the names of all people in the event voice channels,
        then send it to the Attendees table in 90 minutes,
        and return the attendees' names"""
        PERIOD = 5400 if not common.DEV_VERSION else 300  # the total period in seconds
        STEP = PERIOD // 4  # how long to wait per scan

        # get the event channels
        with open("./Text Files/channels.txt") as f:
            channel_ids = [int(line.strip("\n")) for line in f.readlines()]

        channels = [self.bot.get_channel(id) for id in channel_ids]

        # repeat every `STEP` minutes
        attendees = set()  # ensure no duplicates
        for i in range(4):
            # add each person in each event channel to attendees
            for channel in channels:
                for name in [person.display_name for person in channel.members]:
                    attendees.add(memtils.NameParser(name).parsed)

            # sleep for 30 minutes
            # but don't wait a fourth time
            print(f"{attendees} at roll call {i}")
            if i == 3:
                break
            else:
                await async_sleep(STEP)

        # record the attendance
        print(f"Recording attendees: {attendees}")
        self.db.record_att(attendees)
        return attendees

    @commands.command(aliases=["LM"])
    @commands.has_any_role(*common.leader_roles)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def list_members(self, ctx):
        """List all of the registered members"""
        async def wrap(self) -> Tuple[int, str]:
            """Get the memberID and name of all members."""
            rows = [(row[0], row[1])
                    for row in self.db.get_all_members()]
            # handle no registered members
            if not rows:
                raise ValueError("No members are registered")
            return rows

        # create a table
        async with ctx.typing():
            try:
                react_menu.ReactTable(("ID", "Name"), await wrap(self),
                                      self.bot, ctx.channel,
                                      message_text="They are ready to serve, my lord:",
                                      elements_per_page=3,
                                      random_colour=True,
                                      )
            except ValueError:
                await ctx.send("None of our men have been registered, my lord")

    @commands.command(aliases=["att"])
    @commands.has_any_role(*common.leader_roles)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def get_attendance(self, ctx):
        """Get the average attendance per member for this month."""
        # this is necessary to cede control to the event loop
        # while not making the query itself async
        # if the query was async, it could cause the DB to be locked
        async def wrap(self) -> str:
            return self.db.get_att_per_member()

        async with ctx.typing():
            try:
                table_path = await wrap(self)
                react_menu.ReactTable(("Name", "Attendance (%)", "Away (yes or no)"),
                                      await wrap(self),
                                      self.bot,
                                      ctx,
                                      elements_per_page=3,
                                      random_colour=True,
                                      )
            # handle no attendance data
            except ValueError:
                await ctx.send("Our archives fail us... I cannot find any roll calls")

    @commands.command(aliases=["Eatt"])
    @commands.has_any_role(*common.leader_roles)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def get_event_attendance(self, ctx):
        """Get the average attendance per event type for this month"""
        async def wrap(self) -> str:
            return self.db.get_att_per_event()

        async with ctx.typing():
            try:
                react_menu.ReactTable(("Event type", "Attendance %"),
                                      await wrap(self),
                                      self.bot,
                                      ctx,
                                      elements_per_page=2,
                                      )
            # handle no attendance data
            except ValueError:
                await ctx.send("Our archives fail us... I cannot find any roll calls")

    @commands.command(aliases=["JA"])
    @commands.has_any_role(*common.leader_roles)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def joined_at(self, ctx, name: str):
        """Get the join date of a member by their name."""
        # parse the name
        name = memtils.NameParser(name).parsed
        joined_at = self.db.get_join_date_by_name(name)
        # handle no member found
        if not joined_at:
            await ctx.send(f'Our archives do not know this "{name}"')
        else:
            await ctx.send(f"He joined our chapter on {joined_at.strftime('%d.%m')}")

    @commands.command(aliases=["JAI"])
    @commands.has_any_role(*common.leader_roles)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def joined_at_by_id(self, ctx, id: int):
        """Get the join date of a member by their ID."""
        joined_at = self.db.get_join_date_by_id(id)
        # handle no member found
        if not joined_at:
            await ctx.send(f'Our archives do not know this "{name}"')
        else:
            await ctx.send(f"He joined our chapter on {joined_at.strftime('%d.%m')}")

    @commands.command(aliases=["ND"])
    @commands.is_owner()
    async def new_day(self, ctx, event_type: str):
        """Create a new day in the database. The event type must be one of the following:
        air, armour, infantry, co-ops1, co-ops2, internal_ops"""
        # it must be uppercase
        event_type = event_type.upper()
        # verify the event_type
        if event_type not in ("AIR", "ARMOUR", "INFANTRY", "CO-OPS1", "CO-OPS2", "INTERNAL_OPS"):
            return await ctx.send("We don't do that kind of event!")
        else:
            self.db.new_day(event_type)
            await ctx.send("A new day has begun")

    @commands.command(aliases=["MATT", "MY_ATT"])
    @commands.has_any_role(*common.member_roles)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def get_my_attendance(self, ctx):
        """Get your attendance %"""
        name = memtils.NameParser(ctx.author.display_name).parsed
        ratio = self.db.get_member_att(name)
        if ratio is None:
            await ctx.send("You haven't attended any events, brother. Please join our future wars!")
        else:
            await ctx.send(f"{memtils.get_title(ctx.author)}, your attendance ratio is: {ratio}")

    @commands.command(aliases=["V5", "hop_in"])
    @commands.has_any_role(*common.leader_roles)
    @commands.cooldown(1, 5400, commands.BucketType.user)
    async def get_in_ops(self, ctx):
        """Pings everyone currently playing Planetside 2 to get in ops."""
        await ctx.send("I will summon our chapter, my lord")
        await self.get_in_ops_inner()

    async def get_in_ops_inner(self):
        """See the parent method. 
        This exists so that it can be called outside of the bot command"""
        async with common.bot_channel.typing():
            # get all the outfit members
            in_outfit = await memtils.get_in_outfit(True)

            # get people playing PS2
            in_game = [person for person in in_outfit
                       if "Planetside 2" in [
                           act.name for act in person.activities
                       ]
                       ]

            # get the event voice channel ids
            with open("./Text Files/channels.txt") as f:
                ids = [int(row.strip("\n")) for row in f.readlines()]

            channels = [self.bot.get_channel(id) for id in ids]

            # ping them if they're not in those channels
            for person in in_game:
                # search for them in the channels
                found = False
                for channel in channels:
                    if person in channel.members:
                        found = True
                        break

                # ping them if they weren't found
                if not found:
                    await common.bot_channel.send(
                        f"Come quickly, brother, an event is starting {person.mention}!")

    @commands.command(aliases=["away", "A"])
    @commands.has_any_role(*common.leader_roles)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def mark_as_away(self, ctx, name: str):
        """Mark the target as away in the database."""
        # parse the name
        name = memtils.NameParser(name).parsed
        member_found = self.db.mark_away(name)

        # report whether the query was successful
        if member_found:
            await ctx.send("May he return to action soon, my lord.")
        else:
            await ctx.send(f'''Our archives don't know of this "{name}", my lord.''')

    @commands.command(aliases=["IA"])
    @commands.has_any_role(*common.leader_roles)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def is_away(self, ctx, name: str):
        """Get whether the person is away."""
        # parse the name
        name = memtils.NameParser(name).parsed
        row = self.db.get_member_by_name(name)
        if row:
            await ctx.send(f'''{name} is marked as {"not" if not row[2] else ""} away in our archives, my lord.''')
        else:
            await ctx.send(f'''Our archives don't know of this "{name}", my lord.''')

    async def kick_member(self, person: Member):
        """Remove the person from the outfit, move them to Guardsman,
           and DM them about it.

           This is its own method so that get_attendance can be
           extended to auto-kick people."""
        # remove them from the DB
        self.db.delete_member(memtils.NameParser(person.display_name).parsed)

        # get the member-only roles roles
        member_role_ids = [
            588061401617268746,  # Custodes
            564827583540363264,  # Ogryn
            729040717636304948,  # Null Maiden
            702914817157234708,  # Noise Marine
            564827583540363264,  # Remembrancer
            696160922439385091,  # Arbites
            696160804940152982,  # Chrono-gladiator
            545804189180231691,  # Keeper
            545807109774770187,  # Astartes
            545804149821014036,  # Scout
            545804220763340810,  # Champion,
            545819032868356395,  # Chaplain
        ]
        guild = person.guild
        member_roles = [guild.get_role(id) for id in member_role_ids]

        # move them to Guardsman
        await person.remove_roles(*member_roles, reason="Kicked from the outfit")
        await person.add_roles(guild.get_role(545803265741291521), reason="Kicked from the outfit")

        # DM them
        try:
            await person.send("You've been kicked from the chapter because you haven't" +
                              " attended enough events this month." +
                              " You can return in 2 weeks if you have more time :)")
        # ping them in the bot channel if they can't be DMed
        except Forbidden:
            await common.bot_channel.send(f"{person.mention} You've been kicked from the chapter " +
                                          "because you haven't attended enough events this month." +
                                          " You can return in 2 weeks if you have more time :)")

    @commands.command(aliases=["K"])
    @commands.has_any_role(*common.leader_roles)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def kick(self, ctx, person: Union[Member, str]):
        """Kick a person from the outfit. Mention them...
        They will be moved to Guardsman, unregistered, and DMed."""
        async with ctx.typing():
            # handle no Member passed
            if isinstance(person, str):
                person = await memtils.search_member(ctx, person)
                # handle no Member found
                if not person:
                    return await ctx.send("I can't find that person, my lord")

            # validate the person
            if not await memtils.is_member(person.display_name,
                                           [r[1] for r in self.db.get_all_members()]):
                await ctx.send("That person is not in our chapter!")
            else:
                # easter-egg
                if memtils.check_roles(person, common.leader_roles):
                    return await ctx.send("You know that regicide is illegal," +
                                          f" {memtils.get_title(person)}")

                await self.kick_member(person)
                await ctx.send("He has been expelled, my lord")

    @commands.command(aliases=["RA"])
    @commands.has_any_role(*common.leader_roles)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def remove_away(self, ctx, name: str):
        """Remove a person's away status."""
        name = memtils.NameParser(name).parsed
        # validate the person
        if not await memtils.is_member(name, [r[1] for r in self.db.get_all_members()]):
            await ctx.send("That person is not in our chapter!")
        else:
            self.db.unmark_away(name)
            await ctx.send("An old face has returned :D")

    @commands.command(aliases=["SK", "SKSKSKSKSKSKSKSKSK_GIVE_ME_THE_TEA_SIS"])
    @commands.has_any_role(*common.leader_roles)
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def suggest_kicks(self, ctx):
        """Suggest who should be kicked this month."""
        async def wrap(self) -> Tuple[
                List[Tuple[str, int, str, str, str]],
                str, str]:
            return self.db.suggest_kicks()

        async with ctx.typing():
            try:
                table_rows, *stats = await wrap(self)

                # create the reaction table
                KickSuggestionMenu(table_rows, ctx, *stats)
            except ValueError:
                await ctx.send("I have no archive entries to base my opinion on, my lord")

    # @commands.command(aliases = ["K"])
    # @commands.has_any_role(*common.leader_roles)
    async def get_attendance_plus(self, ctx):
        """get_attendance but it allows browsing each person and kicking them."""
        # use mestils.search_member to get the person
        # then use ReactMenu on_reject to call Attendance.kick on them
        raise CommandNotImplementedError()


def setup(bot):
    bot.add_cog(Attendance(bot))


if __name__ == "__main__":
    setup(commands.Bot("TEST"))

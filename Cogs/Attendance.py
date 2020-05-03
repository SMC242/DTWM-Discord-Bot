"""The database interface."""

from discord import Member, File, Forbidden
from discord.ext import commands
from typing import *
from contextlib import suppress
import datetime as D
from Utils import common, memtils, AttendanceDB as db
from asyncio import sleep as async_sleep
from prettytable import PrettyTable
from .Event_handlers import CommandNotImplementedError

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
        common.load_bot(bot)

    @commands.Cog.listener()
    @commands.has_any_role(*common.leader_roles)
    @common.in_bot_channel()
    async def on_member_update(self, before: Member, after: Member):
        """Add new scouts to the Members table automatically"""
        # get the roles that were added
        new_role_names = [role_.name for role_ in after.roles if role_ not in before.roles]
        if "Scout" in new_role_names:
            # get their name
            name = await memtils.NameParser(after.display_name).parse()

            # only register them if they're not already registered
            if not self.db.get_member_by_name(name):
                self.db.add_member(name)
                print(f"New member detected: {name}")

    @commands.command(aliases = ["AAM"])
    @commands.has_any_role(*common.leader_roles)
    @common.in_bot_channel()
    async def add_all_members(self, ctx):
        """Add all current members to the Members table."""
        with ctx.typing():
            in_outfit = await memtils.get_in_outfit()

            # register them if they're not already in the DB
            count = 0  # count every person added to the DB
            for name in in_outfit:
                if not self.db.get_member_by_name(name):
                    self.db.add_member(name)
                    count += 1

            # give feedback
            await ctx.send(f"{count} new brothers have been registered, my lord.")

    @commands.command(aliases = ["AM"])
    @commands.has_any_role(*common.leader_roles)
    @common.in_bot_channel()
    async def add_member(self, ctx, name: str):
        """Register a member with their name."""
        # parse the name
        name = await memtils.NameParser(name).parse()
        
        # check that the name isn't registered
        if name not in [row[1] for row in self.db.get_all_members()]:
            self.db.add_member(name)
            await ctx.send(f"Welcome to the chapter, brother {name}!")
        else:
            await ctx.send(f"{name} is already registered!")

    @commands.command(aliases = ["RM"])
    @commands.has_any_role(*common.leader_roles)
    @common.in_bot_channel()
    async def remove_member(self, ctx, name: str):
        """Unregister a member by their name."""
        # parse the name
        name = await memtils.NameParser(name).parse()
        self.db.delete_member(name)
        await ctx.send("Another brother lost to the warp...")

    @commands.command(aliases = ["RMI"])
    @commands.has_any_role(*common.leader_roles)
    @common.in_bot_channel()
    async def remove_member_by_id(self, ctx, id: int):
        """Unregister a member by their id"""
        self.db.delete_member_by_id(id)
        await ctx.send("Another brother lost to the warp...")

    @commands.command(aliases = ["DATT"])
    @commands.has_any_role(*common.leader_roles)
    @common.in_bot_channel()
    async def do_attendance(self, ctx):
        """Get the names of all people in the event voice channels
        then send it to the DB in 90 minutes."""
        # calculate when attendance_inner will finish
        return_time = (D.datetime.today() + D.timedelta(minutes = 90)).strftime("%H:%M")
        await ctx.send(f"I will return at {return_time}, my lord")
        attendees = await self.attendance_inner()
        return await ctx.send(f"Our men have been counted.\nAttendees: {list(attendees)}")

    async def attendance_inner(self) -> List[str]:
        """Get the names of all people in the event voice channels,
        then send it to the Attendees table in 90 minutes,
        and return the attendees' names"""
        # get the event channels
        with open("./Text Files/channels.txt") as f:
            channel_ids = [int(line.strip("\n")) for line in f.readlines()]

        channels = [self.bot.get_channel(id) for id in channel_ids]

        # repeat every 30 minutes
        attendees = set()  # ensure no duplicates
        for i in range(4):
            # add each person in each event channel to attendees
            for channel in channels:
                for name in [person.display_name for person in channel.members]:
                    attendees.add(await memtils.NameParser(name).parse())

            # sleep for 30 minutes 
            # but don't wait a fourth time
            print(f"{attendees} at roll call {i}")
            if i == 3:
                break
            else:
                await async_sleep(1800)

        # record the attendance
        print(f"Recording attendees: {attendees}")
        self.db.record_att(attendees)
        return attendees

    @commands.command(aliases = ["LM"])
    @commands.has_any_role(*common.leader_roles)
    @common.in_bot_channel()
    async def list_members(self, ctx):
        """List all of the registered members"""
        # create a PrettyTable
        table = PrettyTable(["ID", "Name"])
        for row in self.db.get_all_members():
            table.add_row( (row[0], row[1]) )
        
        await ctx.send(f"They are ready to serve, my lord:```\n{table.get_string()}```")

    @commands.command(aliases = ["att"])
    @commands.has_any_role(*common.leader_roles)
    @common.in_bot_channel()
    async def get_attendance(self, ctx):
        """Get the average attendance per member for this month."""
        try:
            table_path = await self.db.get_att_per_member()
            await ctx.send("Here are the results for this month, my lord:", 
                           file = File(table_path)
                           )
        # handle no attendance data
        except ValueError:
            await ctx.send("Our archives fail us... I cannot find any roll calls")

    @commands.command(aliases = ["Eatt"])
    @commands.has_any_role(*common.leader_roles)
    @common.in_bot_channel()
    async def get_event_attendance(self, ctx):
        """Get the average attendance per event type for this month"""
        try:
            table_path = await self.db.get_att_per_event()
            await ctx.send("These are the results for this month's events, my lord:", 
                           file = File(table_path)
                           )
        # handle no attendance data
        except ValueError:
            await ctx.send("Our archives fail us... I cannot find any roll calls")

    @commands.command(aliases = ["JA"])
    @commands.has_any_role(*common.leader_roles)
    @common.in_bot_channel()
    async def joined_at(self, ctx, name: str):
        """Get the join date of a member by their name."""
        # parse the name
        name = await memtils.NameParser(name).parse()
        joined_at = self.db.get_join_date_by_name(name)
        # handle no member found
        if not joined_at:
            await ctx.send(f'Our archives do not know this "{name}"')
        else:
            await ctx.send(f"He joined our chapter on {joined_at.strftime('%d.%m')}")

    @commands.command(aliases = ["JAI"])
    @commands.has_any_role(*common.leader_roles)
    @common.in_bot_channel()
    async def joined_at_by_id(self, ctx, id: int):
        """Get the join date of a member by their ID."""
        joined_at = self.db.get_join_date_by_id(id)
        # handle no member found
        if not joined_at:
            await ctx.send(f'Our archives do not know this "{name}"')
        else:
            await ctx.send(f"He joined our chapter on {joined_at.strftime('%d.%m')}")

    @commands.command(aliases = ["ND"])
    @commands.is_owner()
    @common.in_bot_channel()
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

    @commands.command(aliases = ["MATT", "MY_ATT"])
    @commands.has_any_role(*common.member_roles)
    @common.in_bot_channel()
    async def get_my_attendance(self, ctx):
        """Get your attendance %"""
        name = await memtils.NameParser(ctx.author.display_name).parse()
        ratio = self.db.get_member_att(name)
        if ratio is None:
            await ctx.send("You haven't attended any events, brother. Please join our future wars!")
        else:
            await ctx.send(f"{memtils.get_title(ctx.author)}, your attendance ratio is: {ratio}")

    @commands.command(aliases = ["V5", "hop_in"])
    @commands.has_any_role(*common.leader_roles)
    @common.in_bot_channel()
    async def get_in_ops(self, ctx):
        """Pings everyone currently playing Planetside 2 to get in ops."""
        await ctx.send("I will summon our chapter, my lord")
        await self.get_in_ops_inner()

    async def get_in_ops_inner(self):
        """See the parent method. 
        This exists so that it can be called outside of the bot command"""
        with common.bot_channel.typing():
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

    @commands.command(aliases = ["away", "A"])
    @commands.has_any_role(*common.leader_roles)
    @common.in_bot_channel()
    async def mark_as_away(self, ctx, name: str):
        """Mark the target as away in the database."""
        # parse the name
        name = await memtils.NameParser(name).parse()
        member_found = self.db.mark_away(name)

        # report whether the query was successful
        if member_found:
            await ctx.send("May he return to action soon, my lord.")
        else:
            await ctx.send(f'''Our archives don't know of this "{name}", my lord.''')

    @commands.command(aliases = ["IA"])
    @commands.has_any_role(*common.leader_roles)
    @common.in_bot_channel()
    async def is_away(self, ctx, name: str):
        """Get whether the person is away."""
        # parse the name
        name = await memtils.NameParser(name).parse()
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
        self.db.delete_member(await memtils.NameParser(person.display_name).parse())

        # get the member-only roles roles
        member_role_ids = [
            545804363084333087,  # Watch Commander
            550052642001518592,  # Watch Leader
            588061401617268746,  # Custodes
            702914817157234708,  # Noise Marine
            564827583540363264,  # Remembrancer
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
        await person.remove_roles(*member_roles, reason = "Kicked from the outfit")
        await person.add_roles(guild.get_role(545803265741291521), reason = "Kicked from the outfit")

        # DM them
        with suppress(Forbidden):
            await person.send("You've been kicked from the chapter because you haven't" + 
                              " attended enough events this month." +
                              " You can return in 2 weeks if you have more time :)")

    @commands.command(aliases = ["K"])
    @common.in_bot_channel()
    @commands.has_any_role(*common.leader_roles)
    async def kick(self, ctx, person: Member):
        """Kick a person from the outfit. Mention them...
        They will be moved to Guardsman, unregistered, and DMed."""
        # validate the person
        if await memtils.NameParser(person.display_name).parse() not in \
            [row[1] for row in self.db.get_all_members()]:
            await ctx.send("That person is not in our chapter!")
        else:
            await self.kick_member(person)

    #@commands.command(aliases = ["K"])
    #@common.in_bot_channel()
    #@commands.has_any_role(*common.leader_roles)
    async def get_attendance_plus(self, ctx):
        """get_attendance but it allows browsing each person and kicking them."""
        # use mestils.search_member to get the person
        # then use ReactMenu on_reject to call Attendance.kick on them
        raise CommandNotImplementedError()

def setup(bot):
    bot.add_cog(Attendance(bot))

if __name__ == "__main__":
    setup(commands.Bot("TEST"))
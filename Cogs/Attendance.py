"""The database interface."""

from discord import member, File
from discord.ext import commands
from typing import *
from BenUtils import db
import sqlite3 as sql, datetime as D
from Utils import common, memtils, mestils
from contextlib import suppress
from prettytable import PrettyTable
from asyncio import sleep as async_sleep

class AttendanceDBWriter(db.DBWriter):
    """Handles the attendance database and accessing it."""

    def __init__(self):
        db.DBWriter.__init__(self, "Attendance")

        # create the table if it doesn't exist
        self.create_tables()

    def new_day(self, event_type: str):
        """Add a new day to the Days table.
        
        ARGUMENTS
        event_type:
            Must be within: AIR, ARMOUR, INFANTRY, CO-OPS1,
            CO-OPS2, INTERNAL_OPS"""
        # ensure that the table check doesn't fail
        if event_type not in ("AIR", "ARMOUR", "INFANTRY", "CO-OPS1", "CO-OPS2", "INTERNAL_OPS"):
            raise ValueError("Invalid event_type")

        # if the day was already registered
        with suppress(sql.IntegrityError):
            self.cursor.execute("""INSERT INTO Days(date, eventType) VALUES (
                    ( SELECT DATE('now') ),
                    ?
                );""", [event_type]
                )
            self.connection.commit()

    def create_tables(self):
        """Create the tables if they're not already created."""
        self._executeFromFile("./Text Files/table_definitions.txt")

    # any methods that the bot will access have been made coroutines
    def add_member(self, name: str):
        """Add a member to the Members table."""
        self.doQuery("INSERT INTO Members(name) VALUES(?);", vars = [name])

    def get_member_by_name(self, name: str) -> Optional[Tuple[int, str, bool, str]]:
        """
        Get the row of a member by their name.

        RETURNS
        None: 
            No member was found.
        Tuple[memberID: int, name: str, away: bool, joinedAt: datetime.date]: 
            The member that was found.
            If multiple members were found, the first one will be returned.
        """
        # fetch the row(s)
        rows = self.doQuery(
            "SELECT memberID, name, away, joinedAt FROM Members WHERE name = ?;", 
            vars = [name])

        # check if nothing was found
        if not rows:
            return None
        else:
            # get the first member
            first_member = rows[0]
            # convert away to bool
            away = bool(first_member[2])
            # convert joinedAt to D.date
            joined_at = D.datetime.strptime(first_member[3], "%Y-%m-%d").date()

            return first_member[:-2] + (away, joined_at)

    def get_member_by_id(self, id: int) -> Optional[Tuple[int, str, bool, D.date]]:
        """
        Get the row of a member by their id.

        RETURNS
        None: 
            No member was found.
        Tuple[memberID: int, name: str, away: bool, joined_at: datetime.date]: 
            The member that was found.
            If multiple members were found, the first one will be returned.
        """
        # fetch the row(s)
        rows = self.doQuery(
            "SELECT memberID, name, away, joinedAt FROM Members WHERE memberID = ?;", 
            [id])

        # check if nothing was found
        if not rows:
            return None
        else:
            # get the first member
            first_member = rows[0]
            # convert away to bool
            away = bool(first_member[2])
            # convert joinedAt to D.date
            joined_at = D.datetime.strptime(first_member[3], "%Y-%m-%d").date()

            return first_member[:-2] + (away, joined_at)

    def delete_member(self, name: str):
        """Delete a member from the Members table by their name."""
        self.doQuery("DELETE FROM Members WHERE name = ?;", [name])

    def delete_member_by_id(self, id: int):
        """Delete a member from the Members table by their id."""
        self.doQuery("DELETE FROM Members WHERE memberID = ?;", [id])

    def record_att(self, attendees: Iterable[str]):
        """
        Mark the attendees as attended in the Attendees table.

        ARGUMENTS
        attendees:
            The list of names of people who attended.
            These names are expected to be parsed by Utils.memtils.NameParser
            with the default settings.
        """
        # get registered members
        members = [row[1] for row in self.get_all_members()]

        # ensure that Members isn't empty
        if not members:
            raise ValueError("No members in the DB")

        # mark attended = True/False depending on whether their name is in attendees
        to_insert = [
            (name, 1) if name in attendees else (name, 0)
            for name in members         
            ]
        
        # send to DB
        self.doQuery("""INSERT INTO Attendees(date, memberID, attended) VALUES(
                ( SELECT DATE('now') ),
                ( SELECT memberID FROM Members WHERE name = ? ),
                ?
            );""",
            to_insert, True
            )

    def get_join_date_by_name(self, name: str) -> Optional[D.date]:
        """Get the join date of a member by their name.
        
        RETURNS
        None: the member wasn't found.
        datetime.Date: the date that the member joined at."""
        try:
            row = self.doQuery("SELECT joinedAt FROM Members WHERE name = ?;", [name])[0]
            return D.datetime.strptime(row[0], "%Y-%m-%d").date()
        except IndexError:
            return None

    def get_join_date_by_id(self, id: int) -> Optional[D.date]:
        """Get the join date of a member by their name
        
        RETURNS
        None: the member wasn't found.
        datetime.Date: the date that the member joined at."""
        try:
            row = self.doQuery("SELECT joinedAt FROM Members WHERE memberID = ?;", [id])[0]
            return D.datetime.strptime(row[0], "%Y-%m-%d").date()
        except IndexError:
            return None

    async def get_att_per_member(self) -> str:
        """Get this month's attendance and save it as an image.

        RETURNS
            The path the the table image.
            
        RAISES
            ValueError: No attendance data returned from Attendees."""
        # get all members because executemany doesn't support SELECT
        members = [row[1] for row in self.get_all_members()]

        # get the target month for the LIKE clause
        target_month = D.datetime.today().strftime("%Y-%m-") + "%"

        # get the attendance per member and whether they were away
        rows = []
        for member_ in members:
            rows.append(
                self.doQuery("""SELECT AVG(attended), away FROM Attendees, Members
                    WHERE Attendees.memberID = Members.memberID
                    AND Members.name = ?
                    AND date LIKE ?;""",
                    vars = (member_, target_month)
                    )[0]
                )

        # handle no attendance data returned
        # which looks like [(None, None)...]
        if not list(filter(lambda row: row[0], rows)):
            raise ValueError("No attendance data returned from Attendees.")

        # convert away and avg. attendance to more readable forms
        averages = map( lambda row: int( round( row[0] *100, 0 ) ), rows )
        aways = ["Yes" if row[1] else "No" for row in rows]

        # convert the lists to a list of rows
        table_rows = [(name, average, away)
                      for name, average, away in zip(members, averages, aways)]

        # create a table
        return await mestils.create_table( table_rows, 
                                    f"table_at_{D.datetime.today().strftime('%H.%M.%S')}",
                                    col_labels = ["Name", "Attendance (%)", "Away (yes or no)"]
                                    )

    async def get_att_per_event(self) -> str:
        """Get this month's average attendance for each event type
        and save it as an image.

        RETURNS
            The path the the table image.
            
        RAISES
            ValueError: No attendance data returned from Attendees."""
        # get the target month for the LIKE clause
        target_month = D.datetime.today().strftime("%Y-%m-") + "%"

        # get the attendance per member and whether they were away
        rows = []
        event_types = ("AIR", "ARMOUR", "INFANTRY", "CO-OPS1", "CO-OPS2", "INTERNAL_OPS")
        for event in event_types:
            rows.append(
                self.doQuery("""SELECT AVG(attended), eventType FROM Attendees, Days
                    WHERE Days.date = Attendees.date
                    AND Days.eventType = ?
                    AND Attendees.date LIKE ?;""",
                    vars = (event, target_month)
                    )[0]
                )

        # handle no attendance data returned
        # which looks like [(None, None)...]
        if not list(filter(lambda row: row[0], rows)):
            raise ValueError("No attendance data returned from Attendees.")
        
        # convert no average for an event type to (event type, 0%) instead of (None, None)
        # and convert average from decimal to percentage
        table_rows: List[str, int] = [(event_type, 0) if row[0] is None 
                else ( row[1], int(round(row[0] * 100, 0)) )
                for event_type, row in zip(event_types, rows)]

        # create table
        return await mestils.create_table(table_rows, 
                                          f"table_at_{D.datetime.today().strftime('%H.%M.%S')}",
                                          ("Event Type", "Average Attendance (%)")
                                        )

    def get_member_att(self, name: str) -> Optional[str]:
        """Get the attendance % of a member.
        
        RETURNS
        None: they have attended no events
        'x%': x % of events were attended by the person"""
        # get the target month for the LIKE clause
        target_month = D.datetime.today().strftime("%Y-%m-") + "%"

        rows = self.doQuery("""SELECT AVG(attended) FROM Attendees, Members
                            WHERE Members.memberID = Attendees.memberID
                            AND Members.name = ?
                            AND Attendees.date LIKE ?;""",
                            vars = (name, target_month)
                        )

        # handle no attended events
        if not rows or not rows[0][0]:
            return None
        else:
            return f"{int(round(rows[0][0] * 100, 0))}%"

    def get_all_members(self) -> List[Tuple[int, str, bool, D.date]]:
        """Get the memberID, name, joinedAt of all registered members in the Members table."""
        rows = self.doQuery("SELECT memberID, name, away, joinedAt FROM Members;")
        return [ ( row[0], row[1], bool(row[2]), D.datetime.strptime(row[3], "%Y-%m-%d").date() ) 
                for row in rows ]

    def mark_away(self, name: str) -> bool:
        '''
        Mark the person as away in the Members table.
        
        RETURNS
        True: a member was found and modified.
        False: " "     "  not "  "   "
        '''
        # count the number of changes and use it to see if a member was hit
        changes_before = self.connection.total_changes
        self.doQuery("UPDATE Members SET away = 1 WHERE name = ?;", [name])
        return self.connection.total_changes > changes_before


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
        self.db = AttendanceDBWriter()
        common.load_bot(bot)

    @commands.Cog.listener()
    @commands.has_any_role(*common.leader_roles)
    @common.in_bot_channel()
    async def on_member_update(self, before: member, after: member):
        """Add new scouts to the Members table automatically"""
        # get the roles that were added
        new_role_names = [role_.name for role_ in after.roles if role_ not in before.roles]
        if "Scout" in new_role_names:
            # get their name
            name = memtils.NameParser(after.display_name).parse()

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
            in_outfit = memtils.get_in_outfit()

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
        name = memtils.NameParser(name).parse()
        
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
        name = memtils.NameParser(name).parse()
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
                    attendees.add(memtils.NameParser(name).parse())

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
        name = memtils.NameParser(name).parse()
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
        name = memtils.NameParser(ctx.author.display_name).parse()
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
            in_outfit = memtils.get_in_outfit(True)

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
        name = memtils.NameParser(name).parse()
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
        name = memtils.NameParser(name).parse()
        row = self.db.get_member_by_name(name)
        if row:
            await ctx.send(f'''{name} is marked as {"not" if not row[2] else ""} away in our archives, my lord.''')
        else:
            await ctx.send(f'''Our archives don't know of this "{name}", my lord.''')

def setup(bot):
    bot.add_cog(Attendance(bot))

if __name__ == "__main__":
    setup(commands.Bot("TEST"))
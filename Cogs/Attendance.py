"""The database interface."""

from discord import member
from discord.ext import commands
from typing import *
from BenUtils import db
import sqlite3 as sql, datetime as D
from Utils import common, memtils
from contextlib import suppress
from prettytable import PrettyTable
from asyncio import sleep as async_sleep

class AttendanceDBWriter(db.DBWriter):
    """Handles the attendance database and accessing it."""

    def __init__(self):
        db.DBWriter.__init__(self, "Attendance")

        # create the table if it doesn't exist
        self.create_tables()

        # show all registered members
        print("Registered members:")
        print(self.doQuery("SELECT name FROM Members;"), end = "\n\n")

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

    def get_member_by_name(self, name: str) -> Optional[Tuple[int, str, bool]]:
        """
        Get the row of a member by their name.

        RETURNS
        None: 
            No member was found.
        Tuple[memberID: int, name: str, away: bool]: 
            The member that was found.
            If multiple members were found, the first one will be returned.
        """
        # fetch the row(s)
        rows = self.doQuery(
            "SELECT memberID, name, away FROM Members WHERE name = ?;", 
            vars = [name])

        # check if nothing was found
        if not rows:
            return None
        else:
            # get the first member
            first_member = rows[0]
            # convert away to bool
            return first_member[:-1] + (bool (first_member[-1]), )

    def get_member_by_id(self, id: int) -> Optional[Tuple[int, str, bool]]:
        """
        Get the row of a member by their id.

        RETURNS
        None: 
            No member was found.
        Tuple[memberID: int, name: str, away: bool]: 
            The member that was found.
            If multiple members were found, the first one will be returned.
        """
        # fetch the row(s)
        rows = self.doQuery(
            "SELECT memberID, name, away FROM Members WHERE memberID = ?;", 
            [id])

        # check if nothing was found
        if not rows:
            return None
        else:
            # get the first member
            first_member = rows[0]
            # convert away to bool
            return first_member[:-1] + (bool (first_member[-1]), )

    def delete_member_by_name(self, name: str):
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
        members = self.doQuery("SELECT name FROM Members;")
        members = [row[0] for row in members]  # convert List[Tuple[str]] to List[str]

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

    def list_members(self) -> List[Tuple[int, str]]:
        """Get the memberID and name of all the registered members."""
        return self.doQuery("SELECT memberID, name FROM Members ORDER BY memberID ASC;")

    def get_att_per_member(self) -> PrettyTable:
        """Get this month's attendance.
        
        RETURNS
            A PrettyTable.
            NOTE: A title must be added to the table.
            
        RAISES
            ValueError: No attendance data returned from Attendees."""
        # get all members because executemany doesn't support SELECT
        members = [row[0] for row in self.doQuery("SELECT name FROM Members;")]

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
        averages = [row[0] * 100 for row in rows]
        aways = ["Yes" if row[1] else "No" for row in rows]

        # create and configure the table
        table = PrettyTable(["Name", "Attendance (%)", "Away (yes or no)"])
        # sort by attendance ascending
        table.sortby = "Attendance (%)"
        table.reversesort = True

        # convert to a table
        for name, average, away in zip(members, averages, aways):
            table.add_row( (name, average, away) )

        return table

    def get_att_per_event(self) -> PrettyTable:
        """Get the average attendance for each event type.

        RETURNS
            A PrettyTable.
            NOTE: A title must be added to the table.
            
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
        
        # convert no average for an event type to (0%, event type) instead of (None, None)
        # and convert average from decimal to percentage
        rows = [(0, event_type) if row[0] is None else (row[0] * 100, row[1])
                for event_type, row in zip(event_types, rows)]
        # create and configure the table
        table = PrettyTable(["Event Type", "Average Attendance (%)"])
        # sort by attendance ascending
        table.sortby = "Average Attendance (%)"
        #table.reversesort = True

        # convert to a table
        for average, event_type in rows:
            table.add_row( (event_type, average) )

        return table

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
    async def add_all_members(self, ctx):
        """Add all current members to the Members table."""
        # get all the outfit members
        in_outfit = []
        for person in common.server.members:
            # check if they have any of the member roles
            for role in common.member_roles:
                if memtils.check_roles(person, role):
                    in_outfit.append(memtils.NameParser(person.display_name).parse())
                    break  # prevent double-adding a person if they have multiple member roles

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
    async def add_member(self, ctx, name: str):
        """Register a member with their name."""
        self.db.add_member(name)
        await ctx.send(f"Welcome to the chapter, brother {name}!")

    @commands.command(aliases = ["RM"])
    @commands.has_any_role(*common.leader_roles)
    async def remove_member(self, ctx, name: str):
        """Unregister a member by their name."""
        self.db.delete_member_by_name(name)
        await ctx.send("Another brother lost to the warp...")

    @commands.command(aliases = ["RMI"])
    @commands.has_any_role(*common.leader_roles)
    async def remove_member_by_id(self, ctx, id: int):
        """Unregister a member by their id"""
        self.db.delete_member_by_id(id)
        await ctx.send("Another brother lost to the warp...")

    @commands.command(aliases = ["DATT"])
    @commands.has_any_role(*common.leader_roles)
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
            if i == 3:
                break
            else:
                await async_sleep(1800)

        # record the attendance
        self.db.record_att(attendees)
        return attendees

    @commands.command(aliases = ["LM"])
    @commands.has_any_role(*common.leader_roles)
    async def list_members(self, ctx):
        """List all of the registered members"""
        # create a PrettyTable
        table = PrettyTable(["ID", "Name"])
        for row in self.db.list_members():
            table.add_row(row)
        
        await ctx.send(f"They are ready to serve, my lord:```\n{table.get_string()}```")

    @commands.command(aliases = ["att"])
    @commands.has_any_role(*common.leader_roles)
    async def get_att(self, ctx):
        """Get the average attendance per member for this month."""
        try:
            await ctx.send(f"Here are the results for this month, my lord:```\n" +
                           f"{self.db.get_att_per_member().get_string()}```")
        # handle no attendance data
        except ValueError:
            await ctx.send("Our archives fail us... I cannot find any roll calls")

    @commands.command(aliases = ["Eatt"])
    @commands.has_any_role(*common.leader_roles)
    async def get_event_att(self, ctx):
        """Get the average attendance per event type for this month"""
        try:
            await ctx.send(f"These are the results for this month's events, my lord:```\n" + 
                           f"{self.db.get_att_per_event().get_string()}```")
        # handle no attendance data
        except ValueError:
            await ctx.send("Our archives fail us... I cannot find any roll calls")

    @commands.command(aliases = ["JA"])
    @commands.has_any_role(*common.leader_roles)
    async def joined_at(self, ctx, name: str):
        """Get the join date of a member by their name."""
        joined_at = self.db.get_join_date_by_name(name)
        # handle no member found
        if not joined_at:
            await ctx.send(f'Our archives do not know this "{name}"')
        else:
            await ctx.send(f"He joined our chapter on {joined_at.strftime('%d.%m')}")

    @commands.command(aliases = ["JAI"])
    @commands.has_any_role(*common.leader_roles)
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

def setup(bot):
    bot.add_cog(Attendance(bot))
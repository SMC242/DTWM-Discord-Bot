import calendar
import datetime
from typing import List
import prettytable
import discord
from discord.ext import commands, tasks
from DB import DBWriter
from checks import inBotChannel, isLeader


class Attendance(commands.Cog):
    """Attendance and player database handling."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._db = DBWriter('Attendance')

        self._createAttendanceTable()

        self.bot.loop.create_task(self.newDay())

    def _createAttendanceTable(self):
        """Build the attendance table."""

        self._db.cursor.executescript("""
CREATE TABLE IF NOT EXISTS Attendees(
    dayID INTEGER,
    memberID INTEGER,
    attended BOOL DEFAULT 0,
    FOREIGN KEY(memberID) REFERENCES members(memberID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY(dayID) REFERENCES Days(dayID) ON DELETE CASCADE ON UPDATE CASCADE);

CREATE TABLE IF NOT EXISTS Members(
    memberID INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    away BOOL DEFAULT 0);

CREATE TABLE IF NOT EXISTS Days(
    dayID INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT);""")

    async def _addMember(self, name: str):
        """Add a member to the database"""

        self._db.doQuery("INSERT INTO Members(name) VALUES(?)", vars=(name, ))

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Check if they were updated to Astartes and Scout, if so remove them from DB"""

        beforeRoles = [role_.name for role_ in before.roles]
        afterRoles = [role_.name for role_ in after.roles]
        difference = [
            role_ for role_ in afterRoles if role_ not in beforeRoles]

        if "Scout" in difference:
            # NOTE This is not ideal. Use the user ID instead if you can? It
            # won't change as often.
            personExists = self._db.doQuery(
                "SELECT name FROM Members WHERE name = ?", vars=(after.nick, ))

            if not personExists:
                await self._addMember(after.nick)

    async def _addAllMembers(self):
        """Add all current members to the DB"""
        serverMembers = self.bot.get_guild(545422040644190220).members
        members = [m for m in serverMembers if any(
            r.nick.lower() in ('astartes', 'watch leader') for r in m.roles)]

        # NOTE: Again, needs a better way of linking names
        filteredNames = [m.nick for m in members]

        # each element must be a tuple
        sqlReadyNames = [(name, ) for name in filteredNames]

        self._db.doQuery("INSERT INTO Members(name) VALUES(?)",
                         vars=sqlReadyNames, many=True)

    async def _deleteMember(self, name: str):
        """Delete a member from the database"""

        self._db.doQuery("DELETE FROM Members WHERE name = ?", vars=(name, ))

    async def _sendAttToDB(self, attendees: List[str]):
        """Send attendees to DB"""

        # prepare for query
        date = self.date().strftime("%d/%m/%Y")
        toInsert = [(date, name) for name in attendees]

        # mark as absent
        self._db.doQuery("""
INSERT INTO Attendees (dayID, memberID, attended) VALUES
    ((SELECT dayID FROM Days WHERE date = ?), (SELECT memberID FROM Members WHERE name = ?), 1);""",
                         vars=toInsert, many=True)

    async def _markAsAway(self, name: str):
        """Mark someone as away for the month"""

        self._db.doQuery(
            "UPDATE Members SET away = 1 WHERE name = ?", vars=(name, ))

    async def _getMonthlyAtt(self):
        """
        Output the month's attendance to #command-chat,
        and clear all away statuses at the end of the month
        """

        # check if it's the first day of the next month
        date = datetime.datetime.today().date()
        firstDayOfMonth = calendar.monthrange(date.year, date.month)[0]
        if not date == datetime.date(date.year, date.month, firstDayOfMonth):
            return  # we don't care unless it's the last day

        # get attendance for each member
        members = self._db.doQuery("SELECT name FROM Members;")
        month = date.strftime("%m")
        year = date.strftime("%Y")

        toInsert = [(name, month, year) for name in members]
        attPerMember = self._db.doQuery("""
SELECT AVG(attended) FROM Attendees, Members, Days
    WHERE
        Members.memberID = Attendees.memberID AND Members.name = ?
        AND Days.dayID = Attendees.dayID
        AND Days.date LIKE '%/?/?';""", vars=(toInsert, ))

        # get away statuses
        aways = self._db.doQuery(
            "SELECT away FROM Members where name = ?", vars=(members, ))

        # convert to readable forms
        aways = [("Yes") if (value == 1) else ("No") for value in aways]
        attPerMember = [int(value * 100) for value in attPerMember]

        # output to #command-chat
        # iterate over members and build output table
        output = f"__Attendance for {date.strftime('%m/%Y')}__"
        output += "\n```"

        for i in range(0, len(members)-1):
            output += f"| Name: {members[i]} | Attendance: {attPerMember[i]}% | Away during the month: {aways[i]} |"

        output += "```"

        # send message
        commandChat = self.bot.get_channel(545809020754067463)
        await commandChat.send(output)

        # remove away statuses
        self._db.doQuery("UPDATE Members SET away = 0;")

    async def newDay(self):
        """Add the current day to Days if not exists"""

        date = datetime.datetime.today().strftime("%d/%m/%Y")
        # if not exists check
        if not self._db.doQuery("SELECT date FROM Days WHERE date = ?", vars=(date, )):
            self._db.doQuery(
                "INSERT INTO Days (date) VALUES (?)", vars=(date, ))

    @staticmethod
    def date():
        """Get today's date in day/month/year format"""

        return datetime.datetime.today().date().strftime("%d/%m/%Y")

    def _removeMemberByID(self, id: int):
        """Unregister a member from the DB with their ID."""

        self._db.doQuery("DELETE FROM Members WHERE memberID = ?;", vars=(id,))

    def _listMembers(self):
        """Fetch all of the members from the DB and their IDs."""

        return self._db.doQuery("SELECT memberID, name FROM Members;")

    @commands.command()
    @inBotChannel()
    @isLeader()
    async def addMember(self, ctx, name: str):
        """Register the target member.

        Arguments: ab!leader addMember {name}
        name: Their player name.
        """
        await ctx.send("It will be done, My Lord.")
        async with ctx.typing():
            await self._addMember(name)
            return await ctx.send(f"Welcome to the chapter, brother {name}!")

    @commands.command()
    @inBotChannel()
    @isLeader()
    async def listMembers(self, ctx):
        """List all the members in the database as a table of id, name."""

        async with ctx.typing():
            # query DB for members and their IDs
            members: List[Tuple[int, str]] = self._listMembers()

            # build the output message
            table = prettytable.PrettyTable(["ID", "Name"])
            for member_ in members:
                table.add_row(member_)

            # send the message
            await ctx.send(f"They are ready to serve:\n```\n{table}```")

    @commands.command(aliases=['byID'])
    @inBotChannel()
    @isLeader()
    async def removeMemberByID(self, ctx, id: int):
        """Unregister a member from the database by their ID.

        Arguments: ab!leader removeMemberByID {id}
        id: Their id in the database.
        """
        async with ctx.typing():
            self._removeMemberByID(id)
            await ctx.send("Another brother lost to the Warp...")

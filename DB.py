"""Handles writing attendance to a sqlite3 database"""

from discord import *
from discord.ext import commands
import sqlite3 as sql
import os, logging, asyncio, datetime, calendar
from typing import *
from sys import exc_info

class DBWriter:
    """Handles the database connection and reading and writing to it."""

    # DECORATORS
    class Decorators:
        def retry(logMsg: str = None, retries: int = 5):
            """Try func for n retries."""

            def middle(func):
                def inner(*args, **kwargs):
                    # convert to function to allow exc_info to be the default
                    if not logMsg:
                        logMsgCallable = exc_info

                    else:
                        logMsgCallable = lambda : logMsg

                    log = logging.getLogger()

                    # try repeatedly
                    for try_ in range(0, retries):
                        try:
                            return func(*args, **kwargs)

                        except:
                            log.error(logMsgCallable())

                    # if retries exhausted
                    return log.error(f"Failed to execute {func}")
                return inner
            return middle


    def __init__(self, name: str):
        """Create DB connection"""

        self.path = ""
        self.connection = None

        self.createDB(name)
        self.createConnection()
        self.cursor = self.connection.cursor()
        # set up the foreign keys on each connection
        self.doQuery("PRAGMA foreign_keys = 1;")


    def createDB(self, name: str):
        """Create a directory and a DB if not exists. Return the path to self.path."""

        # get current directory
        currentDirectory = os.path.dirname(__file__)

        # create directory
        newPath = os.path.join(currentDirectory, "Databases")
        try:
            os.mkdir(newPath)

        except FileExistsError:
            pass

        #create file
        filePath = newPath + f"\{name}.db"
        try:
            with open(filePath):
                pass

        except FileNotFoundError:
            with open(filePath, "w+"):
                pass

        self.path = filePath


    @Decorators.retry(logMsg = "Failed to create connection.")
    def createConnection(self):
        """Create DB connection. Return connection object to self.connection"""

        self.connection = sql.connect(self.path)


    def doQuery(self, query: str, vars: tuple = (), many: bool = False) -> Any:
        """Do one or many queries to the connection"""

        if not many:
            self.cursor.execute(query, vars)

        else:
            self.cursor.executemany(query, vars)

        self.connection.commit()
        return self.cursor.fetchall()


    def _executeFromFile(self, path: str):
        """Execute all commands in a file located at path.
        This is a developer tool designed for creating test database."""

        with open(path) as f:
            scriptLines = f.read()

        self.cursor.executescript(scriptLines)
        self.connection.commit()


class AttendanceDBWriter(DBWriter, commands.Cog):
    """Handles writing attendance"""


    def __init__(self, bot: commands.Bot):
        DBWriter.__init__(self, "Attendance")

        self.bot = bot
        self.loop = asyncio.get_event_loop()

        self.createAttendanceTable()
        # print all registered members
        print("Registered members:")
        print(self.doQuery("SELECT * FROM Members;"), end = "\n\n")
        self.loop.create_task(self.newDay())


    def createAttendanceTable(self):
        """Build the attendance table."""

        self.cursor.executescript("""
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


    async def addMember(self, name: str):
        """Add a member to the database"""

        self.doQuery("INSERT INTO Members(name) VALUES(?)", vars = (name, ))


    @commands.Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        """Check if they were updated to Astartes and Scout, if so remove them from DB"""

        beforeRoles = [role_.name for role_ in before.roles]
        afterRoles = [role_.name for role_ in after.roles]
        difference = [role_ for role_ in afterRoles if role_ not in beforeRoles]

        if "Scout" in difference:
            # check if they're already in the database
            from Discord_Bot import removeTitles
            name = await removeTitles((after.nick, ))

            personExists = self.doQuery("SELECT name FROM Members WHERE name = ?", vars = (name, ))

            if not personExists:
                await self.addMember(name)


    async def addAllMembers(self):
        """Add all current members to the DB"""
        from Discord_Bot import removeTitles
        from Discord_Bot import checkRoles

        serverMembers = self.bot.get_guild(545422040644190220).members
        memberGenerator = await checkRoles(serverMembers, ("Astartes", "Watch Leader"))
        
        members = [person async for isMember, person in memberGenerator if isMember]
        filteredNames = await removeTitles([person.nick if person.nick else person.name for person in members])
        sqlReadyNames = [(name, ) for name in filteredNames]  # each element must be a tuple

        self.doQuery("INSERT INTO Members(name) VALUES(?)", vars = sqlReadyNames, many = True)


    async def deleteMember(self, name: str):
        """Delete a member from the database"""

        self.doQuery("DELETE FROM Members WHERE name = ?", vars = (name, ))


    async def sendAttToDB(self, attendees: List[str]):
        """Send attendees to DB"""

        # prepare for query
        date = self.date().strftime("%d/%m/%Y")
        toInsert = [(date, name) for name in attendees]

        # mark as absent
        self.doQuery("""
INSERT INTO Attendees (dayID, memberID, attended) VALUES
    ((SELECT dayID FROM Days WHERE date = ?), (SELECT memberID FROM Members WHERE name = ?), 1);""",
    vars = toInsert, many = True)


    async def markAsAway(self, name: str):
        """Mark someone as away for the month"""

        self.doQuery("UPDATE Members SET away = 1 WHERE name = ?", vars = (name, ))


    async def getMonthlyAtt(self):
        """
        Output the month's attendance to #command-chat,
        and clear all away statuses at the end of the month
        """

        # check if it's the first day of the next month
        date = datetime.datetime.today().date()
        firstDayOfMonth = calendar.monthrange(date.year, date.month)[0]
        if not date == datetime.date(date.year, date.month, firstDayOfMonth):
            return # we don't care unless it's the last day
        
        # get attendance for each member
        members = self.doQuery("SELECT name FROM Members;")
        month = date.strftime("%m")
        year = date.strftime("%Y")

        toInsert = [(name, month, year) for name in members]
        attPerMember = self.doQuery("""
SELECT AVG(attended) FROM Attendees, Members, Days 
    WHERE 
        Members.memberID = Attendees.memberID AND Members.name = ? 
        AND Days.dayID = Attendees.dayID
        AND Days.date LIKE '%/?/?';""", vars = (toInsert, ))

        # get away statuses
        aways = self.doQuery("SELECT away FROM Members where name = ?", vars = (members, ))
        
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
        self.doQuery("UPDATE Members SET away = 0;")


    async def newDay(self):
        """Add the current day to Days if not exists"""

        date = datetime.datetime.today().strftime("%d/%m/%Y")
        # if not exists check
        if not self.doQuery("SELECT date FROM Days WHERE date = ?", vars = (date, )):
            self.doQuery("INSERT INTO Days (date) VALUES (?)", vars = (date, ))


    @staticmethod
    def date():
        """Get today's date in day/month/year format"""

        return datetime.datetime.today().date().strftime("%d/%m/%Y")


    def removeMemberByID(self, id: int):
        """Unregister a member from the DB with their ID."""

        self.doQuery("DELETE FROM Members WHERE memberID = ?;", vars = (id,) )


    def listMembers(self):
        """Fetch all of the members from the DB and their IDs."""

        return self.doQuery("SELECT memberID, name FROM Members;")


if __name__ == "__main__":
    i = AttendanceDBWriter(commands.Bot("ab"))
"""The database interface."""

import discord
from discord.ext import commands
from typing import *
from .BenUtils import db
import sqlite3 as sql

class AttendanceDBWriter(db.DBWriter, commands.Cog):
    """Handles the attendance database and accessing it.
    
    NOTE: multi-inheritance is required as methods from DBWriter and Cog are needed."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        db.DBWriter.__init__(self, "Attendance", True)

        # create the table if it doesn't exist
        self.create_tables()

        # show all registered members
        print("Registered members:")
        print(self.doQuery("SELECT name FROM Members;"), end = "\n\n")

    def new_day(self):
        """Add a new day to the Days table"""
        self.doQuery(f"INSERT INTO Days(date) VALUES ((SELECT strftime('%d/%m/%Y', DATE('now'))));")

    def create_tables(self):
        """Create the tables if they're not already created."""
        self._executeFromFile("../Text Files/table_definitions.txt")

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
            "SELECT memberID, name, away FROM Members WHERE name = ?", 
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
            "SELECT memberID, name, away FROM Members WHERE memberID = ?", 
            vars = [id])

        # check if nothing was found
        if not rows:
            return None
        else:
            # get the first member
            first_member = rows[0]
            # convert away to bool
            return first_member[:-1] + (bool (first_member[-1]), )

    @commands.Cog.listener()
    async def on_member_update(self, before: member, after: member):
        """Add new scouts to the Members table automatically"""
        # get the roles that were added
        new_role_names = [role_.name for role_ in after.roles if role_ not in before.roles]
        if "Scout" in new_role_names:

"""The database interface for attendance."""

from typing import *
from BenUtils import db
import sqlite3 as sql, datetime as D
from contextlib import suppress
from .mestils import create_table

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

        # convert no attendance to 0%
        new_rows = [(r[0] if r[0] else 0, r[1]) for r in rows]

        # convert away and avg. attendance to more readable forms
        averages = map( lambda row: int( round( row[0] * 100, 0 ) ), new_rows )
        aways = ["Yes" if row[1] else "No" for row in new_rows]

        # convert the lists to a list of rows
        table_rows = [(name, average, away)
                      for name, average, away in zip(members, averages, aways)]

        # sort it by attendance %
        sorted_rows = sorted(table_rows, key = lambda row: row[1], reverse = True)

        # create a table
        return await create_table( sorted_rows, 
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

        # convert no attendance to 0%
        new_rows = [(r[0] if r[0] else 0, r[1]) for r in rows]
        
        # convert no average for an event type to (event type, 0%) instead of (None, None)
        # and convert average from decimal to percentage
        table_rows: List[str, int] = [(event_type, 0) if row[0] is None 
                else ( row[1], int(round(row[0] * 100, 0)) )
                for event_type, row in zip(event_types, rows)]

        # sort it by attendance %
        sorted_rows = sorted(table_rows, key = lambda row: row[1], reverse = True)

        # create table
        return await create_table(sorted_rows, 
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

    def unmark_away(self, name: str) -> bool:
        '''
        Mark the person as away in the Members table.
        
        RETURNS
        True: a member was found and modified.
        False: " "     "  not "  "   "
        '''
        # count the number of changes and use it to see if a member was hit
        changes_before = self.connection.total_changes
        self.doQuery("UPDATE Members SET away = 0 WHERE name = ?;", [name])
        return self.connection.total_changes > changes_before
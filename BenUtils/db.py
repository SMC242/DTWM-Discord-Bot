"""A class for handling databases."""

import sqlite3 as sql, os
from typing import Any, List

class DBWriter:
    """
    Handles the database connection and reading and writing to it.
    
    ATTRIBUTES
    path: str
        The path to the .db file.
    connection: sqlite3.Connection
        The connection obejct for path. 
        Used to commit queries.
    cursor: sqlite3.Cursor
        The cursor for connection.
        Used to execute queries.
    """

    def __init__(self, name: str, useRow: bool = False, use16Bit: bool = False):
        """Create sqlite3 Connection and Cursor to the database called `name`.
        If said DB doesn't exist, it'll be created at .../Databases/`name`.db
        
        name:
            The name describing what the database contains.
        useRow:
            Whether to output tuples that can be accessed like dicts (True),
            or to output tuples (False).
        use16Bit:
            Whether to use UTF-8 (False) or UTF-16 (True) encoding"""

        # these could be class attributes
        # but putting them here allows an instance
        # to be reset by re-instantiating it
        self.path = ""
        self.connection = None

        self.createDB(name)
        self.createConnection()
        self.cursor = self.connection.cursor()
        # set up the foreign keys on each connection
        # due to a limitation of sqlite requiring this for each connection
        self.doQuery("PRAGMA foreign_keys = 1;")

        # set encoding
        if use16Bit:
            self.doQuery("PRAGMA encoding = 'UTF-16';")

        else:
            self.doQuery("PRAGMA encoding = 'UTF-8';")

        # allow dict accessing of query results
        if useRow:
            self.cursor.row_factory = sql.Row


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


    def createConnection(self):
        """Create DB connection. Return connection object to self.connection"""

        self.connection = sql.connect(self.path)


    def doQuery(self, query: str, vars: tuple = (), many: bool = False) -> List[Any]:
        """Do one or many queries to the connection and commit the changes.
        Only use for safe queries or a mistake would be committed."""

        # NOTE
        # the changes will be committed no matter what
        # hence this method is not always good to use
        # it exists to cut down on cookie cutter lines for safe queries

        # sqlite3 handles escaping insertions
        if not many:
            self.cursor.execute(query, vars)

        else:
            self.cursor.executemany(query, vars)

        self.connection.commit()
        return self.cursor.fetchall()


    def _executeFromFile(self, path: str):
        """Execute all commands in a file located at path.
        This is a developer tool designed for creating test databases.
        This name should be mangled (add the __ prefix to name) when distributing.
        Make sure the file is secured, otherwise a user can edit it and inject their code."""

        with open(path) as f:
            scriptLines = f.read()

        self.cursor.executescript(scriptLines)
        self.connection.commit()


    def toggleRow(self, targetState: bool = None):
        """
        Either set toggle cursor.row_factory from
        Row to None/None to Row, or set it to the target state.
        
        targetState:
            True: row_factory = Row
            False: row_factory = None
        """
        
        # if a target was passed
        if targetState:
            self.cursor.row_factory = sql.Row

        elif targetState is False:  # I can't use falsy values since None is falsy
            self.cursor.row_factory = None

        # if no target was passed: toggle
        # if on: toggle off
        elif self.cursor.row_factory:
            self.cursor.row_factory = None

        else: # if not on: toggle on
            self.cursor.row_factory = sql.Row
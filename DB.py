"""Handles writing attendance to a sqlite3 database"""

import sqlite3 as sql
import os
import logging
from sys import exc_info
from typing import Any


class DBWriter:
    """Handles the database connection and reading and writing to it."""

    # DECORATORS
    class Decorators:
        @staticmethod
        def retry(logMsg: str = None, retries: int = 5):
            """Try func for n retries."""

            def middle(func):
                def inner(*args, **kwargs):
                    # convert to function to allow exc_info to be the default
                    if not logMsg:
                        logMsgCallable = exc_info

                    else:
                        def logMsgCallable(): return logMsg

                    log = logging.getLogger()

                    # try repeatedly
                    for _ in range(0, retries):
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

        # create file
        filePath = newPath + f'/{name}.db'
        try:
            with open(filePath):
                pass

        except FileNotFoundError:
            with open(filePath, "w+"):
                pass

        self.path = filePath

    @Decorators.retry(logMsg="Failed to create connection.")
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

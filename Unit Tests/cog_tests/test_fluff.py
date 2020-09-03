import unittest
from discord.ext import commands
from Cogs import Fluff
from testils import create_bot
from time import time
from datetime import datetime


class TestDTWMChanWorship(unittest.TestCase):

    def setUp(self):
        self.bot = create_bot("Fluff")
        self.cog = Fluff.DTWMChanWorship(self.bot)

    def test_chant_inner(self):
        """Check that the correct number of 'DTWM's are returned."""
        # test with a single chant
        dummy_time = datetime.now()
        self.cog.chants["1_test"] = [dummy_time]
        self.assertEqual(self.cog._chant_inner(), ["DTWM"])
        # test with > 1 message output
        self.cog.chants["401_test"] = [dummy_time] * 401
        self.assertEqual(self.cog._chant_inner(), [
            " ".join(["DTWM"] * 400),
            "DTWM"
        ])

    def test_chants_number(self):
        """Check that the total number of chants is counted correctly"""
        self.assertEqual(self.cog.chants_number, 0)
        self.cog.chants["chant_no_1"] = [datetime.now()]
        self.assertEqual(self.cog.chants_number, 1)
        self.cog.chants["chant_no_736"] = [datetime.now()] * 736
        self.assertEqual(self.cog.chants_number, 736)

    def test_leaderboard(self):
        """Check that the correct leaderboard has been created."""
        dummy_time = datetime.now()
        self.cog.chants = {
            "2": [dummy_time] * 4,
            "3": [dummy_time] * 3,
            "1": [dummy_time] * 7,
            "4": [dummy_time] * 2,
            "5": [],
        }
        self.assertEqual(self.cog.leaderboard, [
            ("1", 7),
            ("2", 4),
            ("3", 3),
            ("4", 2),
            ("5", 0),
        ])

    def test_count_person_chants(self):
        """Check that the number of chants for a person is counted correctly.
        Will not work until the 4th of each month."""
        now = datetime.now()
        self.cog.chants["count_test"] = [
            now,
            datetime.now(),
            datetime(now.year, now.month, now.day - 1),
            datetime(now.year, now.month, now.day - 2),
            datetime(now.year, now.month, now.day - 3),
        ]
        self.assertEqual(self.cog.count_person_chants(
            "count_test"), 5)  # check that no period works
        self.assertEqual(self.cog.count_person_chants(
            "count_test", 2), 4)  # check count within 2 days


if __name__ == '__main__':
    unittest.main()

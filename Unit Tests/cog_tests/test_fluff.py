import unittest
from discord.ext import commands
from discord import Activity, ActivityType, AllowedMentions
from Cogs import Fluff
from BaseTest import BaseTest
from testils import create_bot, create_ctx
from time import time
from datetime import datetime

class TestDTWMChanWorship(unittest.TestCase):

    def setUp(self):
        self.bot = create_bot()
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
        

if __name__ == '__main__':
    unittest.main()
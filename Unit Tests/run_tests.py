import importlib, os, discord
import main
from Utils import common
from discord.ext import commands
from BaseTest import BaseTest

# import all tests
tests = [importlib.import_module(file_name[:-3])
         for file_name in os.listdir()
         if file_name.endswith(".py")]

# create mock bot
bot = commands.Bot("mock!", 
                   activity = discord.Activity(
                       name = "Adepts running diagnostics...",
                       type = discord.ActivityType.playing,
                       ),
                    case_insensitive = True,
                    allowed_mentions = discord.AllowedMentions(everyone = False,
                                                               roles = False),
                    )

@bot.command()
async def f(ctx):
    print("entered")

@bot.listen()
async def on_ready():
    """Run all the tests with mock objects"""
    # create mock objects
    main.DEV_VERSION = False
    common.DEV_VERSION = False
    await common.wait_until_loaded(bot)
    i = BaseTest(bot)

    # run all the tests
    total_failures = 0
    for test in tests:
        #total_failures += test.run()
        pass

if __name__ == "__main__":
    with open("./Text Files/token.txt") as f:
        TOKEN = f.readline().strip()
    bot.run(TOKEN)
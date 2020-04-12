"""This modules handles any functions or variables that all modules will access."""

from discord import *
from discord.ext import commands
import unicodedata
from typing import *
from string import ascii_letters

bot = commands.Bot(None)  # temporarily defining the bot
bot_loaded = False  # flag for raising an error if the bot wasn't loaded already
# channels
bot_channel = None
server = None

async def load_bot(target_bot: commands.Bot):
    """
    Allow this module to use the Bot instance.
    The functions won't work and the variables will be None unless this has been called.

    This is due to needing access to the bot for some checks.
    """
    global bot, bot_channel, server

    # unlock all of the functions that need the bot
    bot = target_bot
    bot_loaded = True

    # set up common variables
    bot_channel = bot.get_channel(545818844036464670)
    server = bot.get_guild(545422040644190220)

def in_bot_channel() -> commands.check:
    """Check if the command was invoked in the bot channel."""
    async def inner(ctx):
        # require a bot instance
        if not bot_loaded:
            raise ValueError("This check requires a bot. Use load_bot to unlock it.")

        # check if the bot is in #servitors
        return ctx.channel == bot.get_channel()
    return commands.check(inner)

class NameParser:
    """
    Parse an input name. The following things are optionally checked:
        [TAG]s
        unicode characters,
        titles after a delimter.
    Call parse to get the parsed name with the checks applied.

    ATTRIBUTES
    check_tag: bool
        Whether to check for [TAG]s.
    check_english: bool
        Whether to check for non-English characters.
        Numbers are left in.
    remove_weird_chars: bool
        Whether to remove non-English characters 
        or to attempt to convert them to English characters.
        check_english must be True.
    check_titles: bool
        Whether to remove titles after a delimiter.
    check_numbers: bool
        Whether to remove numbers.
    case: Union[bool, None]
        Which case the name will be returned in.
        None = unchanged case
        True = uppercase
        False = lowercase.
    _original_name: str
        The name that was passed at instantiation.
    """

    def __init__(self, name: str, check_tag: bool = True,
        check_titles: bool = True, check_english: bool = True,
        remove_weird_chars: bool = False, check_numbers: bool = False,
        case: bool = None):
        """
        ARGUMENTS
        name:
            The name to parse when parse is called.
        check_tag:
            Whether to remove [TAG]s.
        check_titles:
            Whether to remove titles after a delimiter.
            Names are expected to be formatted in this way:
            {name} {delimiter} {title}
        check_english:
            Whether to check for non-english characters.
            What is done with those characters is defined
            by remove_weird_chars.
        remove_weird_chars:
            Whether to attempt to convert non-english characters
            or remove them.
        check_numbers:
            Whether to remove numbers.
        case: Union[bool, None]
            Which case the name will be returned in.
            None = unchanged case
            True = uppercase
            False = lowercase.
        """
        self._original_name = name
        self.check_tag = check_tag
        self.check_english = check_english
        self.remove_weird_chars = remove_weird_chars
        self.check_numbers = check_numbers
        self.case = case

    async def parse(self) -> str:
        """Return the parsed name. The name will be parsed according to the settings."""
        # don't modify the original
        name = self._original_name

        # list of settings and their methods
        settings = [
            (self.check_tag, self.remove_tag),
            (self.check_english, self.convert_to_english),
            (self.check_numbers, self.remove_numbers),
            ]

        # apply each setting if it's set
        for setting, method in settings:
            name = await method(name) if setting else name

        # convert the case
        if self.case is True:
            return name.upper()
        if self.case is False:
            return name.lower()
        else:
            return name

    async def remove_tag(self, name: str) -> str:
        """Remove [TAG]s from the name."""
        # exit if there is no tag
        if "]" in name:
            #linear search for end of outfit tag and set name to name after tag
            i=0
            while True: 
                # check if the end of the tag is at i
                if name[i] == "]":
                    # check for a space between the tag and the name
                    try:
                        if name[i+1]==" ":
                            i+=1
                        return name[i+1:]
                    # the tag is at the end of name
                    except IndexError:
                        return name
                # otherwise, continue
                else:
                    i+=1
        else:
            return name

    async def check_english(self, name: str) -> str:
        """Check for non-english characters. What happens to them
        is defined by remove_weird_chars."""
        if not self.remove_weird_chars:
            #try to save them - convert accents to latin letters
            name = unicodedata.normalize("NFKD", name)

        # remove any (surviving) non-ascii characters
        name = name.encode("ascii", "ignore")

        # remove symbols
        char_gen = (char for char in name if char.isalnum())  # filter out the symbols
        return "".join(char_gen)  # convert back to string

    async def remove_numbers(self, name: str) -> str:
        """Remove numbers from the name."""
        return "".join( (char for char in name if char in ascii_letters) )

    async def remove_titles(self, name: str) -> str:
        """Remove titles after a delimiter."""
        # get the valid delimiters
        with open("../Text Files/delimiters.txt") as f:
            delimiters = [line.strip("\n") for line in f.readlines()]

        # discard anything after the delimiter
        for delimiter in delimiters:
            name, *_ = name.split(delimiter)

        return name

if __name__ == "__main__":
    # test parser
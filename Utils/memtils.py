"""Common utils that relate to processing a member."""

from typing import *
import unicodedata
from discord import Member
from discord.ext.commands import Context
from Utils import common

class NameParser:
    """
    Parse an input name. The following things are optionally checked:
        [TAG]s
        unicode characters,
        numbers,
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
        self.check_titles = check_titles
        self.case = case

    async def parse(self) -> str:
        """Return the parsed name. The name will be parsed according to the settings."""
        # don't modify the original
        name = self._original_name

        # list of settings and their methods
        settings = [
            (self.check_tag, self.remove_tag),
            (self.check_titles, self.remove_titles),
            (self.check_english, self.convert_to_english),
            (self.check_numbers, self.remove_numbers),
            ]

        # apply each setting if it's set
        for setting, method in settings:
            name = method(name) if setting else name

        # remove extra whitespace
        name = name.strip()

        # convert the case
        if self.case is True:
            return name.upper()
        if self.case is False:
            return name.lower()
        else:
            return name

    def remove_tag(self, name: str) -> str:
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

    def convert_to_english(self, name: str) -> str:
        """Check for non-english characters. What happens to them
        is defined by remove_weird_chars."""
        if not self.remove_weird_chars:
            #try to save them - convert accents to latin letters
            name = unicodedata.normalize("NFKD", name)

        # remove any (surviving) non-ascii characters
        name = name.encode("ascii", "ignore")
        name = name.decode()  # convert bytes to string

        # remove symbols
        char_gen = (char for char in name if char.isalnum())  # filter out the symbols
        return "".join(char_gen)  # convert back to string

    def remove_numbers(self, name: str) -> str:
        """Remove numbers from the name."""
        return "".join( (char for char in name if char in ascii_letters) )

    def remove_titles(self, name: str) -> str:
        """Remove titles after a delimiter."""
        # get the valid delimiters
        with open("./Text Files/delimiters.txt") as f:
            delimiters = [line.strip("\n") for line in f.readlines()]

        # discard anything after the delimiter
        for delimiter in delimiters:
            name, *_ = name.split(delimiter)

        return name

def check_roles(person: Member, role_name: str) -> bool:
    """Check if the person has the role.
    Not case-sensitive"""
    return role_name.lower() in [role.name.lower() for role in person.roles]

async def get_in_outfit(return_members: bool = False) -> List[Union[Member, str]]:
    """Get all of the people in the outfit. Requires common.load_bot
    
    ARGUMENTS
    return_members: return Discord.Members instead of their names"""
    # throw an error if the bot hasn't been loaded
    if not common.bot_loaded:
        raise ValueError("You must use common.load_bot first")

    # get all the outfit members
    in_outfit = []
    for person in common.server.members:
        # check if they have any of the member roles
        for role in common.member_roles:
            if check_roles(person, role):
                # don't add battle brothers
                if check_roles(person, "Battle Brother"):
                    break
                else:
                    if return_members:
                        in_outfit.append(person)
                    else:
                        in_outfit.append(await NameParser(person.display_name).parse())
                    break  # prevent double-adding a person if they have multiple member roles

    return in_outfit

def get_title(person: Member) -> str:
    """Return 'my lord' if they're a leader, otherwise return 'brother'."""
    title = "brother"
    for role_ in common.leader_roles:
        if check_roles(person, role_):
            title = "my lord"

    return title

async def search_member(ctx: Context, name: str) -> Optional[Member]:
    """Search for the member in ctx's guild by their name."""
    # get the Members and their names
    # the names have to be lowered or the sort will be wrong
    name = name.lower()
    members = sorted( [( m, await NameParser(m.display_name, case = False).parse() )
                        for m in ctx.guild.members],
                            key = lambda m: m[1])
    # binary search through the names
    lower = 0
    upper = len(members)
    found_member = None

    while lower < upper:
        mid = (upper - lower) // 2
        current = members[mid]
        if current[1] < name:
            lower = mid + 1
        elif current[1] > name:
            upper = mid - 1
        else:  # found
            found_member = current[0]
            break

    return found_member
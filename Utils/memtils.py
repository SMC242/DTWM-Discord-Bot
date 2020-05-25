"""Common utils that relate to processing a member."""

from typing import *
import unicodedata
from discord import Member, Guild
from discord.ext.commands import Context
from Utils import common
from fuzzywuzzy import process, fuzz  # this module has a great name :D
from BenUtils.searching import binarySearch

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

    @property
    def parsed(self) -> str:
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
        if self.case is None:
            return name
        if self.case:
            return name.upper()
        else:
            return name.lower()

    def remove_tag(self, name: str) -> str:
        """Remove [TAG]s from the name."""
        # exit if there is no tag
        # credit to Auroram for the high-level refactor
        if "]" in name:
            tag_index = name.index("]")
            name = name[tag_index + 1:]
        return name.strip()  # remove extra spaces

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

def check_roles(person: Member, role_name: Union[Iterable[str], str]) -> bool:
    """Check if the person has the role(s).
    Not case-sensitive"""
    role_names = [role.name.lower() for role in person.roles]
    if isinstance(role_name, str):
        return role_name.lower() in role_names
    # check if any of the target roles are in their roles
    else:
        targets = [name.lower() for name in role_name]
        return bool(set(role_names).intersection(set(targets)))

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
        if check_roles(person, common.member_roles):
            # don't add battle brothers
            if check_roles(person, "Battle Brother"):
                    continue
            else:
                if return_members:
                    in_outfit.append(person)
                else:
                    in_outfit.append(NameParser(person.display_name).parsed)

    return in_outfit

def get_title(person: Member) -> str:
    """Return 'my lord' if they're a leader, otherwise return 'brother'."""
    title = "brother"
    for role_ in common.leader_roles:
        if check_roles(person, role_):
            title = "my lord"

    return title

def search_member(search_with: Union[Context, Guild],
                        name: str) -> Optional[Member]:
    """Search for the member using search_with's members by their name.
    
    ARGUMENTS
    search_with:
        The object to get the server members from.
        Using a Context object is preferable as
        it makes the bot more flexible.
    name:
        The un-parsed name of the person to find.
        
    RETURNS
    None: no member was found.
    Member: the instance of the person found."""
    # get the guild if a Context object was passed
    if isinstance(search_with, Context):
        search_with = search_with.guild

    # get the Members and their names
    # the names have to be lowered or the sort will be wrong
    name = NameParser(name, case = False).parsed
    members = sorted([( m, NameParser(m.display_name, case = False).parsed)
                      for m in search_with.members],
                     key = lambda m: m[1])

    # binary search through the names
    return binarySearch(name, members,
                        return_type = "item",
                        key = lambda m: m[1])

async def is_member(name: str, outfit_members: List[str] = None,
                    db: 'AttendanceDB.AttendanceDBWriter' = None,
                    min_ratio: int = 85) -> bool:
    """Check if the person is a member of the outfit.
    Not case-sensitive and uses a fuzzy ratio.
    
    ARGUEMENTS
    name:
        The name of the person to check against the outfit.
    outfit_members:
        The names of the people in the outfit.
        Defaults to people with the member roles in our discord.
        This should be passed if you need to check against the DB members.
    db:
        The DB interface to use to populate outfit_members
        if outfit_members wasn't passed.
    min_ratio:
        Change this to increase/decrease sensitivity to differences
        between the name and the best match from the outfit.
    """
    # handle an empty list
    if len(outfit_members) == 0:  return False

    # parsed the name and lower it
    parsed_name = NameParser(name, case = False).parsed

    # get the names of the members from the discord or db if they weren't provided
    if not outfit_members:
        if db:
            outfit_members = [row[1] for row in db.get_all_members()]
        else:
            outfit_members = await get_in_outfit()
    member_names = [n.lower() for n in outfit_members]

    # do a fuzzy comparison
    return process.extractOne(parsed_name, member_names)[1] >= min_ratio

def compare_name(name1: str, name2: Union[str, List[str]], 
                       min_ratio: int = 85) -> bool:
    """Use fuzzywuzzy to compare the parsed names.
    
    ARGUMENTS
        name1:
            The name to compare to the other name(s)
        name2:
            The name(s) to comare name1 against.
        min_ratio:
            The percentage of characters that must be the same
            between name1 and name2."""
    # parse name1
    name1 = NameParser(name1).parsed

    # handle name2 = string
    if isinstance(name2, str):
        return fuzz.ratio(name1, name2) >= min_ratio
    # handle name2 = list
    else:
        return process.extractOne(name1, name2)[1] >= min_ratio
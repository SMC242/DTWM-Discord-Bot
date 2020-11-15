"""Utils relating to sending or parsing messages."""

from typing import *
from discord.abc import Messageable
from matplotlib import pyplot, transforms
from asyncio import sleep as async_sleep
import re
import datetime as D
from random import randint

# pre-compile the regexs
REGEX = {
    "instagram": re.compile(r"https:\/\/www\.instagram\.com\/p\/[a-zA-Z-_0-9]*"),
    "timezone": re.compile(r"(CET|CEST)", re.IGNORECASE),
    # source for the below RegEx: https://stackoverflow.com/a/8234912/12399357
    "get_links": re.compile(r"(?P<full_link>(?P<protocol_domain>(?P<Protocol>[A-Za-z]{3,9}:(?:\/\/)?)(?:[-;:&=\+\$,\w]+@)?[A-Za-z0-9.-]+|(?:www.|[-;:&=\+\$,\w]+@)[A-Za-z0-9.-]+)(?P<path>(?:\/[\+~%\/.\w\-_]*)?\??(?:[-\+=&;%@.\w_]*)#?(?:[\w]*))?)")
}


def create_table(cell_contents: Iterable[Iterable[Any]], file_name: str = None,
                 col_labels: List[str] = None, row_labels: List[str] = None) -> str:
    """Create a table and save it as an image.

    ARGUMENTS
    cell_contents:
        The content to populate the rows with.
        Each element in cell_contents represents a row.
        Each element in cell_contents[n] represents a cell.
    col_labels:
        The labels for the columns.
    row_labels:
        "   "      "   "   rows.
    file_name:
        The name of the file. It will be saved as a png file.
        The file will be saved in DTWM-Discord-Bot/Images.
        Defaults to "table_at_{D.datetime.today().strftime('%H.%M.%S')}"
    RETURNS
        The file path of the table image."""
    # create table
    table = pyplot.table(
        cellText=cell_contents, rowLabels=row_labels,
        colLabels=col_labels, loc="center"
    )

    # remove all the background stuff
    pyplot.axis("off")
    pyplot.grid("off")

    # draw the canvas and get the current boundary box's coordinates
    figure = pyplot.gcf()
    figure.dpi = 200
    figure.canvas.draw()
    points = table.get_window_extent(figure._cachedRenderer).get_points()

    # add some padding
    points[0, :] -= 10
    points[1, :] += 10

    # create a boundary box that's cropped to fit the table
    new_boundary_box = transforms.Bbox.from_extents(
        points / figure.dpi)  # 200 DPI

    # save the table
    if not file_name:
        file_name = f"table_at_{D.datetime.today().strftime('%H.%M.%S')}"
    # the extra line is needed so that the path can be returned
    path = f"./Images/{file_name}.png"
    pyplot.savefig(path, bbox_inches=new_boundary_box)

    # clean up the figure so that the table is properly forgotten
    pyplot.clf()
    pyplot.cla()
    pyplot.close()
    return path


def list_join(to_join: Iterable[str], connective: str = "and") -> str:
    """
    Join a list into a grammatically-correct string.
    ARGUMENTS
    to_join:
        The items to join together.
    connective:
        The connective to join the last two elements.
        Example where 'and' is connective:
        'one, two, three, four and five'
    """
    # ensure it's a list
    if not isinstance(to_join, list):
        to_join = list(to_join)
    return ', '.join(to_join[:-2] + [f' {connective} '.join(to_join[-2:])])


def search_word(contents: str, target_word: str) -> bool:
    """Return whether the target_word was found in contents.
    Not case-sensitive."""
    # provide a TypeError instead of an AttributeError if a string isn't passed
    if not isinstance(target_word, str) or not isinstance(contents, str):
        raise TypeError("Strings are required.")

    return (re.compile(r'\b({0})\b'.format(target_word.lower()), flags=re.IGNORECASE).search(
        contents.lower())) is not None


def get_eu_timezone(contents: str) -> List[Optional[str]]:
    """
    ### (method) get_eu_timezone(contents, )
    Get 'CET'/'CEST' if mentioned in `contents`. Not case sensitive.

    ### Parameters
        - `contents`: `str`
            The text to search within

    ### Returns
        `List[Optional[str]]`:
            The timezone found, if any.
    """
    return re.findall(REGEX["timezone"], contents)


def get_instagram_links(msg: str) -> List[Optional[str]]:
    """Uses regex to extract Instagram links.

    RETURNS
    List[]: no links
    List[str]: some links found"""
    return re.findall(REGEX["instagram"],
                      msg)


def is_private(instagram_link: str) -> bool:
    """Check whether the link from Instagram is private.
    The igshid argument will be parsed out of the link.

    This uses the lenght of the link to guess if it's private.
    It seems to be accurate.

    Args:
        instagram_link (str): The link to check.

    Returns:
        bool: Whether it is private.

    Raises:
        ValueError: The link is not from Instagram.
    """
    if "instagram" not in instagram_link:
        raise ValueError("Not an Instagram link")
    # remove igshid
    try:
        igshid_index = instagram_link.index("?igshid")
        parsed_link = instagram_link[:igshid_index]
    except:
        parsed_link = instagram_link
    finally:
        # https://www.instagram.com/p/ is 28 characters
        post_id = parsed_link[28:]
        parsed_post_id = post_id.strip("/")  # remove the trailing /
    # non-private links have 11 characters after the domain
    return len(parsed_post_id) > 11


def chunk_message(msg: str, code_block: bool = False, character_cap: int = 2000) -> List[str]:
    """
    # (method) chunk_message(msg, code_block = False, CHARACTER_CAP = 2000, )
    Split the input string into chunks of 2k characters or less.

    # Parameters
        - `msg`: `str`
            The text to send
        - `code_block`: `bool`
            Whether it should be marked as a code block.
            Defaults to `False`.
        - `character_cap`: `int`
            The maximum characters per message.
            Defaults to `2000`.

    # Raises
        - ValueError: An empty string was passed

    # Returns
        `List[str]`:
            The chunks
    """
    # avoid an empty message
    if not msg:
        raise ValueError("Cannot chunk an empty string")
    if code_block:  # code blocks require 7 characters
        character_cap -= 7
    # split the message into chunks that can be sent
    if len(msg) > character_cap:
        return [f"```\n{msg[chunk_num: chunk_num + character_cap]}```"  # create code block for each message
                if code_block else msg[chunk_num: chunk_num + character_cap]
                for chunk_num in range(0, len(msg), character_cap)]
    else:
        # add code formatting
        code_block_str = "```\n" if code_block else ""
        return [f"{code_block_str}{msg}{code_block_str[:-1]}"]


async def send_as_chunks(msg: Union[str, List[str]], target: Messageable,
                         delay: float = 1, code_block: bool = False,
                         character_cap: int = 2000,
                         **send_kwargs):
    """Wrapper for chunk_messages that also sends the messages
    at a rate of 1/sec

    ARGUMENTS
    msg: the message to chunk and send.
        You may pass in an already chunked message.
    target: any channel, User, or Context to send the messages to.
    delay: the delay between messages.
    code_block: whether to format the messages as code blocks.
    **send_kwargs: any kwargs for Messageable.send()
    """
    # chunk the message if it hasn't been chunked
    if isinstance(msg, str):
        msgs = chunk_message(msg, code_block, character_cap)
    else:
        msgs = msg
    # send the messages
    for msg in msgs:
        await target.send(msg, **send_kwargs)
        await async_sleep(delay)


def get_links(msg: str) -> Optional[List[str]]:
    """Use regex to extract any links from the message.
    NOTE: the regex will match anything after '/' until a new line or space is reached"""
    # credit to Auroram for this expression
    matches = re.findall(REGEX["get_links"],
                         msg)
    # NOTE matches is in this format:
    #     [
    #         (protocol, domain, anything after until whitespace or `\n`),
    #     ]
    # convert matches to List[str]
    # return ["".join(row) for row in matches]
    return [row[0] for row in matches]


def shuffle(target: List[Any]) -> List[Any]:
    """
    ### (method) shuffle(target, )
    Mix up the elements of `target`

    ### Parameters
        - `target`: `List[Any]`
            The list to mix up

    ### Returns
        `List[Any]`:
            The shuffled list
    """
    limit = len(target) - 1
    output: List[Any] = [None] * (limit + 1)

    def generate_index():
        index = randint(0, limit)
        return index if output[index] is None else generate_index()

    for ele in target:
        # get an index that hasn't been used yet
        output[generate_index()] = ele
    return output

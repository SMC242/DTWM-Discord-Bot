"""Utils relating to sending or parsing messages."""

from typing import *
from discord.abc import Messageable
from matplotlib import pyplot, transforms
from asyncio import sleep as async_sleep
import os
import re
import datetime as D


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


def get_instagram_links(msg: str) -> List[Optional[str]]:
    """Uses regex to extract Instagram links.

    RETURNS
    List[]: no links
    List[str]: some links found"""
    return re.findall(r"https:\/\/www\.instagram\.com\/p\/\w*|[-]",
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


def chunk_message(msg: str, code_block: bool = False) -> List[str]:
    """Split the input string into chunks of 2k characters or less."""
    # avoid an empty message
    if not msg:
        raise ValueError("Cannot chunk an empty string")
    CHARACTER_CAP = 2000
    if code_block:  # code blocks require 7 characters
        CHARACTER_CAP -= 7
    # split the message into chunks that can be sent
    if len(msg) > CHARACTER_CAP:
        return [f"```\n{msg[chunk_num: chunk_num + CHARACTER_CAP]}```"  # create code block for each message
                if code_block else msg[chunk_num: chunk_num + CHARACTER_CAP]
                for chunk_num in range(0, len(msg), CHARACTER_CAP)]
    else:
        return [msg]


async def send_as_chunks(msg: Union[str, List[str]], target: Messageable,
                         delay: float = 1, code_block: bool = False,
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
        msgs = chunk_message(msg, code_block)
    else:
        msgs = msg
    # send the messages
    for msg in msgs:
        await target.send(msg, **send_kwargs)
        async_sleep(delay)

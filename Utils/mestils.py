"""Utils relating to sending or parsing messages."""

from typing import *
from discord.abc import Messageable
from matplotlib import pyplot, transforms
from asyncio import sleep as async_sleep
import os, re, datetime as D

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
        cellText = cell_contents, rowLabels = row_labels,
        colLabels = col_labels, loc ="center"
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
    points[0,:] -= 10
    points[1,:] += 10

    # create a boundary box that's cropped to fit the table
    new_boundary_box =  transforms.Bbox.from_extents(points / figure.dpi)  # 200 DPI

    # save the table
    if not file_name:
        file_name = f"table_at_{D.datetime.today().strftime('%H.%M.%S')}"
    path = f"./Images/{file_name}.png"  # the extra line is needed so that the path can be returned
    pyplot.savefig(path, bbox_inches = new_boundary_box)

    # clean up the figure so that the table is properly forgotten
    pyplot.clf()
    pyplot.cla()
    pyplot.close()
    return path

def list_join(to_join: List[str], connective: str = "and") -> str:
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
    return ', '.join(to_join[:-2] + [f' {connective} '.join(to_join[-2:])])

def search_word(contents: str, target_word: str) -> bool:
    """Return whether the target_word was found in contents.
    Not case-sensitive."""
    return (re.compile(r'\b({0})\b'.format( target_word.lower() ), flags=re.IGNORECASE).search(
        contents.lower() )) is not None

def get_instagram_links(msg: str) -> List[Optional[str]]:
    """Uses regex to extract Instagram links.

    RETURNS
    List[]: no links
    List[str]: some links found"""
    return re.findall("https:\/\/www\.instagram\.com\/p\/\w*|[-]",
                     msg)

def chunk_message(msg: str) -> Tuple[str]:
    """Split the input string into chunks of 2k characters or less."""
    # create the DTWM chant and split it into chunks that can be sent
    CHARACTER_CAP = 2000
    if len(msg) > CHARACTER_CAP:
        return [msg[chunk_num: chunk_num + CHARACTER_CAP]
                for chunk_num in range(0, len(msg), CHARACTER_CAP)]
    else:
        return [msg]

async def send_as_chunks(msg: str, target: Messageable,
                         delay: float = 1, **send_kwargs):
    """Wrapper for chunk_messages that also sends the messages
    at a rate of 1/sec
    
    ARGUMENTS
    msg: the message to chunk and send.
    target: any channel, User, or Context to send the messages to.
    delay: the delay between messages.
    **send_kwargs: any kwargs for Messageable.send()
    """
    msgs = chunk_message(msg)
    for msg in msgs:
        await target.send(msg)
        async_sleep(delay, **send_kwargs)

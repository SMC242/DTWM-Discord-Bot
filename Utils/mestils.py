"""Utils relating to sending or parsing messages."""

from typing import *
from matplotlib import pyplot, transforms
import os

# TODO: create a Messagable.send wrapper that chops large messages down into smaller messages

async def create_table(cell_contents: Iterable[Iterable[Any]], file_name: str,
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
    figure.canvas.draw()
    points = table.get_window_extent(figure._cachedRenderer).get_points()

    # add some padding
    points[0,:] -= 10
    points[1,:] += 10

    # create a boundary box that's cropped to fit the table
    new_boundary_box =  transforms.Bbox.from_extents(points / figure.dpi)

    # save the table
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
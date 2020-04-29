"""Utils relating to sending or parsing messages."""

from discord import *
from typing import *
from discord.ext import commands
from math import ceil
from re import finditer

async def send_message(channel: TextChannel, content: str):
    """Send a message to the target channel. 

    If the content exceeds 2k characters, it will be sent as multiple messages
    without splitting up words.
    
    Mantains code snippets."""
    # check the character count
    length = len(content)
    if len(content) < 2000:
        return await channel.send(content)

    # find how many messages are needed
    # always round up or else the character limit will be hit
    portions = ceil(length / 2000)

    # check for code blocks being near the boundaries
    for boundary in range(2000, (2000 * portions), 2000):
        # find any code blocks within the boundary
        [match.start() for match in re.finditer("```", content[boundary - 2000: boundary])]
        

    # for each boundary, backtrack until a space is found
    # set that to the message and 
    # overflow the backtracked chars into the next message
    # a 20 character tolerance is added to each message for shifting
    # to avoid splitting words
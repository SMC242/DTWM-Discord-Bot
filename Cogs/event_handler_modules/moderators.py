from Utils.caching import download_resource, AsyncCache
from discord.message import Attachment
from Utils import mestils
from json import dumps
from discord.ext import commands, tasks
from discord import Message, Member, HTTPException, NotFound, File, Embed, Attachment
from typing import Optional, List, Dict, Set, Union, Iterable
import datetime as D


class MessageAuthoritarian(commands.Cog):
    """Base class for deleting messages if they meet a condition."""
    last_msg: str = None  # the last deleted message

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    async def _get_urls(msg: Message) -> Set[str]:
        """Get all of the unique urls from a message"""
        urls = set()
        if msg.attachments:
            urls.update((attachment.url for attachment in msg.attachments
                         if "unknown" not in attachment.url))  # ignore anonymous uploads
        if msg.embeds:
            for embed in msg.embeds:
                to_add = filter(lambda attr: attr != Embed.Empty,  # remove empty attrs
                                (embed.url, embed.video.url, embed.image.url))
                urls.update(list(to_add))
        # try to get links from the content
        raw_links = mestils.get_links(msg.content)
        urls.update(raw_links)
        return urls

    async def on_message(self, msg: Message):
        """Do your check here. This must be deccorated with commands.Cog.listener()
        See the source for an example."""
        # don't respond to the bot
        if self.bot.user == msg.author:
            return

        raise NotImplementedError()

        # example
        if "ayaya" in msg.contents:
            await msg.channel.send(">={", delete_after=20)
            self.bot.get_cog("AuthoritarianBabySitter").last_msg = msg
            await msg.delete(delay=2)


class AuthoritarianBabySitter(commands.Cog):
    """Holds the resummon_message command to avoid double-registering it."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.disabled: bool = False
        self.last_msg: Message = None

    @commands.command(aliases=["RS", "resummon", "come_back", "false_positive"
                               "false_hit", "resummon_msg"])
    async def resummon_message(self, ctx):
        """Repost the last deleted message."""
        # avoid no message deleted
        if self.last_msg is None:
            return await ctx.send("I have not deleted anything today, my lord.")

        # avoid an empty message and allow adding error messages
        to_send = self.last_msg.content or "`[placeholder]`"

        # attempt to retrieve the attachments
        urls = list((await MessageAuthoritarian._get_urls(self.last_msg)))

        # chunk the message into sets of 5 (only 5 links will embed per message)
        await mestils.send_as_chunks(urls, self.last_msg.channel, character_cap=5)

    @commands.command()
    async def toggle_auto_mods(self, ctx):
        """Enable or disable the auto moderators."""
        self.disabled = not self.disabled
        auto_mod_status = "disabled" if self.disabled else "enabled"
        await ctx.send(f"I have {auto_mod_status} the auto-moderators")


class InstagramHandler(MessageAuthoritarian):
    """Responds to Instagam links"""

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        """Warns the user if they post a private Instagram link."""
        # don't respond to the bot
        if self.bot.user == msg.author:
            return

        # check if there was an Instagram link
        links = mestils.get_instagram_links(msg.content)

        # parse links
        # private links have a longer id whereas public
        # ones have a fixed size of 11
        for link in links:
            if mestils.is_private(link):
                await msg.channel.send("That link was private, brother. I will remove it " + "<:s_40k_adeptus_mechanicus_shocked:585598378721673226>", delete_after=20)
                # cache the message in case of a false-positive
                self.bot.get_cog("AuthoritarianBabySitter").last_msg = msg
                await msg.delete(delay=2)


class RepostHandler(MessageAuthoritarian):
    """Deletes reposted links.

    ATTRIBUTES:
        hashes: format: {the first KB of a file hashed | a URL : timestamp}"""

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        # all of the hashed images from the past 48 hours
        self.hashes: AsyncCache = AsyncCache(max_items=256,  # the hashes are 32 bytes so it's 8KB at max
                                             on_add_pass=lambda x, y, z: print(
                                                 f"Added Key {y} Value {z}"),
                                             on_add_fail=lambda x, y, z: print(
                                                 f"Failed to add Key {y} Value {z}"),
                                             on_remove=lambda x, y, z: print(
                                                 f"Removed Key {y} Value {z}")
                                             )

    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        """Check for duplicate images."""
        # don't respond to self
        if msg.author == self.bot.user:
            return

        # get the urls of all media in the message
        urls = await self._get_urls(msg)

        # download all media
        LIMIT = 1024  # 1024 bytes = 1 KB
        for url in urls:
            async with download_resource(url, LIMIT) as file:
                bytes = await file.content
            await self._check_duplicate(msg, hash(bytes))

    async def _check_duplicate(self, msg: Message, hash: str):
        """Check if the hash is already in self.hashes. If so, delete the message.
        Otherwise: cache the hash."""
        if hash in self.hashes:
            # the link has been saved, so delete the message
            await msg.channel.send("}=< No repostium in this discordium >={",
                                   delete_after=20)
            self.bot.get_cog("AuthoritarianBabySitter").last_msg = msg
            await msg.delete(delay=2)
        else:  # save the link
            self.hashes[hash] = D.datetime.now()

    @ commands.command(aliases=["SCa"])
    @ commands.is_owner()
    async def show_cache(self, ctx):
        """Output all hashes that have been cached. Debugging tool."""
        await mestils.send_as_chunks(
            dumps(self.hashes, indent=4, default=str),
            ctx, code_block=True)


def setup(bot: commands.Bot):
    """Load RepostHandler, InstagramHandler, and AuthoritarianBabySitter

    Args:
        bot (commands.Bot): the bot to load these Cogs to.
    """
    cogs = (
        AuthoritarianBabySitter,
        RepostHandler,
        InstagramHandler,
    )

    for cog in cogs:
        bot.add_cog(cog(bot))

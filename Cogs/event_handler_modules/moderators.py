from Utils.caching import download_resource, AsyncCache
from discord.message import Attachment
from Utils import mestils
from json import dumps
from discord.ext import commands, tasks
from discord import Message, Member, HTTPException, NotFound, File, Embed, Attachment
from typing import Optional, List, Dict, Set, Union, Iterable, Any, Tuple
import datetime as D
from asyncio import get_event_loop, sleep as async_sleep


class StoredMsg:
    """This class will cache a message for a while so that it can be resummoned."""

    def __init__(self, msg: Message, cache_period: float = 60) -> None:
        self.msg = msg
        self.cache_period = cache_period
        self.content: Optional[str] = ""
        self.attachments: Optional[List[bytes]] = []
        self.embed_links: Optional[List[str]] = []
        self._parsed = False
        self.expired = False

        loop = get_event_loop()
        loop.create_task(self.parse_msg())
        loop.create_task(self.cache_msg())

    async def parse_msg(self):
        """
        # (method) parse_msg()
        Get all of the interesting attributes of the message.
        """
        def parse_attrs(embed: Embed) -> Tuple[str, ]:
            """Get all of the non-empty attributes of an embed."""
            def is_empty(embed_attr: Any) -> bool:
                return embed_attr == Embed.Empty

            def attrs_from_embed(embed: Embed) -> Tuple[str, str, str, str]:
                return (embed.url, embed.image.url, embed.video.url)

            return (attr for attr in attrs_from_embed(embed) if not is_empty(attr))

        self.embed_links = [
            attr for e in self.embeds
            for attr in parse_attrs(e)]
        self.content = self.msg.content or "`[placeholder]`"
        self.attachments = [await a.read(use_cached=True) for a in self.msg.attachments]
        self._parsed = True

    async def cache_msg(self):
        """
        # (method) cache_msg()
        Cache the mssage for `self.cache_period` seconds.
        """
        await async_sleep(self.cache_period)
        self._expired = True
        self.release()

    def release(self):
        """Clear all of the attributes."""
        self.content = None
        self.attachments = []
        self.embeds = []

    @property
    def expired(self) -> bool:
        """Check if this object has been uncached."""
        return self._expired

    @property
    def parsed(self) -> bool:
        """Check if this object's message has been parsed."""
        return self._parsed

    def retrieve(self) -> Optional[dict]:
        """
        # (method) retrieve()
        Retrieve all of the message attributes as a dictionary

        # Returns
            `Optional[dict]`:
                The message attributes with the following keys:
                - `content`: the text of the message
                - `embed_links`: `List[str]`
                - `files`: `List[File]`
                Returns `None` if expired.
        """
        if self.expired:
            return None
        files: List[File] = [File(a) for a in self.attachments]
        return {
            "content": self.content,
            "embed_links": self.embed_links,
            "files": files,
        }


class MessageAuthoritarian(commands.Cog):
    """Base class for deleting messages if they meet a condition."""
    last_msg: str = None  # the last deleted message

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.babysitter = self.bot.get_cog("AuthoritarianBabySitter")

    @ staticmethod
    async def _get_urls(msg: Message) -> Set[str]:
        """Get all of the unique urls from a message"""
        urls = set()
        if msg.attachments:
            urls.update((attachment.url for attachment in msg.attachments))
        if msg.embeds:
            for embed in msg.embeds:
                to_add = filter(lambda attr: attr != Embed.Empty,  # remove empty attrs
                                (embed.video.url, embed.image.url))
                urls.update(to_add)
        return urls

    @ staticmethod
    async def _get_msg_links(msg: Message) -> Set[str]:
        """Get the links in the message from the text.
        NOTE: this is a separate method from `_get_urls` because I don't want to download
        things like articles."""
        def is_emote(url: str) -> bool:
            url_index = content.index(url)
            left = content[url_index - 1]
            right = content[url_index + len(url)]
            return left == ":" and right == ">"

        # try to get links from the content
        content = msg.content
        urls = set(mestils.get_links(content))
        # don't hit on emotes
        non_emotes = set((url for url in urls if not is_emote(url)))
        return non_emotes

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

    @ commands.command(aliases=["RS", "resummon", "come_back", "false_positive"
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

    @ commands.command()
    async def toggle_auto_mods(self, ctx):
        """Enable or disable the auto moderators."""
        self.disabled = not self.disabled
        auto_mod_status = "disabled" if self.disabled else "enabled"
        await ctx.send(f"I have {auto_mod_status} the auto-moderators")


class InstagramHandler(MessageAuthoritarian):
    """Responds to Instagam links"""

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @ commands.Cog.listener()
    async def on_message(self, msg: Message):
        """Warns the user if they post a private Instagram link."""
        # don't respond to the bot
        if self.bot.user == msg.author:
            return

        if self.babysitter.disabled:
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

    @ commands.Cog.listener()
    async def on_message(self, msg: Message):
        """Check for duplicate images."""
        # don't respond to self
        if msg.author == self.bot.user:
            return

        if self.babysitter.disabled:
            return

        await self.hash_check(msg)

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

    async def hash_check(self, msg: Message):
        """Hash all of the media and article links and delete the message if it had any duplicates."""
        # get the urls of all media in the message
        urls = await self._get_urls(msg)
        # find out which links are articles
        article_links = (await self._get_msg_links(msg)).difference(urls)

        # download all media
        LIMIT = 1024  # 1024 bytes = 1 KB
        for url in urls:
            # hash the first KB of the media and check if it was already posted
            async with download_resource(url, LIMIT) as file:
                bytes = await file.content
            await self._check_duplicate(msg, hash(bytes))

        # check if the articles have been posted before
        for url in article_links:
            await self._check_duplicate(msg, hash(url))

    @ commands.command(aliases=["SCa"])
    @ commands.is_owner()
    async def show_cache(self, ctx):
        """Output all hashes that have been cached. Debugging tool."""
        await mestils.send_as_chunks(
            self.hashes.pretty_cache,
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

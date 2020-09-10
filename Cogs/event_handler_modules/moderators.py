from Utils import mestils
from json import dumps
from discord.ext import commands, tasks
from discord import Message, Member, HTTPException, NotFound, File, Embed
from typing import Optional, List, Dict, Union
import datetime as D


class MessageAuthoritarian(commands.Cog):
    """Base class for deleting messages if they meet a condition."""
    last_msg: str = None  # the last deleted message

    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
            MessageAuthoritarian.last_msg = msg
            await msg.delete(delay=2)


class AuthoritarianBabySitter(commands.Cog):
    """Holds the resummon_message command to avoid double-registering it."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=["RS", "resummon", "come_back", "false_positive"
                               "false_hit", "resummon_msg"])
    async def resummon_message(self, ctx):
        """Repost the last deleted message."""
        msg = MessageAuthoritarian.last_msg  # the name is too long
        if msg is None:
            return await ctx.send("I have not deleted anything today, my lord.")

        # avoid an empty message and allow adding error messages
        to_send = msg.content or "`[placeholder]`"

        # attempt to retrieve the attachments
        to_attach: List[Optional[File]] = []
        try:
            to_attach = [await attachment.to_file(use_cached=True)  # use_cached makes it more robust
                         for attachment in msg.attachments]
        except (HTTPException, NotFound):
            to_send += "\n`[Failed to get attachments]`"
        # send the text and attachments
        await mestils.send_as_chunks(f"{to_send}", ctx,
                                     files=to_attach,
                                     embed=msg.embeds[0])
        # send the embeds(s). Disord.py doesn't allow > 1 embed per msg
        if len(msg.embeds > 1):
            for embed in msg.embeds:
                await ctx.send(embed=embed)


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
                MessageAuthoritarian.last_msg = msg
                await msg.delete(delay=2)


class RepostHandler(MessageAuthoritarian):
    """Deletes reposted links.

    ATTRIBUTES:
        hashes: format: {the first KB of a file hashed | a URL : timestamp}"""

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        # all of the hashed images from the past 48 hours
        self.hashes: Dict[str, D.datetime] = {}
        self.clean_up_hashes.start()

    @tasks.loop(hours=12)
    async def clean_up_hashes(self) -> tasks.Loop:
        """Removes all links that are more than 2 days old"""
        now = D.datetime.now()
        # this will replace self.links to avoid deleting during iteration
        self.hashes = dict(
            filter(lambda pair: (now - pair[1]).days < 2, self.hashes.items()))  # filter by date within 2 days of now

    @ commands.Cog.listener()
    async def on_message(self, msg: Message):
        """Deletes reposted images"""
        async def check_duplicate(hash: str):
            """Check if the hash is already in self.hashes. If so, delete the message.
            Otherwise: cache the hash."""
            if hash in self.hashes:
                # the link has been saved, so delete the message
                await msg.channel.send("}=< No repostium in this discordium >={",
                                       delete_after=20)
                MessageAuthoritarian.last_msg = msg
                await msg.delete(delay=2)
            else:  # save the link
                self.hashes[hash] = D.datetime.now()

                # don't reply to self
        if msg.author == self.bot.user:
            return

        # the hash of the pixels of the media (loaded as bytes)
        media_hashes: List[str] = []
        # check for uploaded files
        if msg.attachments:
            for attached_file in msg.attachments:
                # this can't be limited so maybe use another method to save memory
                attached_file_bytes = await attached_file.read(use_cached=True)
                media_hashes.append(hash(attached_file_bytes))

        # check for embeds
        if not msg.embeds:
            return

        # get hashes of the media (loaded as bytes)
        # must be separate ifs because there could be a video, article, and image
        for embed in msg.embeds:
            # avoid empty embed
            if (embed.image == Embed.Empty and embed.video == Embed.Empty
                    and embed.url == Embed.Empty):
                print(f"Empty embed ignored. Object: {embed}")
                return
            if embed.video != Embed.Empty:
                # save video link
                async with mestils.download_resource(embed.video.url, limit=1024) as rss:
                    media_hashes.append(hash(await rss.content))
            if embed.url != Embed.Empty:  # it's some kind of article
                # save article link
                check_duplicate(embed.url)
            if embed.image != Embed.Empty:  # it's an image
                async with mestils.download_resource(embed.image.url, limit=1024) as rss:
                    media_hashes.append(hash(await rss.content))

        # check each of the hashes
        for hash_ in media_hashes:
            await check_duplicate(hash_)

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

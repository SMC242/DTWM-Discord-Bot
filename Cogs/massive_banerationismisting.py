from discord.ext import commands
from discord import Member
from Utils.common import leader_roles
from traceback import print_exc


class MessageScrubber(commands.Cog):
    """Cleans out messages from a targeted user"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.has_any_role(*leader_roles)
    @commands.command()
    async def scrub_messages(self, ctx: commands.Context, person: Member):
        """Delete all of a member's messages."""
        print(person.display_name)
        progress_msg = await ctx.send("Channels covered:\n")
        for channel in ctx.guild.text_channels:
            perms = channel.permissions_for(ctx.me)
            if not all((perms.manage_messages, perms.read_message_history, perms.read_messages)) and not perms.administrator:
                await ctx.send(f"{channel.name} skipped due to lack of permissions")
                continue
            await channel.purge(check=lambda m: m.author == person)
            await progress_msg.edit(content=progress_msg.content + f"\n{channel.name}")
        await ctx.send("Done")

    @commands.has_any_role(*leader_roles)
    @commands.command()
    async def test(self, ctx: commands.Context, person: Member):
        """Delete all of a member's messages."""
        print(person.display_name)
        progress_msg = await ctx.send("Channels covered:\n")
        for channel in ctx.guild.text_channels:
            perms = channel.permissions_for(ctx.me)
            if not all((perms.manage_messages, perms.read_message_history, perms.read_messages)) and not perms.administrator:
                await ctx.send(f"{channel.name} skipped due to lack of permissions")
                continue
            async for msg in channel.history(limit=None):
                if msg.author == person:
                    await msg.delete()
            await progress_msg.edit(content=progress_msg.content + f"\n{channel.name}")
        await ctx.send("Done")

    @scrub_messages.error
    async def on_scrub_message_error(self, ctx, error):
        if isinstance(error, commands.ConversionError):
            return ctx.send("That is not a person")
        else:
            print_exc()
            await ctx.send("Error occurred")


def setup(bot: commands.Bot):
    bot.add_cog(MessageScrubber(bot))

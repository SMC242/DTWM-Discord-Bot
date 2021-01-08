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
    async def purge_messages(self, ctx: commands.Context, person: Member):
        """Note: does not work. Delete all of a member's messages."""

        progress_msg = await ctx.send("Channels covered:\n")
        for channel in ctx.guild.text_channels:
            # handle no delete permissions
            perms = channel.permissions_for(ctx.me)
            if not all((perms.manage_messages, perms.read_message_history, perms.read_messages)) and not perms.administrator:
                await ctx.send(f"{channel.name} skipped due to lack of permissions")
                continue

            # delete the messages
            await channel.purge(check=lambda m: m.author == person)
            await progress_msg.edit(content=progress_msg.content + f"\n{channel.name}")
        await ctx.send("Done")

    @commands.has_any_role(*leader_roles)
    @commands.command()
    async def delete_messages(self, ctx: commands.Context, person: Member):
        """Delete all of a member's messages."""

        progress_msg = await ctx.send("Channels covered:\n")
        for channel in ctx.guild.text_channels:
            # handle no delete permissions
            perms = channel.permissions_for(ctx.me)
            if not all((perms.manage_messages, perms.read_message_history, perms.read_messages)) and not perms.administrator:
                await ctx.send(f"{channel.name} skipped due to lack of permissions")
                continue

            # delete the messages
            async for msg in channel.history(limit=None):
                if msg.author == person:
                    await msg.delete()
            await progress_msg.edit(content=progress_msg.content + f"\n{channel.name}")
        await ctx.send("Done")

    @commands.Cog.cog_command_error
    async def on_scrub_message_error(self, ctx, error):
        if isinstance(error, commands.ConversionError):
            return ctx.send("That is not a person")
        else:
            print_exc()
            await ctx.send("Error occurred")


def setup(bot: commands.Bot):
    bot.add_cog(MessageScrubber(bot))

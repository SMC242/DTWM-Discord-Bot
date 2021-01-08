from discord.ext import commands
from discord import Member
from Utils.common import leader_roles


class MessageScrubber(commands.Cog):
    """Cleans out messages from a targeted user"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.has_any_role(*leader_roles)
    @commands.command()
    async def scrub_messages(self, ctx: commands.Context, person: Member):
        """Delete all of a member's messages."""
        progress_msg = await ctx.send("0 channels covered")
        for channel in ctx.guild.text_channels:
            perms = channel.permissions_for(self.bot.user)
            if not perms.manage_messages or not perms.read_message_history:
                await ctx.send(f"{channel.name} skipped due to lack of permissions")
                continue
            await channel.purge(check=lambda m: m.author == person)
            await progress_msg.edit(content=f"{progress_msg.content[0] + 1} channels covered")
        await ctx.send("Done")

    @scrub_messages.error
    async def on_scrub_message_error(self, ctx, error):
        if isinstance(error, commands.ConversionError):
            return ctx.send("That is not a person")
        else:
            raise error


def setup(bot: commands.Bot):
    bot.add_cog(MessageScrubber(bot))

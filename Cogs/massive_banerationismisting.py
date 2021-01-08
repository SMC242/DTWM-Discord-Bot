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
        await ctx.channel.purge(check=lambda m: m.author == person)

    @scrub_messages.error()
    async def on_scrub_message_error(self, ctx, error):
        if isinstance(error, commands.ConversionError):
            return ctx.send("That is not a person")


def setup(bot: commands.Bot):
    bot.add_cog(MessageScrubber(bot))

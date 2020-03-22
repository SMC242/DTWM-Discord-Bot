import discord
from discord.ext import commands


def inBotChannel():
    """This commands may only be use din the bot channel."""

    async def predicate(ctx):
        botChannel = ctx.bot.get_channel(545818844036464670)

        if not botChannel == ctx.channel:
            await ctx.send(f'These are matters for {botChannel.mention}, '
                           'brother. Take it there and I will answer you')
            return False
        return True

    return commands.check(predicate)


def isLeader():
    """Decoratorto only allow leaders to call the command."""

    async def predicate(ctx):
        user_roles = [r.name.lower() for r in ctx.message.author.roles]

        return ('watch leader' in user_roles
                or 'champion' in user_roles)

    return commands.check(predicate)

"""Outfit-specific utilities and weeb commands."""

import json
import random
import time
import discord
from discord.ext import commands
from checks import inBotChannel, isLeader


class Dtwm(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['weeb'])
    @inBotChannel()
    @commands.cooldown(1, 5, type=commands.BucketType.user)
    async def ayaya(self, ctx):
        """Tell the bot to be a weeb."""

        responses = ['ayaya!',
                     'AYAYA!',
                     'ayaya ayaya!',
                     'AYAYA AYAYA!',
                     'ayaya ayaya ayaya!',
                     'AYAYA AYAYA AYAYA!']

        await ctx.send(random.choice(responses))

    @commands.command(aliases=['kys', 'die', 'fuckYou'])
    @inBotChannel()
    @commands.cooldown(1, 5, type=commands.BucketType.user)
    async def commitNotAlive(self, ctx):
        """Tell the bot to kill itself."""

        responses = ['no u',
                     'commit neck rope',
                     'die',
                     'kys']

        await ctx.send(random.choice(responses))

    @commands.command(aliases=['fun', 'random'])
    @inBotChannel()
    async def fluff(self, ctx):
        """Pick a random fluff command and execute it."""

        fluff_commands = [self.imNotAMember,
                          self.patLoli,
                          self.ayaya,
                          self.commitNotAlive,
                          self.giveAdvice,
                          self.ping]

        async with ctx.typing():
            choice = random.choice(fluff_commands)
            await ctx.send(f'Invoking {choice.__name__}:')
            await ctx.invoke(choice)

    @commands.command(aliases=['V5', 'INeedARide', 'WaitUpLetMeHopIn'])
    @inBotChannel()
    @isLeader()
    async def getInOps(self, ctx):
        """Ping every member that is playing PS2 but not in comms."""

        def validate_role(member):
            roles = [r.name.lower() for r in member.roles]
            return 'astartes' in roles or 'watch leader' in roles

        async with ctx.typing():
            # Get the event channel IDs
            event_channel_ids = json.load('data/event_channels.json')

            # Get members with Astartes and higher
            members = [m for c in ctx.guild.voice_channels
                       for m in c.members if validate_role(m)]

            # Get every member that is playing PS2
            ingame_members = set(m for a in m.activities for m in members
                                 if a.name == 'PlanetSide 2')

            # Ping every member that is playing PS2 but not in voice
            for member in ingame_members:
                in_channel = False
                for channel in [self.bot.get_channel(id_)
                                for id_ in event_channel_ids]:
                    if member in channel.members:
                        in_channel = True
                        break
                if not in_channel:
                    await ctx.send(
                        f'{member.mention} an event is going on right now, '
                        'brother. Come join us in glory!')

    @commands.command(aliases=['week', 'whatTraining', 'trainingWeek', 'armourOrAir'])
    @inBotChannel()
    @isLeader()
    async def getTrainingWeek(self, ctx):
        """Returns whether this week is armour or air training."""

        await ctx.send(f'This week, we will train for {topic}, Brother.')

    @commands.command(aliases=['advice', 'advise', 'adviseMe'])
    @inBotChannel()
    @commands.cooldown(1, 5, type=commands.BucketType.user)
    async def giveAdvice(self, ctx, target: str = None):
        """Gives you advice based on your roles

        If you're a scout you will get mostly useful advice
        Arguments: ab!giveAdvice {target}
        **[optional]** the target role
        """
        # Max number of responses per invokation
        MAX_RESPONSES = 2

        await ctx.send('*Thinking...*')

        responses = json.load('data/advice.json')

        with ctx.typing():
            if target is not None:
                try:
                    return await ctx.send(random.choice(
                        responses[target.lower]))
                except BaseException:
                    # TODO: Add error handlers for missing roles and typos
                    return

            # Get a list of all roles
            user_roles = set(r.name.lower() for r in ctx.message.author.roles)

            # Special case for newcomers
            if 'scout' in user_roles:
                await ctx.send(
                    'You will get serious advice as you are new here:\n'
                    f'{random.choice(responses["scout"])}')
                return

            # Get a list of all roles on record
            dict_roles = set(k.lower() for k in responses)

            valid_options = user_roles.intersection(dict_roles)

            for _ in range(MAX_RESPONSES):
                key = random.choice(valid_options)
                await ctx.send(random.choice(responses[key]))

    @commands.command(aliases=['notMember', 'notM'])
    @commands.cooldown(1, 5, type=commands.BucketType.user)
    async def imNotAMember(self, ctx):
        """Reacts to whether you'Re a member of DTWM."""
        if not 'astartes' or 'watch leader' in ctx.author.roles:
            await ctx.send('Join DTWM on Miller NC!')
            await ctx.invoke(self.bot.get_command('joinDtwm'))
        else:
            await ctx.send('Brother, you are one of us!')

    @commands.command(aliases=['join', 'j'])
    @commands.cooldown(1, 60, type=commands.BucketType.user)
    async def joinDTWM(self, ctx):
        """Posts the invite link to the Discord server."""
        await ctx.send(
            'Come quickly, brother! We can always use new Astartes. '
            'https://joindtwm.net/join')

    @commands.command(aliases=['pat', 'headpat'])
    @inBotChannel()
    @commands.cooldown(1, 5, type=commands.BucketType.user)
    async def patLoli(self, ctx):
        """Get the bot to pat a loli"""

        emotes = ['<:w_komi_headpat:661011597048938505>',
                  '<a:BTS_pat9:661014548970602506>',
                  '<a:BTS_pat8:661014550396665856>',
                  '<:BTS_pat7:661014545543856178>',
                  '<:BTS_pat6:661014545791320104>',
                  '<:BTS_pat5:661014545560764416>',
                  '<:BTS_pat4:661014544860053504>',
                  '<:BTS_pat3:661014543631253550>',
                  '<a:BTS_pat2:661014549922578432>',
                  '<a:BTS_pat12:661014546260951095>',
                  '<:BTS_pat11:661014545795645443>',
                  '<a:BTS_pat10:661014544944070656>',
                  '<:BTS_pat:661014543765602314>']

        await ctx.send(random.choice(emotes))

    @commands.command(aliases=['p', 'speed'])
    @inBotChannel()
    @commands.cooldown(1, 5, type=commands.BucketType.user)
    async def ping(self, ctx):
        """Check how fast the bot is running."""

        async with ctx.typing():
            # Get timedelta
            startTime = time.time()
            await ctx.send('You summoned me, my Lord?')
            timedelta = time.time() - startTime

            # React to result
            if timedelta <= 0.1:
                msg = 'I came as fast as I could'
            elif timedelta <= 0.5:
                msg = 'I polished your armour'
            else:
                msg = 'RIP'

            print(f'   Process time: {timedelta} seconds\n'
                  f'   Latency: {self.bot.latency}')
            # 'The Tyranids are coming!
            # You must escape now and send word to Terra'
            # NOTE: When tf does it say that? - Auro
            await ctx.send(msg + ':\n```'
                           f'Latency: {self.bot.latency:.2f}\n'
                           f'I took {timedelta:.2f} seconds to get here.```')

"""All of the attendance-related functions and commands."""

from typing import *
from discord import *
from discord.ext import commands
from datetime import datetime, time, date
import asyncio
from classes import AsyncCommand

# checks
def isLeader():
    '''Decorator to allow only leaders to call the command'''
    async def inner(ctx):
        #checking if the user is a leader
        success= await checkRoles((ctx.message.author,), ("Watch Leader", "Champion"))

        if not success:
            raise NotLeaderError()

        return success

    return commands.check(inner)


def inBotChannel():
    '''Checks if called in bot channel.
    If not in bot channel, doesn't execute command and scolds.
    Unless command is whitelisted'''

    async def inner(ctx):
        # log the command
        print(f"command: {ctx.command.name} call recieved at {D.datetime.today().time().strftime('%H hours, %M minutes')}")
        botChannel=ctx.bot.get_channel(545818844036464670)

        if not botChannel==ctx.message.channel:
            await ctx.send(f"These are matters for {botChannel.mention}, brother. Take it there and I will answer you")
            return False

        else:
            return True

    return commands.check(inner)


@bot.group()
@isLeader()
async def leader(ctx):
    if ctx.invoked_subcommand is None:
        return await ctx.send('Give me your orders, My Lord. I am but a lowly servitor, not a psyker')


class AttendanceCog(commands.Cog):
    """Contains all the attendance commands and functions."""

    # ATTRIBUTES
    startDay: datetime = None


    # METHODS
    def __init__(self, bot: commands.Bot):
        """Schedule attendance."""

        self.bot = bot
        self.startDay = datetime.today().date().day

        asyncio.get_event_loop().create_task(self.scheduleAttendance())


    async def scheduleAttendance(self):
        """Infinitely attempt to schedule attendanc,
        if a day has passed."""

        while True:
            # get time now
            today = datetime.today().date()
            timenow = datetime.today().time()

            # day has changed --> schedule attendance
            if today.day != self.startDay and today.day != 5:  # no events on Saturday
                # remove once this comes out of the testing phase
                await self.bot.get_channel(545818844036464670).send("```css\nTemporary logging: Attendance scheduled```")

                # update startDay
                self.startDay = today

                # handle starting during an event
                if 2000 < int(timenow.strftime("%H%M")) < 2130:  #if started during an event
                    attendees=await executeOnEvents(AsyncCommand(self.getAttendance, name="getAttendance",
                        arguments=(bot.get_guild(545422040644190220),)))

                    await self.callAttendance(attendees)

                # wait until the event
                else:
                    # calculate seconds to event start
                    target=time(19, 59)  # in UTC
    
                    newTarget = datetime.combine(date.min, target)
                    oldTime = datetime.combine(date.min, timenow)
                    runInSeconds = (newTarget - oldTime).seconds

                    # wait until event time
                    await asyncio.sleep(runInSeconds)

                    #ping people to get in ops
                    await getInOpsInner()

                    # do attendance
                    attendees=await executeOnEvents(AsyncCommand(self.getAttendance, name="getAttendance", arguments=(bot.get_guild(545422040644190220),)))
                        
                    failure= await self.callAttendance(attendees)

            # wait 4 hours, then check again
            await asyncio.sleep(14400)


    async def getAttendance(self, ctx: Union[commands.Context, Guild])-> List[str]:
        '''Returns a list of people in the ops/training channels'''
        #reads the channels to check from a file
        #appends the channel IDs to channels
        channels=createListFromFile("channels.txt", type=int)

        #get guild
        if not isinstance(ctx, Guild):
            server=ctx.message.guild

        else:
            server=ctx
    
        #get list of names in ops
        #for every channel in channels it gets the members  
        #sequentially and appends them to the list
        channelMembers=[]
        for channel in channels:
            channel=server.get_channel(channel)

            for attendee in channel.members:
                channelMembers.append(attendee.display_name)

        #parsing the names
        attendees = await removeTitles(channelMembers)

        print(f"Attendees at {D.datetime.now().strftime('%H%M')}: {attendees}")

        return attendees


    async def attendanceWrapper(self, ctx):
        '''This wrapper exists so that attendance can be called outside of doAttendance
        as doAttendance is a command object'''
        attendees=await self.getAttendance(ctx)

        DBWriter=bot.get_cog('AttendanceDBWriter')
        await DBWriter.sendAttToDB(attendees)

        return attendees


    @leader.command(aliases=["attendance","getAttendance", "att"])
    @inBotChannel()
    @commands.cooldown(1, 60, type=commands.BucketType.user)
    async def doAttendance(self, ctx):
        '''Records current attendees in the db.'''
    
        #give user feedback
        await ctx.send("It will be done, my Lord")

        async with ctx.typing():
            attendees=await self.attendanceWrapper(ctx)

            if failure:
                await ctx.send('We do not take roll call on Saturdays!')

            if attendees==[]:
                await ctx.send("Nobody is there, My Liege. Our men have become complacent!")

            else:
                await ctx.send(f"Attendees: {attendees}")

            await ctx.send("Attendance check completed **UmU**")


# for the cog loader
def setup(bot: commands.Bot):
    bot.add_cog(AttendanceCog(bot))

if __name__ == "__main__":
    setup(commands.Bot("ab"))
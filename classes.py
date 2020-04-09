#author: benmitchellmtb, auroram
from discord.ext import commands
from discord import *
import threading, os, sys, traceback, asyncio, re, random, csv, string, concurrent
from DB import AttendanceDBWriter
from typing import Callable, Union, Tuple, List
import datetime as D
from functools import wraps

def validateString(string: str, validAnswers: List[str]=None)-> bool:
    '''Check if the input is valid against basic checks and validAnswers, if not None
    
    CHECKS
    length is not 0
    string is not empty
    string is in validAnswers if exists
    
    string: the input to be validated
    validAsnwers: string must be in this list to be valid
    
    RETURNS
    True: if valid
    False: if not valid'''

    if string == "":
        return False

    elif len(string) == 0:
        return False

    elif validAnswers is not None and string not in validAnswers:
        return None

    else:
        return True


def createListFromFile(filePath, type=str):
    '''Returns a list populated by parsed lines from a text file.
    Prefixes filePath with 'TextFiles/'.

    filePath: string path of the file to be read
    varList: output list
    type: the type of variables to be read (str, int, float, etc)'''

    with open("Text Files/"+filePath) as f:
       varList=[type((line.strip("\n")).lower()) for line in f]
    
    return varList  


def insertionSort(unsorted: list)->list:
    '''Sorts the input list and returns a sorted list
    
    Adapted from https://www.geeksforgeeks.org/python-program-for-insertion-sort/'''

    for outerCount in range(1, len(unsorted)-1):
        current=unsorted[outerCount]
        innerCount=outerCount-1

        while innerCount>=0 and current < unsorted[innerCount]:
            unsorted[innerCount+1]=unsorted[innerCount]
            innerCount-=1

            unsorted[innerCount+1]=current

    return unsorted


def binarySearch(target, toSearch: list, returnIndex=True)->Union[int, bool]:
    '''Search the input list for target

    returnIndex: true=return index of target. False=return found bool'''

    lower=0
    upper=len(toSearch)-1
    mid=lower + ((upper-lower) // 2)
    found=False

    while not found and lower<=upper:
        mid=lower + ((upper-lower) // 2)

        if toSearch[mid]==target:  #target is found
            found=True

        elif toSearch[mid]>target:  #target is smaller than current
            upper=mid-1

        else:  #target is larger than current
            lower=mid+1

    if found:
        if returnIndex:
            return mid

        else:
            return True

    else:
        return False


def searchWord(word: str, msg: Union[Message, str])->bool:
    '''Returns a bool based on whether the word is in the message'''

    #ensuring msg is a string
    if isinstance(msg, Message):
        msg=msg.contents

    return (re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE).search(msg)) is not None


class MessageResponses(commands.Cog):
    """Base class. Handles reacting to messages with on_message events.
    
    getChannels must be run upon on_ready"""

    def __init__(self, bot: commands.Bot, cooldown: int = 60):
        """cooldown is in seconds."""

        self.bot = bot
        self.cooldown = cooldown
        self.parent = None  # will be registered to a ReactionParent


    async def getChannels(self):
        '''Creates the dict of channels.
        Cannot be done before on_ready'''

        today=D.date.today()
        tempHit=D.datetime(today.year, today.month, today.day)  #add placeholder datetime until there's a hit

        server= self.bot.get_guild(545422040644190220)
        self.channels = {tChannel : tempHit for tChannel in server.text_channels}  #for rate limiting by channel


    async def checkLastHit(self, msg: Message):
        '''Check if rate limited'''

        #search for channel
        try:
            lastHit=self.channels[msg.channel]

        except KeyError:  #message in newly-created channel
            self.getChannels()  #check the channels again
            return False

        except AttributeError:  #channel list not set up yet
            return False

        #check hit
        timenow=D.datetime.now()
        if (timenow - lastHit).total_seconds() > self.cooldown:            
            return True

        else:
            return False


    def on_message(self, msg: Message):
        raise NotImplementedError()


class ReactionParent:
    """Handles sharing settings between all MessageResponses Cogs."""

    def __init__(self, children: List[MessageResponses]):
        self.reactionsAllowed = True

        # register children
        for child in children:
            child.parent = self

        self.children = children


    async def getChannels(self):
        """Set up the channels attribute for all children."""

        # get the channels dict
        await self.children[0].getChannels()
        channels = self.children[0].channels

        # send it to each child
        for child in self.children:
            child.channels = channels


class MessageReactions(MessageResponses):
    """Manages adding reactionst to messages"""

    def __init__(self, bot: commands.Bot, cooldown: int = 60):
        super().__init__(bot, cooldown)


    async def react(self, target: Message, emote: Union[Emoji, int]):
        '''Wrapper for Message.add_reaction.

        Updates self.lastHit'''

        if not isinstance(emote, Emoji):
            emote=self.bot.get_emoji(emote)

        return await target.add_reaction(emote)


    @commands.Cog.listener()
    async def on_message(self, inputMsg: Message):
        if inputMsg.author==self.bot.user:  #don't respond to self
            return

        if not (await self.checkLastHit(inputMsg) and self.parent.reactionsAllowed):
            return

        msg=inputMsg.content.lower()

        #check for whitelisted emotes
        if searchWord("php", msg):
            emoteID=662430179129294867

        elif searchWord("ayaya", msg) or "<:w_ayaya:622141714655870982>" in msg:
            emoteID=622141714655870982

        else:
            return

        #if matched
        channel = inputMsg.channel
        async with channel.typing():
            self.channels[channel]=D.datetime.now()
            await self.react(inputMsg, emoteID)
            return await channel.send("_", delete_after = 0.0000000000001)  #to end the typing


class MessageResponseMessages(MessageResponses):
    """Handles sending messages in response to users."""

    def __init__(self, bot: commands.Bot, cooldown: int = 300):
        super().__init__(bot, cooldown)


    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        if msg.author==self.bot.user:  #don't respond to self
            return

        if not (await self.checkLastHit(msg) and self.parent.reactionsAllowed):
            return

        pingResponses = [
            "Who ping?",
            "Stop ping",
            "What do you want?",
            "Stop pinging me, cunt",
            "<:w_all_might_ping:590815766895656984>",
            "<:ping_wake_up_magi:597537421046841374>",
            "<:ping6:685193730709389363>",
            "<:ping5:685193730965504043>",
            "<a:ping4:685194385511678056>",
            "<a:ping3:685193731611295778>",
            "<a:ping2:685193730877423727>",
            "<a:ping1:685193730743074867>",
            "<:ping:685193730701000843>",
        ]

        # get angry if ben was pinged
        mentioned = [mention.id for mention in msg.mentions]
        if 395598378387636234 in mentioned or 507206805621964801 in mentioned:
            output = random.choice(pingResponses)

        # respond to princess sheep
        elif 326713068451004426 == msg.author.id:
            output = "Here's your bot function. BAAAAAAAAAAAAAAAAAAAA!"

        else: 
            return

        # if matched
        channel = msg.channel
        async with channel.typing():
            self.channels[channel]=D.datetime.now()
            return await channel.send(output)


class botOverrides(commands.Cog):
    """Handle any behvaiour changes for the bot"""

    reactionsAllowed=True
    schedulingRan = False

    def __init__(self, bot: commands.Bot):
        '''Subclass of Cog to override certain functions of Bot.
        getChannels must be called after on_ready to fully initialise this class'''

        self.bot=bot

        # add all other Cogs
        cogs = [AttendanceDBWriter(self.bot), MessageResponseMessages(self.bot),
            MessageReactions(self.bot)]
        for instance in cogs:
            self.bot.add_cog(instance)

        self.reactionParent = ReactionParent(cogs[1:])

        # get which training week it is
        with open("Text Files/trainingWeek.csv") as f:
            for row in csv.reader(f, "excel"):
                trainingWeekRow=row  #this will take the final row as the correct week

        trainingWeekRow=map(int, trainingWeekRow)  #convert all to int

        self.firstTrainingWeek=D.datetime(*trainingWeekRow)

        # attendance rescheduler
        self.startDay = D.datetime.today().date()


    async def chooseStatus(self):
        '''Update random status hourly'''

        playingStatuses=[
            "Purging Heretics and Patting Lolis",
            "raid: ben's hentai stash",
            "Quest For The Tankist Role",
            "Recruiting Blueberries",
            "Ayaya",
            "Zerging",
            "Applying For DTWM Simulator",
            "A Mad 0.1 KPM 0.2 KDR sesh 😤",
            "Plotting A Split",
            "Debating Best Girl",
            "Spanking Guardsmen",
            "Crusade Planning",
            "Commander Cyrious: Keyboard Warrior",
            "A Heated Gamer Moment",
            "Editing A Sick Montage",
            "Slaaneshi Gathering",
            "Waiting For the Council Meeting To End",
            "Learning to Feel Pain",
            "UwU",
            "UmU",
            "Heresy Detected",
            '"Washing" My Body Pillow',
            "With My Waifu",
            "Itadakimasu~!",
            "Seals For Supper",
            "Regretting Starting An Open Platoon",
            "Anywhere But The Waypoint",
        ]

        watchingStatuses=[
            "Ahegao Tutorials",
            "Ayaya Intensifies"
            ]

        statuses=[Activity(name=msg, type=ActivityType.playing) for msg in playingStatuses]
        watching=[Activity(name=msg, type=ActivityType.watching) for msg in watchingStatuses]

        statuses+=watching

        while True:
            #set random status
            await self.bot.change_presence(activity=random.choice(statuses))

            await asyncio.sleep(3600)  #change presence every hour


    async def rescheduleAttendance(self):
        """
        Infinitely check if a new day has passed. 
        If a day has passed, reschedule attendance.
        """

        # check for a new day every 4 hours
        while True:
            await self.scheduleAttendance()
            await asyncio.sleep(14400)


    async def scheduleAttendance(self):
        """Schedule attendance if it hasn't been scheduled today."""

        # prevent duplicate queues
        # by checking if it's a new day
        today = D.datetime.today().day

        if self.startDay != today:
            self.schedulingRan = False
            self.startDay = today

        # exit if this already ran today
        if self.schedulingRan:
            return

        else:
            self.schedulingRan = True
            # remove once this comes out of the testing phase
            await self.bot.get_channel(545818844036464670).send("```css\nTemporary logging: Attendance scheduled```")

        # getting the required functions
        from Discord_Bot import executeOnEvents, callAttendance, getInOpsInner

        #scheduling the attendance function
        timenow=D.datetime.now()
        if timenow.weekday() == 5:  #no events on Saturday
            return

        timenow=timenow.time()

        # wait until the event time
        target=D.time(19, 59)
    
        newTarget=D.datetime.combine(D.date.min, target)
        oldTime=D.datetime.combine(D.date.min, timenow)
        runInSeconds= (newTarget - oldTime).seconds

        await asyncio.sleep(runInSeconds)

        await getInOpsInner()  #ping people to get in ops

        attendees=await executeOnEvents(AsyncCommand(getAttendance, name="getAttendance", arguments=(bot.get_guild(545422040644190220),)))
        ignored = await callAttendance(attendees)


    @property
    def trainingWeek(self)-> str:
        '''Get the current training week - air or armour
        
        THROWS
        ValueError: firstTrainingWeek is not a monday = check trainingWeek.txt is a monday'''
        #credit to auroram for rewrite

        #find this week's monday
        today=D.date.today()
        
        topics = ['Aerial Superiority', 'Armour Support']

        _, week_num, _ = today.isocalendar()
        # NOTE: 1st week: air, 2nd week: armour, 3rd week: air, etc.
        # This scales with the number of actual topics, no changes needed!
        topic = topics[week_num % len(topics) - 1]

        return topic
    

    @commands.Cog.listener()
    async def on_command_error(self, ctx, exception):
        """Handle an exception raised during command invokation."""
        # Only use this error handler if the current context does not provide its
        # own error handler
        if hasattr(ctx.command, 'on_error'):
            return
        # Only use this error handler if the current cog does not implement its
        # own error handler
        if ctx.cog and commands.Cog._get_overridden_method(
                ctx.cog.cog_command_error) is not None:
            return

        #if command on cooldown
        if isinstance(exception, commands.CommandOnCooldown):
          return await ctx.send(f"Hold on, My Lord. I must gather my energy before another\nTry again in {int(exception.retry_after)} seconds!")

        #if command is unknown
        elif isinstance(exception, commands.CommandNotFound):
            if '@' in ctx.invoked_with :
                return await ctx.send("How dare you try to use me to annoy others!")

            else:
                return await ctx.send(f'Sorry My Lord, the archives do not know of this "{ctx.invoked_with}" you speak of')

        elif isinstance(exception, commands.MissingRequiredArgument):
            return await ctx.send("Your command is incomplete, My Lord! You must tell me my target")

        elif isinstance(exception, commands.CheckFailure):
            #the handling for this is done in the checking decorators
            pass

        elif isinstance(exception, NotLeaderError):
            return await ctx.send("Only leaders may do that, brother. Go back to your company")

        elif isinstance(exception, commands.DisabledCommand):
            return await ctx.send("I cannot do that, My Lord. The Adepts are doing maintenance on this coroutine.")

        elif isinstance(exception, commands.BadArgument):
            return await ctx.send("I don't understand your orders, My Lord")

        elif isinstance(exception, RateLimited):
            return await ctx.send("Please give me room to think, Brother")

        elif isinstance(exception, CommandNotImplementedError):
            return await ctx.send("The Adepts are yet to complete that command, Brother")

        #if bot can't access the channel
        elif isinstance(exception, Forbidden):
            return await ctx.send("I can't access one or more of those channels TwT")

        #elif isinstance(exception, commands.NotFound):
        #    #silence errors from instances being deleted partway through a command execution
        #    pass

        else:  #if not caught by previous conditions, display error
            # NOTE: This is the default error handling behaviour, which is kept for
            # development purposes for the time being, but will be disabled at a later
            # point
            print(f'Ignoring exception in command {ctx.command}:', file=sys.stderr)

            # fetch exception and convert it to one string
            rootException = exception.original  # fetch the original error
            tbLines = traceback.format_exception(type(rootException), rootException,
                                      rootException.__traceback__)
            tb = "\n".join(tbLines)
            tb = tb + f"Occured at: {D.datetime.now().time()}"

            # dump to terminal
            print(tb)

            # dump error to a log file
            with open("Text Files/errorLog.txt", "a+") as f:
                f.write(tb)

            # dump error to bot testing.errors
            await self.bot.get_channel(697746979782000680).send(f"```\n{tb}```")

            #give user feedback if internal error occurs
            return await ctx.send("Warp energies inhibit me... I cannot do that, My Lord")  


class TerminalCommand:
    '''Class to wrap all information about a terminal command'''

    population=0

    def __init__(self, func: Callable, name: str=None, description: str=None, arguments: Union[List, Tuple]=None):
        self.func=func
        self.population=TerminalCommand.population+1

        if name is None:
            self.name=f"func{self.population}"
        else:
            self.name=name

        if description is None:
            self.description="No description"

        else:
            self.description=description

        if arguments is None:
            self.arguments=None

        else:
            self.arguments=arguments


    def call(self):
        '''Calls the object's function with its arguments
        Catches any errors and re-raises them
        Returns the results'''

        try:
            if self.arguments is not None:
                return self.func(*self.arguments)

            else:
                return self.func()

        except Exception as error:
            raise error

    @property
    def details(self):
        return f"Name: {self.name}\nDescription: {self.description}"

class AsyncCommand(TerminalCommand):
    async def call(self):
        '''Returns the output of self.coro'''
        return await self.coro

    @property
    def coro(self):
        '''Returns a coroutine for the func and its args'''
        if self.arguments is not None:
            return self.func(*self.arguments)

        else:
            return self.func()


class ThreadCommand(TerminalCommand):
    @property
    def thread(self):
        '''Returns an instance of Threading.Thread for the function and its args'''

        return threading.Thread(target=self.func, args=self.arguments, name=self.name)

    def call(self):
        return self.thread.start()


class NotLeaderError(commands.CommandError):
    '''If the Member is not >=Champion'''
    pass

class RateLimited(commands.CommandError):
    '''For the custom on_message rate limiter'''
    pass

class CommandNotImplementedError(commands.CommandError):
    '''Command partially complete but not disabled for testing reasons'''
    pass
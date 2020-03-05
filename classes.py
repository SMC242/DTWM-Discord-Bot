#author: benmitchellmtb, auroram
from discord.ext import commands
from discord import *
import threading, os, sys, traceback, asyncio, re, random, csv, string, concurrent
from sheet import SheetHandler
from DB import AttendanceDBWriter
from typing import Callable, Union, Tuple, List
import datetime as D

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


class MessageReactions(commands.Cog):
    """Base class. Handles reacting to messages with on_message events."""

    # ATTRIBUTES
    reactionsAllowed=True

    def __init__(self, bot: commands.Bot, cooldown: int, sharedCooldown: bool = False):
        """cooldown is in seconds.
        sharedCooldown: whether to share the channel cooldowns between all instances."""

        self.bot = bot
        self.cooldown = cooldown


    def getChannels(self):
        '''Creates the dict of channels.
        Cannot be done before on_ready'''

        today=D.date.today()
        tempHit=D.datetime(today.year, today.month, today.day)  #add placeholder datetime until there's a hit

        server= self.bot.get_guild(545422040644190220)
        self._channelHits={tChannel : tempHit for tChannel in server.text_channels}  #for rate limiting by channel


class botOverrides(commands.Cog):
    reactionsAllowed=True

    def __init__(self, bot: commands.Bot):
        '''Subclass of Cog to override certain functions of Bot.
        getChannels must be called after on_ready to fully initialise this class'''
        self.bot=bot
        # add attendance Cogs
        #self.bot.add_cog(AttendanceDBWriter(bot))
        self.bot.add_cog(SheetHandler())

        with open("Text Files/trainingWeek.csv") as f:
            for row in csv.reader(f, "excel"):
                trainingWeekRow=row  #this will take the final row as the correct week

        trainingWeekRow=map(int, trainingWeekRow)  #convert all to int

        self.firstTrainingWeek=D.datetime(*trainingWeekRow)

        self.sheetHandler = SheetHandler()


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


    def getChannels(self):
        '''Creates the dict of channels.
        Cannot be done before on_ready'''

        today=D.date.today()
        tempHit=D.datetime(today.year, today.month, today.day)  #add placeholder datetime until there's a hit

        server= self.bot.get_guild(545422040644190220)
        self._channelHits={tChannel : tempHit for tChannel in server.text_channels}  #for rate limiting by channel


    async def checkLastHit(self, msg: Message):
        '''Check if rate limited'''

        #search for channel
        try:
            lastHit=self._channelHits[msg.channel]

        except KeyError:  #message in newly-created channel
            self.getChannels()  #check the channels again
            return False

        except AttributeError:  #channel list not set up yet
            return False

        #check hit
        timenow=D.datetime.now()
        if not ((timenow - lastHit).total_seconds() > 60):                
            return False

        else:
            return True


    @commands.Cog.listener()
    async def on_message(self, inputMessage: Message):
        '''React to certain messages'''

        async def react(self, target: Message, emote: Union[Emoji, int]):
            '''Wrapper for Message.add_reaction.

            Updates self.lastHit'''

            if not isinstance(emote, Emoji):
                emote=self.bot.get_emoji(emote)

            self._channelHits[target.channel]=D.datetime.now()

            return await target.add_reaction(emote)

        pingResponses = responses = [
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
            "<:ping:685193730701000843>"
            ]

        if inputMessage.author==self.bot.user:  #don't respond to self
            return

        #if rate limit passes and reactions not disabled
        if await self.checkLastHit(inputMessage) and self.reactionsAllowed:
            msg=inputMessage.content.lower()

            #check for whitelisted emotes
            if searchWord("php", msg):
                emoteID=662430179129294867

            elif searchWord("ayaya", msg) or "<:w_ayaya:622141714655870982>" in msg:
                emoteID=622141714655870982

            # get angry if ben was pinged
            if 395598378387636234 in [mention.id for mention in msg.mentions]:
                return await msg.channel.send(random.choice(pingResponses))

            # respond to princess sheep
            elif 326713068451004426 == msg.author.id:
              return await msg.channel.send("Here's your bot function. BAAAAAAAAAAAAAAAAAAAA!")

            else:  #if not matched
                return

            #if matched
            async with inputMessage.channel.typing():
                await react(self, inputMessage, emoteID)
                return await inputMessage.channel.send("_", delete_after = 0.0000000000001)  #to end the typing


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
            traceback.print_exception(type(exception), exception,
                                      exception.__traceback__, file=sys.stderr)
            print(f"Occured at: {D.datetime.now().time()}")

            return await ctx.send("Warp energies inhibit me... I cannot do that, My Lord")  #give user feedback if internal error occurs


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

class commandListener():
    '''Class for handling console commands'''

    def help(self):
        '''Display all console commands'''
        print("Commands list:\n")

        for command in self.commands:
            print(command.details)

    
    async def close(self):
        '''Command to throw pummel at bot'''

        print("Ow that hurts... Closing now :,(")

        #acknowledge shutdown
        botChannel=self.bot.get_channel(545818844036464670)
        await botChannel.send('The warp screams in my mind... I must go now')

        try:
            await self.bot.logout()
            self.bot.loop.stop()

        except concurrent.futures.CancelledError:
            input("Press any key to exit")
            sys.exit(0)


    async def listening(self):
        '''always listening for commands from the console'''

        #constantly checking if a command name is inputted
        while True:
            try:
                listenerInput= await self.bot.loop.run_in_executor(None, input)
                listenerInput=listenerInput.lower()

            except KeyboardInterrupt:
                continue

            if listenerInput=="" or listenerInput==" " or listenerInput=="\n":
                continue

            for command in self.commands:
                if listenerInput == command.name:
                    try:
                        if isinstance(command, AsyncCommand):
                            await command.call()

                        else:
                            command.call()

                    except KeyboardInterrupt:
                        continue

                    except Exception as error:
                        print(f'Error occured:', file=sys.stderr)
                        traceback.print_exception(type(error), error,
                                                    error.__traceback__, file=sys.stderr)


    async def scheduleEvent(self):
        '''Take in a function from Discord_Bot.py and schedule it
        Doesn't support arguments'''

        async def getAttendanceArguments(self):
            #get the DTWM guild
            #if URGE rewrite: get 2nd guild
            return self.bot.get_guild(545422040644190220)

        validModules={
            "attendanceWrapper": await getAttendanceArguments(self),
            }

        #set to None if no args
        print(f"Valid modules:\n{list(validModules.keys())}\n")

        #validating
        success=False
        while not success:
            eventInput=input("Enter the name of the module to execute\n")

            success=validateString(eventInput, list(validModules.keys()))
                
        import Discord_Bot
        func=getattr(Discord_Bot, eventInput)
        
        #valdating time
        success=False
        while not success:
            time=input("Enter the time to execute at. Separate multiple times with spaces\n")

            if validateString(time):
                fail=False
                times=time.split(" ")

                for time in times:
                    if len(time) != 4:
                        fail=True

                if not fail:
                    success=True

        asyncio.ensure_future(Discord_Bot.executeOnEvents(AsyncCommand(func, name=eventInput, arguments=validModules[eventInput]),\
           times), loop=self.loop)
        print(f"Event ({eventInput}) scheduled")


    async def __ainit__(self, loop, bot):
        self.commands=[
        AsyncCommand(self.close, name="close",\
           description='Ends the bot rightly. Use for closing the bot without causing problems.'),
        TerminalCommand(os._exit, name="die",\
            description='Instantly kills the bot. For emergencies only. Use "close" outside of emergencies',\
            arguments=(0,)),
        TerminalCommand(self.help, name="help", description="Displays all terminal commands"),
        AsyncCommand(self.scheduleEvent, name="schedule", description="Schedule a function to execute at a custom time/set of times"),
        ]

        self.bot=bot
        self.loop=loop
        
        #printing the terminal commands list to the terminal user
        print('Command listener active... Commands list:')
        for command in self.commands:
            print(command.details)

        await self.listening()

    def __init__(self, bot: commands.Bot):
        '''Loop: the asyncio event loop.
        threads: a list of active threads '''

        loop=asyncio.get_event_loop()

        coro=self.__ainit__(loop, bot)

        bot.loop.create_task(coro)


class NotLeaderError(commands.CommandError):
    '''If the Member is not >=Champion'''
    pass

class RateLimited(commands.CommandError):
    '''For the custom on_message rate limiter'''
    pass

class CommandNotImplementedError(commands.CommandError):
    '''Command partially complete but not disabled for testing reasons'''
    pass
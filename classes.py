#author: benmitchellmtb
from discord.ext import commands
from discord import Forbidden, Message
import threading, os, sys, traceback, asyncio
from typing import Callable, Union, Tuple, List
import asyncio, concurrent
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

class botOverrides(commands.Cog):
    def __init__(self, bot: commands.Bot):
        '''Subclass of Cog to override certain functions of Bot'''
        self.bot=bot

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

        #if bot can't access the channel
        elif isinstance(exception, Forbidden):
            return await ctx.send("I can't access one or more of those channels TwT")

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
        botChannel=ctx.bot.get_channel(545818844036464670)
        await botChannel.send('The warp screams in my mind... I must go now')

        self.bot.loop.stop()


    async def listening(self):
        '''always listening for commands from the console'''

        #constantly checking if a command name is inputted
        while True:
            try:
                listenerInput= await self.bot.loop.run_in_executor(None, input)
                #listenerInput=input()
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


class NoArgsPassed(Exception):
    pass
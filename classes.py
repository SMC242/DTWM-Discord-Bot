from discord.ext import commands
import threading, os, sys, traceback, asyncio
from typing import Callable, Union, Tuple, List
import asyncio

bot=commands.Bot(command_prefix="ab!")
def createListFromFile(filePath, type=str):
    '''Returns a list populated by parsed lines from a text file
    filePath: string path of the file to be read
    varList: output list
    type: the type of variables to be read (str, int, float, etc)'''

    with open("Text Files/"+filePath) as f:
       varList=[type((line.strip("\n")).lower()) for line in f]
    
    return varList  

class botOverrides(commands.Bot):
    @bot.listen()
    async def on_command_error(ctx, exception):
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

        # NOTE: This is the default error handling behaviour, which is kept for
        # development purposes for the time being, but will be disabled at a later
        # point
        print(f'Ignoring exception in command {ctx.command}:', file=sys.stderr)
        traceback.print_exception(type(exception), exception,
                                  exception.__traceback__, file=sys.stderr)

        #if command on cooldown
        if isinstance(exception, commands.CommandOnCooldown):
          await ctx.send(f"Hold on, My Lord. I must gather my energy before another\nTry again in {int(exception.retry_after)} seconds!")

        #if command is unknown
        elif isinstance(exception, commands.CommandNotFound):
            #building the invoked command
            invokedCommand: str=None
            for char in ctx.message:
                if char==" ":
                    break

                else:
                    invokedCommand.join(char)

            await ctx.send(f'Sorry My Lord, the archives do not know of this "{invokedCommand}" you speak of')

        #if bot can't access the channel
        elif isinstance(exception, Forbidden):
            await ctx.send("I can't access one or more of those channels TwT")

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
        '''Returns a coroutine for the func and its args'''
        return await self.func(self.arguments)

    @property
    def coro(self):
        return self.func(self.arguments)


class ThreadCommand(TerminalCommand):
    def call(self):
        '''Returns an instance of Threading.Thread for the function and its args'''

        return threading.Thread(target=self.func, args=self.arguments, name=self.name)

class commandListener():
    '''Class for handling commands'''
    #commands={
    #    'close' : 'Ends the bot rightly. Use for closing the bot without causing problems.',
    #    'die' : 'Instantly kills the bot. For emergencies only. Use "close" outside of emergencies',
    #    'help' : 'Displays the commands list'
    #    }

    def help():
        for command in self.commands:
            command.showDetails()


    stopThreads=False

    def __init__(self, loop, threads):
        '''Loop: the asyncio event loop.
        threads: a list of active threads'''

        self.commands=[
        TerminalCommand(self.close, name="close",\
           description='Ends the bot rightly. Use for closing the bot without causing problems.'),
        TerminalCommand(os._exit, name="die",\
            description='Instantly kills the bot. For emergencies only. Use "close" outside of emergencies',\
            arguments=(0,)),
        TerminalCommand(self.help, name="help", description="Displays all terminal commands"),
        ]

        self.loop=loop
        self.threads=threads
        
        #printing the terminal commands list to the terminal user
        print('Command listener active... Commands list:')
        for command in self.commands:
            print(command.details)

        commandListenerThread=threading.Thread(target=commandListener.listening, args=[self], name="commandListener")
        commandListenerThread.start()

    def close(self):
            '''Command to throw pummel at bot'''

            self.loop.stop()
            self.stopThreads=True


    def listening(self):
        '''always listening for commands from the console'''

        listenerInput=input().lower()
         
        #constantly checking if a command name is inputted
        while True:
            for command in self.commands:
                if listenerInput == command.name:
                    try:
                        command.call()
                    except Exception as error:
                        print(error.__repr__())
                        print("Fatal error. Command listener closing")
                        break
                else:
                    continue

            if self.stopThreads:
                #gives each thread 3 seconds to finish
                #kills them if they don't finish in that time
                for thread in self.threads:
                    thread.join(3)
                
                sys.exit(0)

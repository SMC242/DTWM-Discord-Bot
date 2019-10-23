from discord.ext import commands
import threading, os, sys, traceback, asyncio

def createListFromFile(filePath, type=str):
    '''Returns a list populated by parsed lines from a text file
    filePath: string path of the file to be read
    varList: output list
    type: the type of variables to be read (str, int, float, etc)'''

    with open("Text Files/"+filePath) as f:
       varList=[type((line.strip("\n")).lower()) for line in f]
    
    return varList  
bot=commands.Bot(command_prefix="ab!")

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

        #This is the first line where non-standard things happen
        if isinstance(exception, commands.CommandOnCooldown):
          await ctx.send(f"Hold on, My Lord. I must gather my energy before another\nTry again in {int(exception.retry_after)} seconds!")

        if isinstance(exception, Forbidden):
            await ctx.send("I can't access one or more of those channels TwT")



class commandListener():
    commands={
        'close' : 'Ends the bot rightly. Use for closing the bot without causing problems.',
        'die' : '''Instantly kills the bot. For emergencies only. Use "close" outside of emergencies''',
        'help' : 'Displays the commands list'
        }

    stopThreads=False

    def __init__(self, loop, threads):
        self.loop=loop
        self.threads=threads
        
        print('Command listener active... Commands list:')
        print(commandListener.commands)

        stopThreadsListener=threading.Thread(target=commandListener.run, args=[self], name="stopThreadsListener")
        stopThreadsListener.start()

        commandListenerThread=threading.Thread(target=commandListener.listening, args=[self], name="commandListener")
        commandListenerThread.start()
        self.threads.insert(0, commandListenerThread)


    def run(self):
        while True:
            if self.stopThreads is True:
                #gives each thread 3 seconds to finish
                #kills them if they don't finish in that time
                for thread in self.threads:
                    thread.join(3)

                sys.exit(0)

    def listening(self):
        '''always listening for commands from the console'''
        def close(self): #command to throw pummel at bot
            self.loop.stop()
            self.stopThreads=True

        listenerInput=input()
        listenerInput=listenerInput.lower()

        #3D list of command names, callbacks, and actual arguments
        commands=["die", "close", "reset"],
        [os._exit, close],
        [0, self]
         
        while True:

            for i, command in enumerate(commands):
                if listenerInput == command:
                    commands[1]

            

            if listenerInput == "die": #command to kill the bot quickly
                #has to be first for extra SPEEEEEEEEED
                os._exit(0)

            elif listenerInput == "close": #command to throw pummel at bot
                self.loop.stop()
                self.stopThreads=True

            elif listenerInput

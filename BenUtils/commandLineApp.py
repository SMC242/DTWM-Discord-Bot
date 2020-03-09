"""A bare-bones terminal command listener"""

from .callbacks import Callback
from typing import Dict

class CommandLineApp:
    """A bare-bones terminal command listener
    
    Default commands:
        ?HELP : display all commands and their __doc__s
        
    ATTRIBUTES
    commands: str : Callback dict
        The valid commands.
    closeName: str
        The name of the command to stop the listener.
    startNow: bool
        Whether to start upon instantiation or wait for .run()
    inputMessage: str
        The message to be displayed to ask the user to input.
    closeMessage: str
        The message to be displayed when the listener dies.
    helpName: str
        The name of the help command.
    caseSensitive: bool
        Whether to check case.
    _running: bool property
        The running status.
    """

    # ATTRIBUTES
    _running = False


    def __init__(self, commands: Dict[str, Callback], closeName: str = "?CLOSE",
        startNow: bool = False, inputMessage: str = "Input Command.",
        closeMessage: str = "Command listener closing...", caseSensitive: bool = False,
        helpName: str = "?HELP"):
        """
        ARGUMENTS
        commands:
            The valid commands. Format: {name : callback}
        closeName:
            The name of the command to stop the listener.
        startNow:
            Whether to start upon instantiation or wait for .run()
        inputMessage:
            The message to be displayed to ask the user to input.
        closeMessage:
            The message to be displayed when the listener dies.
        caseSensitive:
            Whether to check cases.
        helpName:

        """
        
        self.commands = commands
        self.closeName = closeName
        self.inputMessage = inputMessage
        self.closeMessage = closeMessage
        self.helpName = helpName
        self.caseSensitive = caseSensitive

        # convert all command names to lowercase if case sensitivity is disabled
        if not caseSensitive:
            self.closeName = closeName.lower()
            self.helpName = helpName.lower()

            self.commands = {key.lower() : value for key, value in commands.items()}

        if startNow:
            self.run()


    def run(self):
        """Run listener until stopped. Stop with .die() or KeyboardInterrupt"""

        self._running = True
        while self.running:
            answer = input(f"{self.inputMessage}\n")
            if not self.caseSensitive:
                answer = answer.lower()

            # check if valid command
            try:
                self.commands[answer]()

            # The command is invalid
            except KeyError:
                # check for help and close
                if answer == self.helpName:
                    self.help()

                elif answer == self.closeName:
                    self.die()

                else:
                    pass

        # give user feedback when listener dies
        else:
            print(f"{self.closeMessage}\n")


    def help(self):
        """Show __doc__ of all commands"""

        # print user's commands
        for name, callback in self.commands.items():
            for doc in callback.__doc__:
                print(f"Name: {name}\nDescription: {doc}\n")

        # print forced commands
        for name, value in ((self.closeName, self.die.__doc__), (self.helpName, "Display this message")):
            print(f"Name: {name}\nDescription: {value}\n")


    def die(self):
        """Stop the command listener"""

        self._running = False


    @property
    def running(self):
        """Get the listener activity status"""

        return self._running
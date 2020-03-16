"""Callback classes"""

from typing import Generator, Coroutine, Callable, Union, Tuple, List
from inspect import iscoroutinefunction
import asyncio, threading

class BaseCallback:
    """
    Callbacks that are normal functions
    
    ATTRIBUTES
    _func: callable
        The function to be called.
    _args: tuple
        The positional arguments for _func.
    _kwargs: dict
        The keyword arguments for _func.
    _name:  str property
        The name describing what _func does.
    __doc__: str
        The description of _func.
        NOTE: only custom functions' .__doc__s can be written to. 
        Errors due to writing to __doc__ will be silenced.
    """

    def __init__(self, func: Callable, docString: str = None, name: str = None, args = (), kwargs = {}):
        """
        ARGUMENTS
        func:
            The function to execute.
        docString:
            Override the docstring of func.
        name:
            The name of the object. Should describe what the callback does.
        *args, **kwargs:
            The arguments of func.
        """

        self._args = args
        self._kwargs = kwargs
        self._func = func
        self._name = str(name)

        if docString:
            try:
                self._func.__doc__ = docString

            except AttributeError:  # __doc__ isn't writable
                pass

        # ensure docstring
        if not self._func.__doc__:
            self._func.__doc__ = ""


    def __call__(self):
        """Call _func"""

        # behave normally for simple callbacks, but act as an ABC otherwise
        if self.__class__ == BaseCallback:
            return self._func(*self._args, **self._kwargs)

        else:
            raise NotImplementedError()


    @property
    def __doc__(self) -> str:
        """Get the description of _func"""

        return self._func.__doc__


    @property
    def name(self) -> str:
        """Get the _name of this instance"""

        return self._name


class ThreadCallback(BaseCallback):
    """
    Callbacks that spawn threads.
    
    ATTRIBUTES
    _daemon: bool
        Flag for whether it's a daemon thread.
    thread: threading.Thread property
        threading.Thread instance made from _func, _args, _kwargs. Creates if not exists.
    _thread: threading.Thread
        The threading.Thread instance.
    """

    def __init__(self, func: Callable, daemon: bool, *args, **kwargs):
        """
        ARGUMENTS
        daemon:
            Flag for whether it's a daemon thread.
        """

        super().__init__(self, func, args = args, kwargs = kwargs)

        self._daemon = daemon


    def __call__(self):
        """Spawn a thread for func with args and kwargs"""

        return self.thread.run()


    @property
    def thread(self) -> threading.Thread:
        """Get self as a threading.Thread"""

        if not self._thread:
            self._thread = threading.Thread(target = self._func, args = self._args,
                kwargs = self._kwargs, daemon = self._daemon)

        return self._thread


class AsyncCallback(BaseCallback):
    """
    Callbacks that run asynchronously.
    
    ATTRIBUTES
    eventLoop: asyncio.AbstractEventLoop
        The event loop that coro will be executed on.
    _coro: coroutine property
        The coroutine made from the input func, args, and kwargs.
    """

    def __init__(self, func: Union[Callable, Coroutine], *args, **kwargs):
        assert iscoroutinefunction(func)  # ensure an async function was passed

        super().__init__(self, func, args = args, kwargs = kwargs)

        self.eventLoop = asyncio.get_event_loop()
        self._coro = self._func(self_.args, self._kwargs)


    def __call__(self):
        """Call func now or return it as a coroutine"""

        self.eventLoop.add_task(self.coro)


    @property
    def coro(self) -> Coroutine:
        """Gets func as a coroutine"""

        return self._coro


    @property
    def coroutine(self) -> Coroutine:  # 2nd alias for coro
        """Gets func as a coroutine"""

        return self._coro


# in-dev. The flags need to be revised as they're awkward to input
# example: Callback(((print, False),))
class Callback:
    """
    High level callback class. Handles converting functions, coroutines, and threads to spawn to callbacks.
    
    Trade off from performance for easy handling of callbacks and aggregating functions into 1 callback.
    When performance is more important, use the specific callback classes.
    
    ATTRIBUTES
    calls: list of callable
        The callbacks.
    __doc__: str generator property
        All the __doc__s of calls.
    names: str generator property
        All the _names of calls.
    """

    # ATTRIBUTES
    calls: List[BaseCallback] = []


    def __init__(self, funcs: Tuple[Tuple[Callable, bool],], arguments: List[tuple,] = None,
            daemon: bool = True, keywords: List[dict,] = None):
        """
        NOTE: Pass an empty tuple/dict if a function has no args/kwargs but other functions do.
        E.G funcs = [func1, func2], args = (tuple(), (True, False)), kwargs = ({arg : True}, {})

        ARGUMENTS
        funcs:
            The function(s) to convert and whether it's to be a thread.
            Format: [(func, isThread), (func, isThread),].
            If async or normal: isThread = False
        arguments:
            The positional arguments of the funcs.
        daemon:
            Option to spawn a daemon thread.
        keywords:
            The keyword arguments of funcs. 
        """ 

        # ensure args and kwargs can be iterated over in parallel to funcs
        funcsLength = len(funcs)
        if not keywords:
            keywords = [ {} ] * funcsLength

        if not arguments:
            arguments = [ () ] * funcsLength

        assert len(keywords) == funcsLength == len(arguments)

        # ensure flags
        for pair in funcs:
            try:
                pair[1]

            except (IndexError, TypeError):
                raise ValueError("func flags are not set.")
        
        # create Callback objects
        for i, pair in enumerate(funcs):
            func, flag, *_ = pair  # discard unexpected arguments
            args, kwargs = arguments[i], keywords[i]

            if flag:
                self.calls.append(ThreadCallback(func, daemon, args = args, kwargs = kwargs))

            elif iscoroutinefunction(func):
                self.calls.append(AsyncCallback(func, args = args, kwargs = kwargs))

            else:
                self.calls.append(BaseCallback(func, args = args, kwargs = kwargs))

        
    def __call__(self) -> List[tuple]:
        """Execute the callback(s) and returns their results"""

        return [call() for call in self.calls]


    @property
    def __doc__(self) -> Generator[str, None, None]:
        """Generator for the __doc__s of _funcs"""

        return (call.__doc__ for call in self.calls)


    @property
    def names(self) -> Generator[str, None, None]:
        """Generator for the _names of calls"""

        return (call.name for call in self.calls)
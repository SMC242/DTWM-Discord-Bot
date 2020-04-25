"""Callback classes"""

from typing import Generator, Coroutine, Callable, Union, Tuple, List, Hashable, Dict
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
    _doc: str
        The docstring override.
    __doc__: str
        The description of _func.
    """

    def __init__(self, func: Callable, docString: str = None, name: str = None, args = (), kwargs = {}):
        """
        ARGUMENTS
        func:
            The function to execute.
        docString:
            Override the docstring of func.
            Defaults to the function's docstring.
        name:
            The name of the object. Should describe what the callback does.
        *args, **kwargs:
            The arguments of func.
        """

        self._args = args
        self._kwargs = kwargs
        self._func = func
        self._name = str(name)
        self._doc = docString


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

        if self._doc:  return self._doc
            
        else: return self._func.__doc__


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


    def __init__(self, funcs: Dict[Callable, dict]):
        """
        ARGUMENTS
        funcs:
            dict of function : settings dict.
            settings dict should have these keys:
                args: the tuple of arguments for the function.
                kwargs: the dict of keyword arguments for the function.
                type: string stating whether it's a standard, async, or thread function.
                    Must be within ('standard', 'async', 'thread').
                daemon: boolean stating whether it's a daemon thread.
        """ 

        def setToDefault(target: dict, key: Hashable, defaultValue: Any) -> dict:
            """
            For each key in `target`, set `value[key]` to defaultValue
            if it's falsy or there's a KeyError."""

            # iterate over top level keys
            for func, settings in target.items():
                try:
                    # check value of each key for a falsy value
                    if not settings[key]:
                        target[func][key] = defaultValue

                # if the target key doesn't exist, set it to the default value
                except KeyError:
                    target[func][key] = defaultValue

            return target

        
        # ensure all keys were passed
        for set_ in ("args", tuple(), "kwargs", dict(),
            "daemon", False, "type", "standard"):
            funcs = setToDefault(funcs, set_[0], set_[1])

        # create calls
        for func, settings in funcs.items():
            # choose the callback type
            type_ = settings["type"]
            if type_ == "standard":
                chosenType = BaseCallback
                
            elif type_ == "async":
                chosenType = AsyncCallback

            elif type_ == "thread":
                chosenType = ThreadCallback

            else:
                raise ValueError(f"Invalid type ({type_})")

            # create instance
            self.calls.append(chosenType(func, args = settings["args"], kwargs = settings["kwargs"]))
        

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
"""This module handles temporarily storing unique values
    """

from typing import TypeVar
import aiohttp
import traceback
from typing import Coroutine, ByteString, Hashable, Callable, Tuple, Iterable, Any, Optional, Dict, List, NewType
from datetime import datetime
from json import dumps
from asyncio import get_event_loop, sleep as async_sleep, gather
import asyncio
from collections import abc, OrderedDict
from functools import wraps


class download_resource:
    """Context manager to download and return a file handler asynchronously.
    Removes the .

    ATTRIBUTES
        url (str): the target URL
        limit (int): the number of bytes to read
        reponse (aiohttp.ClientResponse): the response from the
    """

    def __init__(self, url: str, limit: int = None):
        """Args:
        url (str): The URL that identifies the resource to download.
        limit (int): the number of bytes to read. Defaults to the whole file"""
        self.url = url
        self.limit = limit
        self.response: aiohttp.ClientResponse = None

    async def __aenter__(self) -> 'download_resource':
        """Returns:
        None: the download failed.
        download_resources object: the download was successful."""
        # request the resource
        async with aiohttp.ClientSession() as session:
            # keep the reponse object around until exit
            try:
                self.response = await session.get(self.url)
            except aiohttp.client_exceptions.InvalidURL:  # log error if a weird URL is passed
                print(f"Bad URL: {self.url}")

            if self.response.status != 200:  # ensure that the request passed
                return None
            # get the number of bytes to read if no limit passed
            self.limit = self.limit or int(
                self.response.headers["Content-Length"])
            return self

    @property
    def content(self) -> Coroutine[ByteString, None, None]:
        """Return a coroutine that outputs the number of bytes requested."""
        # it has to be this way because passing -1 wasn't working
        if self.limit:
            return self.response.content.read(self.limit)
        else:
            return self.response.content.read()

    async def __aexit__(self, *args):
        """Handle a bad response if it happened. Also close the connection."""
        # handle errors
        if args[0]:
            traceback.print_exc()
        # close the response connection
        self.response.close()


# Type aliases
event_args = Callable[['AsyncCache', Hashable, Any], Any]


class AsyncCache:
    """
    Caches values until the cache overflows

    NOTE: `event_args` = Callable[['AsyncCache', collections.abc.Hashable, `typing.Any`]
                                  `typing.Any`]
    # Attributes
    `_cache (private Dict[Hashable, Any]`):
        The currently cached items.
        Items will be removed when `max_items` is exceeded.

    `max_items (int)`:
        The maximum number of items in `_cache`.

    `on_add_pass (event_args)`:
        The function to call after a unique item is added to the cache.
        Arguments: (instance of `AsyncCache`, (the key that was added, the value that was added))

    `on_add_fail (event_args)`:
        The function to call after a duplicate item was attempted to be added to the cache.
        Arguments: (instance of `AsyncCache`, (the key that wasn't added, the value that wasn't added))

    `on_remove (event_args)`:
        The function to call after an item is removed from the cache.
        Arguments: (instance of `AsyncCache`, the key-value pair that was removed from the cache)

    `_event_loop (asyncio.AbstractEventLoop)`:
        The event loop that is used to run the `on_{events}`

    `_cleaning (bool)`:
        Whether the cleaning task is running.
        Used to prevent multiple calls of `clean()` and wiping the cache as a result.
    """

    def __init__(self, max_items: int = 128,
                 on_add_pass: event_args = None,
                 on_add_fail: event_args = None,
                 on_remove: event_args = None,
                 ):
        self._cache: OrderedDict[Hashable, Any] = OrderedDict()
        self._cleaning: bool = False
        self.max_items = max_items
        on_add_pass = on_add_pass or self.on_add_pass
        on_add_fail = on_add_fail or self.on_add_fail
        on_remove = on_remove or self.on_remove

        self._event_loop = asyncio.get_event_loop()

    def _call(self, event: Callable, *args, **kwargs) -> asyncio.Task:
        """
        # (method) _call(event, )
        Create and add a task from the event.

        # Parameters
            - `event`: `Callable`
                The event function to call

        # Returns
            `Task`:
                The Task that wraps the event
        """
        @wraps(event)
        async def inner():
            return event(self, *args, **kwargs)
        return self._event_loop.create_task(inner())

    def on_add(self, key: Hashable, value: Any) -> asyncio.Task:
        """
        # (method) on_add(key, value, )
        Add a pair to the cache. Will call `on_add_pass/fail` asynchronously.
        NOTE: this is the internal interface for adding things.

        # Parameters
            - `key`: `Hashable`
                The key to add
            - `value`: `Any`
                The value to add
        """
        if key in self._cache:  # key isn't unique
            task = self._call(self.on_add_fail, key, value)
        self._cache[key] = value  # key is unique --> add it
        task = self._call(self.on_add_pass, key, value)

        # check if the cache is too big
        if len(self._cache) >= self.max_items and not self._cleaning:
            # the cleaning check is to prevent a bug where `clean` was called repeatedly
            # and wiped the cache
            self._cleaning = True
            self._event_loop.create_task(self.clean())

        return task

    async def clean(self):
        """
        ### (method) clean()
        Remove the older half of the cache.
        """
        max = int(0.5 * len(self._cache))
        pairs = list(self._cache.items())
        new_cache = OrderedDict({key: value for key, value in
                                 pairs[max:]})
        old_cache = OrderedDict({key: value for key, value in
                                 pairs[:max]})
        self._cache.clear()  # remove all references to the dict's old values
        self._cache = new_cache
        self._cleaning = False

        # call on_remove
        return asyncio.gather(
            *[self._call(self.on_remove, *pair) for pair in old_cache.items()]
        )

    def append(self, key: Hashable, value: Any) -> asyncio.Task:
        """Add the key and value to the cache."""
        return self.on_add(key, value)

    def extend(self, pairs: Dict[Hashable, Any]) -> List[asyncio.Task]:
        """Add multiple pairs to the cache"""
        return asyncio.gather(*[self.on_add(*pair) for pair in pairs.items()])

    @property
    def cache(self) -> Dict[Hashable, Any]:
        """Get the current cache"""
        return self._cache

    # default event callbacks
    @staticmethod
    def on_add_pass(self, key: Hashable, value: Any):
        """This will be called after a unique key is added to the cache.
        Does nothing by default."""
        pass

    @staticmethod
    def on_add_fail(self, key: Hashable, value, Any):
        """This will be called after a duplicate key is not added to the cache.
        Does nothing by default."""
        pass

    @staticmethod
    def on_remove(self, key: Hashable, value: Any):
        """This will be called after a key is removed from the cache.
        Does nothing by default."""
        pass

    # beware ye, only magic methods are beyond this place
    def __add__(self, pair: Tuple[Hashable, Any]) -> asyncio.Task:
        """Add the key and value to the cache with the `cache + (key, value)` syntax."""
        return self.on_add(*pair)

    def __sub__(self, key: Hashable) -> asyncio.Task:
        """Remove the key from the cache with the `cache - key` syntax"""
        value = self._cache[key]
        del self._cache[key]
        return self._call(self.on_remove, key, value)

    def __getitem__(self, key: Hashable) -> Optional[Any]:
        """Use the `cache[key]` syntax to access values."""
        try:
            return self._cache[key]
        except KeyError:
            return None

    def __setitem__(self, key: Hashable, value: Any) -> asyncio.Task:
        """Add an item to the cache using the `cache[key] = value` syntax."""
        return self.on_add(key, value)

    def __delitem__(self, key: Hashable):
        """Delete a key from the cache using the `del cache[key]` syntax"""
        value = self._cache[key]
        del self._cache[key]
        return self._call(self.on_remove, key, value)

    def __len__(self) -> int:
        """Get the number of pairs in the cache."""
        return len(self._cache)

    def __iter__(self) -> Iterable[Tuple[Hashable, Any]]:
        """Get an iterator for self._cache"""
        return iter(self._cache.items())

    def __contains__(self, key: Hashable) -> bool:
        """Check if a key is in the cache"""
        return key in self._cache

    def __repr__(self) -> str:
        """Get the attributes of the cache as a string"""
        return (
            f"Utils.caching.{self.__class__}(max_items = {self.max_items}, "
            f"on_add_pass = {self.on_add_pass}, on_add_fail = {self.on_add_fail}, "
            f"on_remove = {self.on_remove})\nWith private attributes:"
            f"_event_loop = {self._event_loop}, _cleaning = {self._cleaning},"
            f"_cache = {self._cache}"
        )

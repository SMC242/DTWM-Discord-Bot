"""This module handles temporarily storing unique values
    """

import aiohttp
import traceback
from typing import Coroutine, ByteString, Hashable, Callable, Tuple, Iterable, Any, Optional, Dict, List
from datetime import datetime
from json import dumps
from asyncio import get_event_loop, sleep as async_sleep, gather
import asyncio
from collections import abc
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
            self.response = await session.get(self.url)
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


class Cache:
    """Keeps values around for a set period and checks if values are in the cache.

    Attributes
    ----
        `_cached` : `Dict[Hashable, datetime]`
            The currently held values.
            Old values will be removed after `period`

        `period : float`
            The number of days that something should be cached.

        `check_period : float`
            The number of hours between each cache clean-up.

        `_running : bool`
            Whether the clean-up loop is currently active.

        `_clean_up_loop : asyncio.Task`
            The clean-up loop. You should stop this with `stop()`.
            It can be restarted with `start()`

        `on_unique_pass : Coroutine[Tuple['Cache', Any], Any]`
            The function to call before something is added to the cache.
            It should take in the self and the new value as its arguments.
            Defaults to doing nothing.

        `on_unique_fail : Coroutine[Tuple['Cache', Any], Any]`
            The function to call after attempting to add an item
            to the cache that is already cached.
            It should take in the self and the new value as its arguments.
            Defaults to not adding the item.

        `on_remove : Callable[Tuple['Cache', Tuple[Any, datetime]], Any]`
            The function to call after deleting an item.
            It should take in the self and the key-value pair as its arguments.
            Defaults to doing nothing.

        ayaya (Dict[Any, Any]):
            v5
    ---
    """

    def __init__(self, period: float = 2, check_period: float = 12,
                 on_unique_pass: Callable[['Cache', Any], Any] = None,
                 on_unique_fail: Callable[['Cache', Any], Any] = None,
                 on_remove: Callable[['Cache', Tuple[Any, datetime]], Any] = None,
                 ):
        """
        Parameters:
        ---
            period (float): the number of days that something should be cached.

            check_period (float): the number of hours between each cache clean-up.

            on_unique_pass (Callable[Tuple['Cache', Any], Any]): the function to call before something is added to the cache.
                It should take in the self and the new value as its arguments.
                Defaults to doing nothing.

            on_unique_fail (Callable[Tuple['Cache', Any], Any]): the function to call after attempting to add an item
                to the cache that is already cached.
                It should take in the self and the new value as its arguments.
                Defaults to doing nothing.

            on_remove (Callable[Tuple['Cache', Tuple[Any, datetime]], Any]): the function to call after deleting an item.
                It should take in the self and the key-value pair as its arguments.
                Defaults to doing nothing.
        ---
        """

        self._cached: Dict[Hashable, datetime] = {}
        self.period = period
        self.check_period = check_period
        # set the events to their defaults
        self.on_unique_pass = on_unique_pass or self._on_unique_pass
        self.on_unique_fail = on_unique_fail or self._on_unique_fail
        self.on_remove = on_remove or self._on_remove
        # start the cleanup loop
        self._clean_up_loop = None
        self._running = False
        self._event_loop = asyncio.get_event_loop()
        self._event_loop.create_task(self.start())

    @property
    def cached(self) -> dict:
        """Get the current cache

        Returns:
            dict: the current cache
        """
        return self._cached

    @cached.setter
    def cached(self, new_cache: dict):
        """Overwrite the whole cache.
        Will call `on_remove` for each pair in the cache.
        `on_add` will be called for each key added.
        Use the `+` operator, dict-like access, or the `append` method for adding single values.
        Use `extend`  for adding multiple values.

        Args:
            new_cache (dict): The new value of the cache.
        """
        # call on_remove
        map(lambda pair: self.on_remove(self, pair),
            self._cached.items())

        # call on_add
        self._cached.clear()
        map(lambda key: self.on_add(self, key),
            new_cache)

    def on_add(self, key: Hashable) -> bool:
        """Attempt to add the key to the cache. If it's already there, call `on_unique_fail`,
        else call `on_unique_pass`. 
        NOTE: handles adding the key. Do not try to add the key after calling this function.

        Args:
            key (Hashable): The key to add

        Returns:
            bool: whether the key was unique.
        """
        if key in self._cached:
            self.on_unique_fail(self, key)
            return False  # key not unique
        self._cached[key] = datetime.now()
        self.on_unique_pass(self, key)
        return True  # key is unique

    def append(self, key: Hashable):
        """Add a single key to the cache."""
        self.on_add(key)

    def extend(self, keys: Iterable[Hashable]):
        """Add multiple keys to the cache and call `on_add` for each key."""
        # must be converted to list or else the output seems to get eaten by map()
        list(map(lambda key: self.on_add(key),
                 keys))

    async def _clean_up_cache(self):
        """Remove cache items that are more than `period` days old.
        Is called every `check_period` hours.
        """
        while self._running:
            # remove any values older than `period`
            now = datetime.now()
            for key, timestamp in self._cached.items():
                if (now - timestamp).days >= self.period:
                    del self._cached[key]
                self.on_remove(self, key)

            # 1 hour * 60 = 60 minutes,  60 minutes * 60 = 3600 seconds
            await async_sleep(self.period * 60**2)

    async def stop(self, timeout_seconds: float = 10):
        """Stop the clean up cache loop.

        Args:
            timeout_seconds (float): how long to wait before forcefully stopping the loop.
        """
        self._running = False
        async_sleep(timeout_seconds)  # wait for the loop to end on its own
        if not self._clean_up_loop.done():  # force close it if it doesn't stop on its own
            self._clean_up_loop.cancel()

    async def start(self):
        """Start the cache clean-up loop"""
        self._running = True
        self._event_loop.create_task(self._clean_up_cache())

    @property
    def running(self) -> bool:
        """Get whether the clean up task is still running

        Returns:
            bool: Whether the clean-up task is running
        """
        return self._running

    def cache_repr(self) -> str:
        """Get the current cache as a pretty JSON string

        Returns:
            str: the prettified JSON-format representation of the cache
        """
        return dumps(self._cached, indent=4, default=str)

    # default event callbacks
    @staticmethod
    def on_unique_pass(self, key: Hashable):
        """The default on_unique_pass callback does nothing.
        It will be called after attempting to add a unique value to the cache."""
        pass

    @staticmethod
    def on_unique_fail(self, key: Hashable):
        """The default on_unique_fail callback does nothing.
        It will be called after attempting to add a non-duplicate value to the cache."""
        pass

    @staticmethod
    def on_remove(self, pair: Tuple[Hashable, datetime]):
        """The default on_remove callback does nothing.
        It will be called after a key is removed from the cache."""
        pass

    # magic method boilerplate from here on. There is nothing interesting below.

    def __add__(self, key: Hashable):
        """Add a key to the cache.

        Args:
            key (Hashable): the key to add to the cache.
        """
        self.append(key)

    def __contains__(self, key: Hashable) -> bool:
        """Checks whether the key is in the cache

        Args:
            key (Hashable): The key to look for

        Returns:
            bool: Whether the key is in the cache
        """
        return key in self._cached

    def __len__(self) -> int:
        """Count the number of keys in the cache."""
        return len(self._cached)

    def __getitem__(self, key: Hashable) -> Optional[datetime]:
        """Get the timestamp of a key in the cache

        Args:
            key (Hashable): The key to fetch

        Returns:
            Optional[datetime]: The timestamp of the key.
                                None will be returned if the key doesn't exist
        """
        try:
            return self._cached[key]
        except KeyError:
            return None

    def __delitem__(self, key: Hashable):
        """Delete an item from the cache using this syntax: `del cache["key"]`

        Args:
            key (Hashable): The key to remove

        Raises:
            KeyError: the key wasn't in the cache
        """
        del self._cached[key]

    def __iter__(self) -> Iterable[Tuple[str, datetime]]:
        """Allows for each iteration over the cache keys and values."""
        return iter(self._cached.items())

    def __repr__(self) -> str:
        """Get the attributes of this object as a string.
        """
        return (f"Utils.caching.{self.__class__.__name__}(period = {self.period}, "
                f"on_unique_pass = {self.on_unique_pass}, "
                f"on_unique_fail = {self.on_unique_fail}, "
                f"on_remove = {self.on_remove})")


class AsyncCache(Cache):
    """An asynchronous version of `Cache` that is based on timestamps rather than number of pairs.
    The event callbacks will be called asynchronously.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def cached(self) -> dict:
        return super().cached

    @cached.setter
    def cached(self, new_cache: dict) -> asyncio.Task:
        """Overwrite the whole cache.
        Will call `on_remove` for each pair in the cache asynchronously.
        `on_add` will be called for each key added asynchronously.
        Use the `+` operator, dict-like access, or the `append` method for adding single values.
        Use `extend`  for adding multiple values.

        Args:
            new_cache (dict): The new value of the cache.

        Returns:
            The Task running asyncio.gather on all of the `on_remove` and `on_add` Tasks.
        """
        # call on_remove
        remove_tasks = list(map(lambda pair: self.on_remove(self, pair),
                                self._cached.items()))

        # call on_add
        self._cached.clear()
        add_tasks = map(lambda key: self.on_add(key),
                        new_cache)

        return self._event_loop.create_task(
            asyncio.gather(*remove_tasks, *add_tasks, loop=self._event_loop)
        )

    def on_add(self, key: Hashable) -> Tuple[asyncio.Task, bool]:
        """Attempt to add the key to the cache. If it's already there, call `on_unique_fail`,
        else call `on_unique_pass`. 
        NOTE: handles adding the key. Do not try to add the key after calling this function.

        Args:
            key (Hashable): The key to add

        Returns:
            The awaitable to wait for this method to finish and whether the key is unique.
        """
        if key in self._cached:
            # duplicate key
            return (self._call_event_cb(self.on_unique_fail, self, key), False)
        self._cached[key] = datetime.now()
        # key is unique
        return (self._call_event_cb(self.on_unique_pass, self, key), True)

    def append(self, key: Hashable):
        """Add a single key to the cache."""
        self.on_add(key)

    def extend(self, keys: Iterable[Hashable]):
        """Add multiple keys to the cache and call `on_add` for each key."""
        map(lambda key: self.on_add(key),
            keys)

    def _call_event_cb(self, event_cb: Callable[[Any], Any], *args, **kwargs) -> asyncio.Task:
        """Asynchronously call the event callback.

        Args:
            event_cb (Callable[Any, Any]): The event callback to be called
        """
        @wraps(event_cb)
        async def inner():
            return event_cb(*args, **kwargs)
        return self._event_loop.create_task(inner())


if __name__ == "__main__":
    async def main():
        i = Cache(
            0.000231481,  # 20 sec
            0.000115741,  # 10 sec
            lambda cache, key: print(f"{key} added"),
            lambda cache, key: print(f"{key} failed to add"),
            lambda cache, key: print(f"{key} removed"),
        )
        i.append("ayaya")
        i.extend(("UmU", "v5", "thing"))
        del i["ayaya"]
        print(i["ayaya"])
        i + "new_key"
        print(i)
        print(i.cache_repr())
        print(len(i))
        for pair in i:
            print(pair)
        await async_sleep(20)
        print(i.cache_repr())
        i.cached = {"1": datetime.now(), "2": datetime.now()}
        print(i.cache_repr())
        print("1" in i)
        print("end test")
    # get_event_loop().run_until_complete(main())
    import time
    i = Cache(
        0.000231481,  # 20 sec
        0.000115741,  # 10 sec
        lambda cache, key: print(f"{key} added"),
        lambda cache, key: print(f"{key} failed to add"),
        lambda cache, key: print(f"{key} removed"),
    )
    i.append("ayaya")
    i.extend(("UmU", "v5", "thing"))
    del i["ayaya"]
    print(i["ayaya"])
    i + "new_key"
    print(i)
    print(i.cache_repr())
    print(len(i))
    for pair in i:
        print(pair)
    time.sleep(30)
    print(i.cache_repr())
    i.cached = {"1": datetime.now(), "2": datetime.now()}
    print(i.cache_repr())
    print("1" in i)
    print("end test")

"""This module handles temporarily storing unique values
    """

import aiohttp
import traceback
from typing import Coroutine, ByteString, Hashable, Callable, Tuple, Iterable, Any, Optional, Dict, List, Union
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


# Type aliases
event_args = Callable[['AsyncCache', Tuple[Hashable, Any]], Any]


class AsyncCache:
    """
    Caches values until the cache overflows

    # Attributes
    `_cache (private Dict[Hashable, Any]`):
        The currently cached items.
        Items will be removed when `max_items` is exceeded.

    `max_items (int)`:
        The maximum number of items in `_cache`.

    `on_add_pass (event_args)`:
        The function to call when a unique item is added to the cache.
        Arguments: (instance of `AsyncCache`, (the key that was added, the value that was added))

    `on_add_fail (event_args)`:
        The function to call when a duplicate item was attempted to be added to the cache.
        Arguments: (instance of `AsyncCache`, (the key that wasn't added, the value that wasn't added))

    `on_remove (event_args)`:
        The function to call when an item is removed from the cache.
        Arguments: (instance of `AsyncCache`, the key-value pair that was removed from the cache)

    `_event_loop (asyncio.AbstractEventLoop)`:
        The event loop that is used to run the `on_{events}`
    """

    def __init__(self, max_items: int = 128,
                 on_add_pass: event_args = None,
                 on_add_fail: event_args = None,
                 on_remove: event_args = None,
                 ):
        self._cache: Dict[Hashable, Any] = {}
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
        task = self._call(self.on_add_pass, key, value)

        if len(self) >= self.max_items:
            self.clean()

    def clean(self):
        pass

    def append(self, key: Hashable, value: Any):
        """Add the key and value to the cache."""
        self.on_add(key, value)

    def extend(self, pairs: Dict[Hashable, Any]):
        """Add multiple pairs to the cache"""
        for pair in pairs.items():
            self.on_add(*pair)

    def __add__(self, pair: Tuple[Hashable, Any]) -> asyncio.Task:
        """Add the key and value to the cache with the `cache + (key, value)` syntax."""
        self.on_add(*pair)

    def __sub__(self, key: Hashable):
        pass

    def __getitem__(self, key: Hashable) -> Optional[Any]:
        pass

    def __delitem__(self, key: Hashable):
        pass

    def __len__(self) -> int:
        pass

    def __repr__(self) -> str:
        pass

    def __contains__(self, key: Hashable) -> bool:
        pass

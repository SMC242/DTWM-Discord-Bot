import unittest
from Utils.caching import AsyncCache
import asyncio
from collections import OrderedDict


def async_test(f):
    """Block until the async test finishes"""
    def wrapper(*args, **kwargs):
        future = f(*args, **kwargs)
        asyncio.get_event_loop().run_until_complete(future)
    return wrapper


class test_caching(unittest.TestCase):
    def setUp(self):
        self.instance = AsyncCache()
        self.pair = None  # for event callbacks

    def test_append(self):
        """Test that single items can be added with `.append()`"""
        self.instance.append(1, 1)
        self.assertEqual(self.instance._cache, OrderedDict({1: 1}))

        # check that it allows weird hashable keys
        self.instance.append((1, 2), 3)
        self.assertEqual(self.instance._cache, OrderedDict({1: 1, (1, 2): 3}))

    def test_cache_property(self):
        """Test that the cache getter works"""
        self.instance.append(1, 2)
        self.assertEqual(self.instance.cache, OrderedDict({1: 2}))

    @async_test
    async def test_on_add(self):
        """Test that a different event is called on pass and on fail"""
        self.instance.on_add_pass = lambda inst, k, v: setattr(
            self, "pair", (k, v))  # store the added pair
        self.instance.on_add_fail = lambda inst, k, v: setattr(
            self, "pair2", False)  # change the value of pair on fail

        # test on_pass
        self.instance.append(1, 1)
        await asyncio.sleep(1)  # wait for the event CB to be called
        self.assertEqual(self.pair, (1, 1), "Unique key didn't get added")

        # test on_fail
        self.instance.append(1, 1)
        await asyncio.sleep(1)  # wait for the event CB to be called
        self.assertEqual(self.pair2, False, "Non-unique key didn't fail")

        # test that on_fail still fires with a different value
        self.pair = True  # make sure that the result of the last test doesn't interfere
        self.instance.append(1, 2)
        await asyncio.sleep(1)  # wait for the event CB to be called
        self.assertEqual(self.pair2, False,
                         "Non-unique key with unique value didn't fail")

    def test_extend(self):
        """Test that multiple items can be added to the cache at a time"""
        self.instance.append(7, 8)
        self.instance.extend({1: 2, 3: 4, 5: 6})
        self.assertEqual(self.instance.cache,
                         OrderedDict({7: 8, 1: 2, 3: 4, 5: 6}), "Failed to add multiple keys in order")

    def test_len(self):
        """Test that __len__ works correctly"""
        self.instance.extend({1: 2, 3: 4})
        self.assertEqual(len(self.instance), 2)

    @async_test
    async def test_clean(self):
        """Check that the cache clears itself when overflowing"""
        self.instance.max_items = 6
        self.instance.extend({
            1: 1,
            2: 2,
            3: 3,
            4: 4,
            5: 5,
            6: 6,
            7: 7,  # it should round down the number of keys to remove when given an odd number
        })
        await asyncio.sleep(1)  # wait for the event CB
        self.assertEqual(self.instance.cache,
                         OrderedDict({
                             4: 4,
                             5: 5,
                             6: 6,
                             7: 7,
                         }),
                         "Cache didn't clear itself")

    @async_test
    async def test_on_remove(self):
        """Test that the CB is called when removing keys."""
        self.pair = []
        self.instance.on_remove = lambda inst, k, v: self.pair.append((k, v))
        self.instance.max_items = 2
        self.instance.extend({
            1: 1,
            2: 2,
            3: 3,
            4: 4
        })
        await asyncio.sleep(1)  # wait for the CB to be called
        self.assertEqual(self.pair, [(1, 1), (2, 2)], "on_remove not called")

    def test_sugar(self):
        """Test all of the syntactic sugar methods."""
        # test __add__
        self.instance + (1, 1)
        self.assertEqual(self.instance.cache, OrderedDict(
            {1: 1}), "Add operator is wonky")

        # test __sub__
        self.instance - 1
        self.assertEqual(self.instance.cache, OrderedDict({}),
                         "Subtract operator is wonky")

        # test __getitem__
        self.assertEqual(self.instance[1], None)
        self.instance.append(2, "val")
        self.assertEqual(self.instance[2], "val", "Dict-like access is wonky")

        # test __setitem__
        self.instance[3] = "value"
        self.assertEqual(self.instance.cache, OrderedDict({
                         2: "val", 3: "value"}), "Dict-like setting is wonky")

        # test __delitem__
        del self.instance[3]
        self.assertEqual(self.instance.cache, OrderedDict({
                         2: "val"}), "Dict-like removing is wonky")

        # test __iter__
        self.instance + (3, 3)
        self.assertEqual([(k, v) for k, v in self.instance.cache.items()],
                         [(2, "val"), (3, 3)],
                         "Iteration failed")

        # test __contains__
        self.assertTrue(3 in self.instance, "`in` operator is wonky")


if __name__ == '__main__':
    unittest.main()

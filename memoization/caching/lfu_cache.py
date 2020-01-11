from threading import RLock

from memoization.model import DummyWithable, CacheInfo
from memoization.caching.general.keys import make_key
import memoization.caching.general.values_with_ttl as values_toolkit_with_ttl
import memoization.caching.general.values_without_ttl as values_toolkit_without_ttl


def get_caching_wrapper(user_function, max_size, ttl, algorithm, thread_safe):
    """
    Get a caching wrapper for LFU cache
    """

    cache = {}                                          # the cache to store function results
    sentinel = object()                                 # sentinel object for the default value of map.get
    hits = misses = 0                                   # hits and misses of the cache
    lock = RLock() if thread_safe else DummyWithable()  # ensure thread-safe
    if ttl is not None:                                 # setup values toolkit according to ttl
        values_toolkit = values_toolkit_with_ttl
    else:
        values_toolkit = values_toolkit_without_ttl
    lfu_freq_list_root = _FreqNode.root()               # LFU frequency list root

    def wrapper(*args, **kwargs):
        """
        The actual wrapper
        """
        nonlocal hits, misses
        key = make_key(args, kwargs)
        cache_expired = False
        with lock:
            result = _access_lfu_cache(cache, key, sentinel)
            if result is not sentinel:
                if values_toolkit.is_cache_value_valid(result):
                    hits += 1
                    return values_toolkit.retrieve_result_from_cache_value(result)
                else:
                    cache_expired = True
            misses += 1
        result = user_function(*args, **kwargs)
        with lock:
            if key in cache:
                if cache_expired:
                    # update cache with new ttl
                    cache[key].value = values_toolkit.make_cache_value(result, ttl)
                else:
                    # result added to the cache while the lock was released
                    # no need to add again
                    pass
            else:
                _insert_into_lfu_cache(cache, key, values_toolkit.make_cache_value(result, ttl),
                                       lfu_freq_list_root, max_size)
        return result

    def cache_clear():
        """
        Clear the cache and its statistics information
        """
        nonlocal hits, misses, lfu_freq_list_root
        with lock:
            cache.clear()
            hits = misses = 0
            lfu_freq_list_root.prev = lfu_freq_list_root.next = lfu_freq_list_root

    def cache_info():
        """
        Show statistics information
        :return: a CacheInfo object describing the cache
        """
        with lock:
            return CacheInfo(hits, misses, cache.__len__(), max_size, algorithm, ttl, thread_safe)

    def get_caching_list():
        """
        Get a list containing all (key, value) in the cache in an order determined by the algorithm - LFU
        """
        result = []
        freq_node = lfu_freq_list_root.prev
        while freq_node != lfu_freq_list_root:
            cache_node = freq_node.cache_head.next
            while cache_node != freq_node.cache_head:
                result.append((cache_node.key, cache_node.value))
                cache_node = cache_node.next
            freq_node = freq_node.prev
        return result

    # expose operations to wrapper
    wrapper.cache_clear = cache_clear
    wrapper.cache_info = cache_info
    wrapper._cache = cache
    wrapper._lfu_root = lfu_freq_list_root
    wrapper._root_name = '_lfu_root'
    wrapper._get_caching_list = get_caching_list

    return wrapper


################################################################################################################################
# LFU Cache
# Least Frequently Used Cache
#
# O(1) implementation - please refer to the following documents for more details:
# http://dhruvbird.com/lfu.pdf
# https://medium.com/@epicshane/a-python-implementation-of-lfu-least-frequently-used-cache-with-o-1-time-complexity-e16b34a3c49b
################################################################################################################################


class _CacheNode(object):
    """
    Cache Node for LFU Cache
    """

    __slots__ = 'prev', 'next', 'parent', 'key', 'value', '__weakref__'

    def __init__(self, prev=None, next=None, parent=None, key=None, value=None):
        self.prev = prev
        self.next = next
        self.parent = parent
        self.key = key
        self.value = value

    @classmethod
    def root(cls, parent=None, key=None, value=None):
        """
        Generate an empty root node
        """
        node = cls(None, None, parent, key, value)
        node.prev = node.next = node
        return node

    def destroy(self):
        """
        Destroy the current cache node
        """
        self.prev.next = self.next
        self.next.prev = self.prev
        if self.parent.cache_head == self:
            self.parent.cache_head = None
        self.prev = self.next = self.parent = self.key = self.value = None


class _FreqNode(object):
    """
    Frequency Node for LFU Cache
    """

    __slots__ = 'prev', 'next', 'frequency', 'cache_head', '__weakref__'

    def __init__(self, prev=None, next=None, frequency=None, cache_head=None):
        self.prev = prev
        self.next = next
        self.frequency = frequency
        self.cache_head = cache_head

    @classmethod
    def root(cls, frequency=None, cache_head=None):
        """
        Generate an empty root node
        """
        node = cls(None, None, frequency, cache_head)
        node.prev = node.next = node
        return node

    def destroy(self):
        """
        Destroy the current frequency node
        """
        self.prev.next = self.next
        self.next.prev = self.prev
        self.prev = self.next = self.cache_head = None


def _insert_into_lfu_cache(cache, key, value, root, max_size):
    first_freq_node = root.next
    if cache.__len__() >= max_size:
        # The cache is full

        if first_freq_node.frequency != 1:
            # The first element in frequency list has its frequency other than 1 (> 1)
            # We need to drop the last element in the cache list of the first frequency node
            # and then insert a new frequency node, attaching an empty cache node together with
            # another cache node with data to the frequency node

            # Find the target
            cache_head = first_freq_node.cache_head
            last_node = cache_head.prev

            # Modify references
            last_node.prev.next = cache_head
            cache_head.prev = last_node.prev

            # Drop the last node; hold the old data to prevent arbitrary GC
            old_key = last_node.key
            old_value = last_node.value
            last_node.destroy()

            if first_freq_node.cache_head.next == first_freq_node.cache_head:
                # Getting here means that we just deleted the only data node in the cache list
                # under the first frequency list
                # Note: there is still an empty sentinel node
                # We then need to destroy the sentinel node and its parent frequency node too
                first_freq_node.cache_head.destroy()
                first_freq_node.destroy()
                first_freq_node = root.next  # update

            # Delete from cache
            del cache[old_key]

            # Prepare a new frequency node, a cache root node and a cache data node
            empty_cache_root = _CacheNode.root()
            freq_node = _FreqNode(root, first_freq_node, 1, empty_cache_root)
            cache_node = _CacheNode(empty_cache_root, empty_cache_root, freq_node, key, value)
            empty_cache_root.parent = freq_node

            # Modify references
            root.next.prev = root.next = freq_node
            empty_cache_root.prev = empty_cache_root.next = cache_node

        else:
            # We can find the last element in the cache list under the first frequency list
            # Moving it to the head and replace the stored data with a new key and a new value
            # This is more efficient

            # Find the target
            cache_head = first_freq_node.cache_head
            manipulated_node = cache_head.prev

            # Modify references
            manipulated_node.prev.next = cache_head
            cache_head.prev = manipulated_node.prev
            manipulated_node.next = cache_head.next
            manipulated_node.prev = cache_head
            cache_head.next.prev = cache_head.next = manipulated_node

            # Replace the data; hold the old data to prevent arbitrary GC
            old_key = manipulated_node.key
            old_value = manipulated_node.value
            manipulated_node.key = key
            manipulated_node.value = value

            # use another name so it can be accessed later
            cache_node = manipulated_node

            # Delete from cache
            del cache[old_key]
    else:
        # The cache is not full

        if first_freq_node.frequency != 1:
            # The first element in frequency list has its frequency other than 1 (> 1)
            # Creating a new node in frequency list with 1 as its frequency required
            # We also need to create a new cache list and attach it to this new node

            # Create a cache root and a frequency node
            cache_root = _CacheNode.root()
            freq_node = _FreqNode(root, first_freq_node, 1, cache_root)
            cache_root.parent = freq_node

            # Create another cache node to store data
            cache_node = _CacheNode(cache_root, cache_root, freq_node, key, value)

            # Modify references
            cache_root.prev = cache_root.next = cache_node
            first_freq_node.prev = root.next = freq_node  # note: DO NOT swap "=", because first_freq_node == root.next

        else:
            # We create a new cache node in the cache list
            # under the frequency node with frequency 1

            # Create a cache node and store data in it
            cache_head = first_freq_node.cache_head
            cache_node = _CacheNode(cache_head, cache_head.next, first_freq_node, key, value)

            # Modify references
            cache_node.prev.next = cache_node.next.prev = cache_node

    # Finally, insert the data into the cache
    cache[key] = cache_node


def _access_lfu_cache(cache, key, sentinel):
    if key in cache:
        cache_node = cache[key]
    else:
        # Key does not exist
        # Access failed
        return sentinel
    freq_node = cache_node.parent
    target_frequency = freq_node.frequency + 1
    if freq_node.next.frequency != target_frequency:
        # The next node on the frequency list has a frequency value different from
        # (the frequency of the current node) + 1, which means we need to construct
        # a new frequency node and an empty cache root node
        # Then we move the current node to the newly created cache list

        # Create a cache root and a frequency root
        cache_root = _CacheNode.root()
        new_freq_node = _FreqNode(freq_node, freq_node.next, target_frequency, cache_root)
        cache_root.parent = new_freq_node

        # Modify references
        cache_node.prev.next = cache_node.next
        cache_node.next.prev = cache_node.prev
        cache_node.prev = cache_node.next = cache_root
        cache_root.prev = cache_root.next = cache_node
        new_freq_node.next.prev = new_freq_node.prev.next = new_freq_node
        cache_node.parent = cache_root.parent

    else:
        # We can move the cache node to the cache list of the next node on the frequency list

        # Find the head element of the next cache list
        next_cache_head = freq_node.next.cache_head

        # Modify references
        cache_node.prev.next = cache_node.next
        cache_node.next.prev = cache_node.prev
        cache_node.next = next_cache_head.next
        cache_node.prev = next_cache_head
        next_cache_head.next.prev = next_cache_head.next = cache_node
        cache_node.parent = freq_node.next

    # check the status of the current frequency node
    if freq_node.cache_head.next == freq_node.cache_head:
        # Getting here means that we just moved away the only data node in the cache list
        # Note: there is still an empty sentinel node
        # We then need to destroy the sentinel node and its parent frequency node too
        freq_node.cache_head.destroy()
        freq_node.destroy()

    return cache_node.value

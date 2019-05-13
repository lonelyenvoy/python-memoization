from functools import partial, update_wrapper
from collections import namedtuple
import time
from threading import RLock
import inspect
import warnings

try:
    import enum  # only works on Python 3.5+
    enum.IntFlag  # only works on Python 3.6+
except (ImportError, AttributeError):
    from memoization.backport import enum  # backport for Python 3.4 and 3.5


# Public symbols
__all__ = ['cached', 'CachingAlgorithmFlag', 'FIFO', 'LRU', 'LFU']
__version__ = '0.1.4'


class CachingAlgorithmFlag(enum.IntFlag):
    FIFO = 1    # First In First Out
    LRU = 2     # Least Recently Used
    LFU = 4     # Least Frequently Used


# Insert the algorithm flags to the global namespace
globals().update(CachingAlgorithmFlag.__members__)


def cached(user_function=None, max_size=None, ttl=None, algorithm=CachingAlgorithmFlag.LRU, thread_safe=True):
    """
    @cached decorator wrapper
    :param user_function: The decorated function, to be cached
    :param max_size: The max number of items can be held in the cache
    :param ttl: Time-To-Live
                Defining how long the cached data is valid (in seconds)
                If not given, the data in cache is valid forever.
                Valid only when max_size > 0
    :param algorithm: The algorithm used when caching
                      Default: LRU (Least Recently Used)
                      Valid only when max_size > 0
                      Refer to CachingAlgorithmFlag for possible choices.
    :param thread_safe: Whether thw cache is thread safe
                        Setting it to False enhances performance.
    :return: decorator function
    """

    # Adapt to the usage of calling the decorator and that of not calling it
    # i.e. @cached and @cached()
    if user_function is None:
        return partial(cached, max_size=max_size, ttl=ttl, algorithm=algorithm, thread_safe=thread_safe)

    # Perform type checking
    if not hasattr(user_function, '__call__'):
        raise TypeError('Unable to do memoization on non-callable object ' + str(user_function))
    if max_size is not None:
        if not isinstance(max_size, int):
            raise TypeError('Expected max_size to be an integer or None')
        elif max_size < 0:
            raise ValueError('Expected max_size to be a nonnegative integer or None')
    if ttl is not None:
        if not isinstance(ttl, int) and not isinstance(ttl, float):
            raise TypeError('Expected ttl to be a number or None')
        elif ttl <= 0:
            raise ValueError('Expected ttl to be a positive number or None')
    if not isinstance(algorithm, CachingAlgorithmFlag):
        raise TypeError('Expected algorithm to be one of CachingAlgorithmFlag')
    if not isinstance(thread_safe, bool):
        raise TypeError('Expected thread_safe to be a boolean value')

    # Warn on zero-argument functions
    user_function_info = inspect.getfullargspec(user_function)
    if len(user_function_info.args) == 0 and user_function_info.varargs is None and user_function_info.varkw is None:
        warnings.warn('It makes no sense to do memoization on a function without arguments', SyntaxWarning)

    # Create wrapper
    wrapper = _create_cached_wrapper(user_function, max_size, ttl, algorithm, thread_safe)
    return update_wrapper(wrapper, user_function)  # update wrapper to make it look like the original function


def _create_cached_wrapper(user_function, max_size, ttl, algorithm, thread_safe):
    """
    Factory that creates an actual executed function when a function is decorated with @cached
    """

    cache = {}                                           # the cache to store function results
    sentinel = object()                                  # sentinel object for the default value of map.get
    hits = misses = 0                                    # hits and misses of the cache
    make_key = _make_key
    lock = RLock() if thread_safe else _DummyWithable()  # ensure thread-safe

    ##############################################################################################################
    # For TTL only
    ##############################################################################################################

    if ttl is None:

        def make_cache_value(result):
            return result

        def is_cache_value_valid(value):
            return True

        def retrieve_result_from_cache_value(value):
            return value

    else:

        def make_cache_value(result):
            return result, time.time() + ttl

        def is_cache_value_valid(value):
            return time.time() < value[1]

        def retrieve_result_from_cache_value(value):
            return value[0]

    ##############################################################################################################

    if max_size == 0:

        def cache_clear():
            nonlocal misses
            with lock:
                misses = 0

        # No caching, only statistics
        def wrapper(*args, **kwargs):
            nonlocal misses
            with lock:
                misses += 1
            return user_function(*args, **kwargs)

    elif max_size is None:

        def cache_clear():
            nonlocal hits, misses
            with lock:
                cache.clear()
                hits = misses = 0

        # Unlimited cache
        def wrapper(*args, **kwargs):
            nonlocal hits, misses
            key = make_key(args, kwargs)
            value = cache.get(key, sentinel)
            if value is not sentinel and is_cache_value_valid(value):
                with lock:
                    hits += 1
                return retrieve_result_from_cache_value(value)
            else:
                with lock:
                    misses += 1
                result = user_function(*args, **kwargs)
                cache[key] = make_cache_value(result)
                return result

    else:
        if algorithm == CachingAlgorithmFlag.FIFO or algorithm == CachingAlgorithmFlag.LRU:

            full = False                        # whether the cache is full or not
            root = []                           # linked list
            root[:] = [root, root, None, None]  # initialize by pointing to self
            _PREV = 0                           # index for the previous node
            _NEXT = 1                           # index for the next node
            _KEY = 2                            # index for the key
            _VALUE = 3                          # index for the value

            def cache_clear():
                nonlocal hits, misses, full
                with lock:
                    cache.clear()
                    hits = misses = 0
                    full = False
                    root[:] = [root, root, None, None]

            if algorithm == CachingAlgorithmFlag.FIFO:

                # Limited cache, FIFO
                def wrapper(*args, **kwargs):
                    nonlocal hits, misses, root, full
                    key = make_key(args, kwargs)
                    with lock:
                        node = cache.get(key, sentinel)
                        if node is not sentinel and is_cache_value_valid(node[_VALUE]):
                            hits += 1
                            return retrieve_result_from_cache_value(node[_VALUE])
                        misses += 1
                    result = user_function(*args, **kwargs)
                    with lock:
                        if key in cache:
                            # result added to the cache while the lock was released
                            # no need to add again
                            pass
                        elif full:
                            # switch root to the oldest element in the cache
                            old_root = root
                            root = root[_NEXT]
                            # keep references of root[_KEY] and root[_VALUE] to prevent arbitrary GC
                            old_key = root[_KEY]
                            old_value = root[_VALUE]
                            # overwrite the content of the old root
                            old_root[_KEY] = key
                            old_root[_VALUE] = make_cache_value(result)
                            # clear the content of the new root
                            root[_KEY] = root[_VALUE] = None
                            # delete from cache
                            del cache[old_key]
                            # save the result to the cache
                            cache[key] = old_root
                        else:
                            # add a node to the linked list
                            last = root[_PREV]
                            node = [last, root, key, make_cache_value(result)]  # new node
                            cache[key] = root[_PREV] = last[_NEXT] = node  # save result to the cache
                            # check whether the cache is full
                            full = (cache.__len__() >= max_size)
                    return result

                wrapper._fifo_root = root
                wrapper._root_name = '_fifo_root'

            else:  # algorithm == CachingAlgorithmFlag.LRU

                # Limited cache, LRU
                def wrapper(*args, **kwargs):
                    nonlocal hits, misses, root, full
                    key = make_key(args, kwargs)
                    with lock:
                        node = cache.get(key, sentinel)
                        if node is not sentinel and is_cache_value_valid(node[_VALUE]):
                            # move the node to the front of the list
                            node_prev, node_next, _, result = node
                            node_prev[_NEXT] = node_next
                            node_next[_PREV] = node_prev
                            node[_PREV] = root[_PREV]
                            node[_NEXT] = root
                            root[_PREV][_NEXT] = node
                            root[_PREV] = node
                            # update statistics
                            hits += 1
                            return retrieve_result_from_cache_value(result)
                        misses += 1
                    result = user_function(*args, **kwargs)
                    with lock:
                        if key in cache:
                            # result added to the cache while the lock was released
                            # no need to add again
                            pass
                        elif full:
                            # switch root to the oldest element in the cache
                            old_root = root
                            root = root[_NEXT]
                            # keep references of root[_KEY] and root[_VALUE] to prevent arbitrary GC
                            old_key = root[_KEY]
                            old_value = root[_VALUE]
                            # overwrite the content of the old root
                            old_root[_KEY] = key
                            old_root[_VALUE] = make_cache_value(result)
                            # clear the content of the new root
                            root[_KEY] = root[_VALUE] = None
                            # delete from cache
                            del cache[old_key]
                            # save the result to the cache
                            cache[key] = old_root
                        else:
                            # add a node to the linked list
                            last = root[_PREV]
                            node = [last, root, key, make_cache_value(result)]  # new node
                            cache[key] = root[_PREV] = last[_NEXT] = node  # save result to the cache
                            # check whether the cache is full
                            full = (cache.__len__() >= max_size)
                    return result

                wrapper._lru_root = root
                wrapper._root_name = '_lru_root'

        elif algorithm == CachingAlgorithmFlag.LFU:

            lfu_freq_list_root = _FreqNode.root()  # LFU frequency list root

            def cache_clear():
                nonlocal hits, misses, lfu_freq_list_root
                with lock:
                    cache.clear()
                    hits = misses = 0
                    lfu_freq_list_root.prev = lfu_freq_list_root.next = lfu_freq_list_root

            # Limited cache, LFU, with ttl
            def wrapper(*args, **kwargs):
                nonlocal hits, misses, root, full
                key = make_key(args, kwargs)
                with lock:
                    result = _access_lfu_cache(cache, key, sentinel)
                    if result is not sentinel and is_cache_value_valid(result):
                        hits += 1
                        return retrieve_result_from_cache_value(result)
                    misses += 1
                result = user_function(*args, **kwargs)
                with lock:
                    if key in cache:
                        # result added to the cache while the lock was released
                        # no need to add again
                        pass
                    else:
                        _insert_into_lfu_cache(cache, key, make_cache_value(result), lfu_freq_list_root, max_size)
                return result

            wrapper._lfu_root = lfu_freq_list_root
            wrapper._root_name = '_lfu_root'

        else:
            raise RuntimeError('Unrecognized caching algorithm flag')

    def cache_info():
        with lock:
            return _CacheInfo(hits, misses, cache.__len__(), max_size, algorithm, ttl, thread_safe)

    wrapper.cache_info = cache_info
    wrapper.cache_clear = cache_clear
    wrapper._cache = cache
    return wrapper


class _HashedList(list):
    """
    This class guarantees that hash() will be called no more than once per element.
    """

    __slots__ = 'hash_value'

    def __init__(self, tup, hash_value):
        super().__init__(tup)
        self.hash_value = hash_value

    def __hash__(self):
        return self.hash_value


def _make_key(args, kwargs, kwargs_mark=(object(),)):
    """
    Make a cache key
    """
    key = args
    if kwargs:
        key += kwargs_mark
        for item in kwargs.items():
            key += item
    try:
        hash_value = hash(key)
    except TypeError:  # process unhashable types
        return str(key)
    else:
        return _HashedList(key, hash_value)


####################################################################################################
# LFU Cache
# Least Frequently Used Cache
#
# O(1) implementation - please refer to the following documents for more details:
# http://dhruvbird.com/lfu.pdf
# https://medium.com/@epicshane/a-python-implementation-of-lfu-least-frequently-used-cache-with-o-1-time-complexity-e16b34a3c49b
####################################################################################################


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


class _DummyWithable(object):
    """
    This class is used to create instances that can bypass "with" statements
    """

    __slots__ = ()

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# Named type CacheInfo
_CacheInfo = namedtuple('CacheInfo', ['hits', 'misses', 'current_size', 'max_size', 'algorithm', 'ttl', 'thread_safe'])


if __name__ == '__main__':
    import sys
    sys.stderr.write('python-memoization v' + __version__ +
                     ': A powerful caching library for Python, with TTL support and multiple algorithm options.\n')
    sys.stderr.write('Go to https://github.com/lonelyenvoy/python-memoization for usage and more details.\n')



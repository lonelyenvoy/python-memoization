from threading import RLock

from memoization.model import DummyWithable, CacheInfo
from memoization.caching.general.keys import make_key
import memoization.caching.general.values_with_ttl as values_toolkit_with_ttl
import memoization.caching.general.values_without_ttl as values_toolkit_without_ttl


def get_caching_wrapper(user_function, max_size, ttl, algorithm, thread_safe):
    """
    Get a caching wrapper for FIFO cache
    """

    cache = {}                                          # the cache to store function results
    sentinel = object()                                 # sentinel object for the default value of map.get
    hits = misses = 0                                   # hits and misses of the cache
    lock = RLock() if thread_safe else DummyWithable()  # ensure thread-safe
    if ttl is not None:                                 # setup values toolkit according to ttl
        values_toolkit = values_toolkit_with_ttl
    else:
        values_toolkit = values_toolkit_without_ttl

    # for FIFO list
    full = False                                        # whether the cache is full or not
    root = []                                           # linked list
    root[:] = [root, root, None, None]                  # initialize by pointing to self
    _PREV = 0                                           # index for the previous node
    _NEXT = 1                                           # index for the next node
    _KEY = 2                                            # index for the key
    _VALUE = 3                                          # index for the value

    def wrapper(*args, **kwargs):
        """
        The actual wrapper
        """
        nonlocal hits, misses, root, full
        key = make_key(args, kwargs)
        cache_expired = False
        with lock:
            node = cache.get(key, sentinel)
            if node is not sentinel:
                if values_toolkit.is_cache_value_valid(node[_VALUE]):
                    hits += 1
                    return values_toolkit.retrieve_result_from_cache_value(node[_VALUE])
                else:
                    cache_expired = True
            misses += 1
        result = user_function(*args, **kwargs)
        with lock:
            if key in cache:
                if cache_expired:
                    # update cache with new ttl
                    cache[key][_VALUE] = values_toolkit.make_cache_value(result, ttl)
                else:
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
                old_root[_VALUE] = values_toolkit.make_cache_value(result, ttl)
                # clear the content of the new root
                root[_KEY] = root[_VALUE] = None
                # delete from cache
                del cache[old_key]
                # save the result to the cache
                cache[key] = old_root
            else:
                # add a node to the linked list
                last = root[_PREV]
                node = [last, root, key, values_toolkit.make_cache_value(result, ttl)]  # new node
                cache[key] = root[_PREV] = last[_NEXT] = node  # save result to the cache
                # check whether the cache is full
                full = (cache.__len__() >= max_size)
        return result

    def cache_clear():
        """
        Clear the cache and its statistics information
        """
        nonlocal hits, misses, full
        with lock:
            cache.clear()
            hits = misses = 0
            full = False
            root[:] = [root, root, None, None]

    def cache_info():
        """
        Show statistics information
        :return: a CacheInfo object describing the cache
        """
        with lock:
            return CacheInfo(hits, misses, cache.__len__(), max_size, algorithm, ttl, thread_safe)

    def get_caching_list():
        """
        Get a list containing all (key, value) in the cache in an order determined by the algorithm - FIFO
        """
        node = root[_PREV]
        result = []
        while node is not root:
            result.append((node[_KEY], node[_VALUE]))
            node = node[_PREV]
        return result

    # expose operations to wrapper
    wrapper.cache_clear = cache_clear
    wrapper.cache_info = cache_info
    wrapper._cache = cache
    wrapper._fifo_root = root
    wrapper._root_name = '_fifo_root'
    wrapper._get_caching_list = get_caching_list

    return wrapper

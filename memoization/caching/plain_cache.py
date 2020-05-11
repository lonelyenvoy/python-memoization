from threading import RLock

from memoization.model import DummyWithable, CacheInfo
import memoization.caching.general.keys_order_dependent as keys_toolkit_order_dependent
import memoization.caching.general.keys_order_independent as keys_toolkit_order_independent
import memoization.caching.general.values_with_ttl as values_toolkit_with_ttl
import memoization.caching.general.values_without_ttl as values_toolkit_without_ttl


def get_caching_wrapper(user_function, max_size, ttl, algorithm, thread_safe, order_independent, custom_key_maker):
    """
    Get a caching wrapper for space-unlimited cache
    """

    cache = {}                                                  # the cache to store function results
    sentinel = object()                                         # sentinel object for the default value of map.get
    hits = misses = 0                                           # hits and misses of the cache
    lock = RLock() if thread_safe else DummyWithable()          # ensure thread-safe
    if ttl is not None:                                         # set up values toolkit according to ttl
        values_toolkit = values_toolkit_with_ttl
    else:
        values_toolkit = values_toolkit_without_ttl
    if custom_key_maker is not None:                            # use custom make_key function
        make_key = custom_key_maker
    else:
        if order_independent:                                   # set up keys toolkit according to order_independent
            make_key = keys_toolkit_order_independent.make_key
        else:
            make_key = keys_toolkit_order_dependent.make_key

    def wrapper(*args, **kwargs):
        """
        The actual wrapper
        """
        nonlocal hits, misses
        key = make_key(args, kwargs)
        value = cache.get(key, sentinel)
        if value is not sentinel and values_toolkit.is_cache_value_valid(value):
            with lock:
                hits += 1
            return values_toolkit.retrieve_result_from_cache_value(value)
        else:
            with lock:
                misses += 1
            result = user_function(*args, **kwargs)
            cache[key] = values_toolkit.make_cache_value(result, ttl)
            return result

    def cache_clear():
        """
        Clear the cache and statistics information
        """
        nonlocal hits, misses
        with lock:
            cache.clear()
            hits = misses = 0

    def cache_info():
        """
        Show statistics information
        :return: a CacheInfo object describing the cache
        """
        with lock:
            return CacheInfo(hits, misses, cache.__len__(), max_size, algorithm,
                             ttl, thread_safe, order_independent, custom_key_maker is not None)

    # expose operations and members of wrapper
    wrapper.cache_clear = cache_clear
    wrapper.cache_info = cache_info
    wrapper._cache = cache

    return wrapper

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

    def cache_is_empty():
        """Return True if the cache contains no elements"""
        return cache.__len__() == 0

    def cache_is_full():
        """Return True if the cache is full"""
        return False

    def cache_contains_argument(function_arguments, alive_only=True):
        """
        Return True if the cache contains a cached item with the specified function call arguments

        :param function_arguments:  Can be a list, a tuple or a dict.
                                    - Full arguments: use a list to represent both positional arguments and keyword
                                      arguments. The list contains two elements, a tuple (positional arguments) and
                                      a dict (keyword arguments). For example,
                                        f(1, 2, 3, a=4, b=5, c=6)
                                      can be represented by:
                                        [(1, 2, 3), {'a': 4, 'b': 5, 'c': 6}]
                                    - Positional arguments only: when the arguments does not include keyword arguments,
                                      a tuple can be used to represent positional arguments. For example,
                                        f(1, 2, 3)
                                      can be represented by:
                                        (1, 2, 3)
                                    - Keyword arguments only: when the arguments does not include positional arguments,
                                      a dict can be used to represent keyword arguments. For example,
                                        f(a=4, b=5, c=6)
                                      can be represented by:
                                        {'a': 4, 'b': 5, 'c': 6}

        :param alive_only:          Whether to check alive cache item only (default to True).

        :return:                    True if the desired cached item is present, False otherwise.
        """
        if isinstance(function_arguments, tuple):
            positional_argument_tuple = function_arguments
            keyword_argument_dict = {}
        elif isinstance(function_arguments, dict):
            positional_argument_tuple = ()
            keyword_argument_dict = function_arguments
        elif isinstance(function_arguments, list) and len(function_arguments) == 2:
            positional_argument_tuple, keyword_argument_dict = function_arguments
            if not isinstance(positional_argument_tuple, tuple) or not isinstance(keyword_argument_dict, dict):
                raise TypeError('Expected function_arguments to be a list containing a positional argument tuple '
                                'and a keyword argument dict')
        else:
            raise TypeError('Expected function_arguments to be a tuple, a dict, or a list with 2 elements')
        key = make_key(positional_argument_tuple, keyword_argument_dict)
        with lock:
            value = cache.get(key, sentinel)
            if value is not sentinel:
                return values_toolkit.is_cache_value_valid(value) if alive_only else True
            return False

    def cache_contains_key(key, alive_only=True):
        """
        Return True if the cache contains a cache item with the specified key. This function is only recommended to use
        when you provide a custom key maker; otherwise, use cache_contains_argument() instead.

        :param key:                 A key built by the default key maker or a custom key maker.

        :param alive_only:          Whether to check alive cache item only (default to True).

        :return:                    True if the desired cached item is present, False otherwise.
        """
        with lock:
            value = cache.get(key, sentinel)
            if value is not sentinel:
                return values_toolkit.is_cache_value_valid(value) if alive_only else True
            return False

    def cache_contains_result(return_value, alive_only=True):
        """
        Return True if the cache contains a cache item with the specified user function return value. O(n) time
        complexity.

        :param return_value:        A return value coming from the user function.

        :param alive_only:          Whether to check alive cache item only (default to True).

        :return:                    True if the desired cached item is present, False otherwise.
        """
        with lock:
            for value in cache.values():
                is_alive = values_toolkit.is_cache_value_valid(value)
                cache_result = values_toolkit.retrieve_result_from_cache_value(value)
                if cache_result == return_value:
                    return is_alive if alive_only else True
            return False

    def cache_for_each(consumer):
        """
        Perform the given action for each cache element in an order determined by the algorithm (FIFO) until all
        elements have been processed or the action throws an error

        :param consumer:            an action function to process the cache elements. Must have 3 arguments:
                                      def consumer(cache_key, cache_result, is_alive): ...
                                    cache_key is built by the default key maker or a custom key maker.
                                    cache_result is a return value coming from the user function.
                                    is_alive is a boolean value indicating whether the cache is still alive
                                    (if a TTL is given).
        """
        with lock:
            for key, value in cache.items():
                is_alive = values_toolkit.is_cache_value_valid(value)
                cache_result = values_toolkit.retrieve_result_from_cache_value(value)
                consumer(key, cache_result, is_alive)

    def cache_remove_if(predicate):
        """
        Remove all cache elements that satisfy the given predicate

        :param predicate:           a predicate function to judge whether the cache elements should be removed. Must
                                    have 3 arguments:
                                      def consumer(cache_key, cache_result, is_alive): ...
                                    cache_key is built by the default key maker or a custom key maker.
                                    cache_result is a return value coming from the user function.
                                    is_alive is a boolean value indicating whether the cache is still alive
                                    (if a TTL is given).

        :return:                    True if at least one element is removed, False otherwise.
        """
        with lock:
            keys_to_be_removed = []
            for key, value in cache.items():
                is_alive = values_toolkit.is_cache_value_valid(value)
                cache_result = values_toolkit.retrieve_result_from_cache_value(value)
                if predicate(key, cache_result, is_alive):
                    keys_to_be_removed.append(key)
            for key in keys_to_be_removed:
                del cache[key]
            return len(keys_to_be_removed) > 0

    # expose operations and members of wrapper
    wrapper.cache_clear = cache_clear
    wrapper.cache_info = cache_info
    wrapper.cache_is_empty = cache_is_empty
    wrapper.cache_is_full = cache_is_full
    wrapper.cache_contains_argument = cache_contains_argument
    wrapper.cache_contains_key = cache_contains_key
    wrapper.cache_contains_result = cache_contains_result
    wrapper.cache_for_each = cache_for_each
    wrapper.cache_remove_if = cache_remove_if
    wrapper.cache_make_key = make_key
    wrapper._cache = cache

    return wrapper

from threading import RLock

from memoization.model import DummyWithable, CacheInfo
import memoization.caching.general.keys_order_dependent as keys_toolkit_order_dependent
import memoization.caching.general.keys_order_independent as keys_toolkit_order_independent
import memoization.caching.general.values_with_ttl as values_toolkit_with_ttl
import memoization.caching.general.values_without_ttl as values_toolkit_without_ttl


def get_caching_wrapper(user_function, max_size, ttl, algorithm, thread_safe, order_independent, custom_key_maker):
    """Get a caching wrapper for LRU cache"""

    cache = {}                                                  # the cache to store function results
    key_argument_map = {}                                       # mapping from cache keys to user function arguments
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

    # for LRU list
    full = False                                                # whether the cache is full or not
    root = []                                                   # linked list
    root[:] = [root, root, None, None]                          # initialize by pointing to self
    _PREV = 0                                                   # index for the previous node
    _NEXT = 1                                                   # index for the next node
    _KEY = 2                                                    # index for the key
    _VALUE = 3                                                  # index for the value

    def wrapper(*args, **kwargs):
        """The actual wrapper"""
        nonlocal hits, misses, root, full
        key = make_key(args, kwargs)
        cache_expired = False
        with lock:
            node = cache.get(key, sentinel)
            if node is not sentinel:
                # move the node to the front of the list
                node_prev, node_next, _, result = node
                node_prev[_NEXT] = node_next
                node_next[_PREV] = node_prev
                node[_PREV] = root[_PREV]
                node[_NEXT] = root
                root[_PREV][_NEXT] = node
                root[_PREV] = node
                if values_toolkit.is_cache_value_valid(node[_VALUE]):
                    # update statistics
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
                del key_argument_map[old_key]
                # save the result to the cache
                cache[key] = old_root
                key_argument_map[key] = (args, kwargs)
            else:
                # add a node to the linked list
                last = root[_PREV]
                node = [last, root, key, values_toolkit.make_cache_value(result, ttl)]  # new node
                cache[key] = root[_PREV] = last[_NEXT] = node  # save result to the cache
                key_argument_map[key] = (args, kwargs)
                # check whether the cache is full
                full = (cache.__len__() >= max_size)
        return result

    def cache_clear():
        """Clear the cache and its statistics information"""
        nonlocal hits, misses, full
        with lock:
            cache.clear()
            key_argument_map.clear()
            hits = misses = 0
            full = False
            root[:] = [root, root, None, None]

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
        return full

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
            node = cache.get(key, sentinel)
            if node is not sentinel:
                return values_toolkit.is_cache_value_valid(node[_VALUE]) if alive_only else True
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
            node = root[_PREV]
            while node is not root:
                is_alive = values_toolkit.is_cache_value_valid(node[_VALUE])
                cache_result = values_toolkit.retrieve_result_from_cache_value(node[_VALUE])
                if cache_result == return_value:
                    return is_alive if alive_only else True
                node = node[_PREV]
            return False

    def cache_for_each(consumer):
        """
        Perform the given action for each cache element in an order determined by the algorithm until all
        elements have been processed or the action throws an error

        :param consumer:            an action function to process the cache elements. Must have 3 arguments:
                                      def consumer(user_function_arguments, user_function_result, is_alive): ...
                                    user_function_arguments is a tuple holding arguments in the form of (args, kwargs).
                                      args is a tuple holding positional arguments.
                                      kwargs is a dict holding keyword arguments.
                                      for example, for a function: foo(a, b, c, d), calling it by: foo(1, 2, c=3, d=4)
                                      user_function_arguments == ((1, 2), {'c': 3, 'd': 4})
                                    user_function_result is a return value coming from the user function.
                                    cache_result is a return value coming from the user function.
                                    is_alive is a boolean value indicating whether the cache is still alive
                                    (if a TTL is given).
        """
        with lock:
            node = root[_PREV]
            while node is not root:
                is_alive = values_toolkit.is_cache_value_valid(node[_VALUE])
                user_function_result = values_toolkit.retrieve_result_from_cache_value(node[_VALUE])
                user_function_arguments = key_argument_map[node[_KEY]]
                consumer(user_function_arguments, user_function_result, is_alive)
                node = node[_PREV]

    def cache_arguments():
        """
        Get user function arguments of all alive cache elements

        see also: cache_items()

        Example:
            @cached
            def f(a, b, c, d):
                ...
            f(1, 2, c=3, d=4)
            for argument in f.cache_arguments():
                print(argument)  # ((1, 2), {'c': 3, 'd': 4})

        :return: an iterable which iterates through a list of a tuple containing a tuple (positional arguments) and
                 a dict (keyword arguments)
        """
        with lock:
            node = root[_PREV]
            while node is not root:
                if values_toolkit.is_cache_value_valid(node[_VALUE]):
                    yield key_argument_map[node[_KEY]]
                node = node[_PREV]

    def cache_results():
        """
        Get user function return values of all alive cache elements

        see also: cache_items()

        Example:
            @cached
            def f(a):
                return a
            f('hello')
            for result in f.cache_results():
                print(result)  # 'hello'

        :return: an iterable which iterates through a list of user function result (of any type)
        """
        with lock:
            node = root[_PREV]
            while node is not root:
                if values_toolkit.is_cache_value_valid(node[_VALUE]):
                    yield values_toolkit.retrieve_result_from_cache_value(node[_VALUE])
                node = node[_PREV]

    def cache_items():
        """
        Get cache items, i.e. entries of all alive cache elements, in the form of (argument, result).

        argument: a tuple containing a tuple (positional arguments) and a dict (keyword arguments).
        result: a user function return value of any type.

        see also: cache_arguments(), cache_results().

        Example:
            @cached
            def f(a, b, c, d):
                return 'the answer is ' + str(a)
            f(1, 2, c=3, d=4)
            for argument, result in f.cache_items():
                print(argument)  # ((1, 2), {'c': 3, 'd': 4})
                print(result)    # 'the answer is 1'

        :return: an iterable which iterates through a list of (argument, result) entries
        """
        with lock:
            node = root[_PREV]
            while node is not root:
                if values_toolkit.is_cache_value_valid(node[_VALUE]):
                    yield key_argument_map[node[_KEY]], values_toolkit.retrieve_result_from_cache_value(node[_VALUE])
                node = node[_PREV]

    def cache_remove_if(predicate):
        """
        Remove all cache elements that satisfy the given predicate

        :param predicate:           a predicate function to judge whether the cache elements should be removed. Must
                                    have 3 arguments, and returns True or False:
                                      def consumer(user_function_arguments, user_function_result, is_alive): ...
                                    user_function_arguments is a tuple holding arguments in the form of (args, kwargs).
                                      args is a tuple holding positional arguments.
                                      kwargs is a dict holding keyword arguments.
                                      for example, for a function: foo(a, b, c, d), calling it by: foo(1, 2, c=3, d=4)
                                      user_function_arguments == ((1, 2), {'c': 3, 'd': 4})
                                    user_function_result is a return value coming from the user function.
                                    cache_result is a return value coming from the user function.
                                    is_alive is a boolean value indicating whether the cache is still alive
                                    (if a TTL is given).

        :return:                    True if at least one element is removed, False otherwise.
        """
        nonlocal full
        removed = False
        with lock:
            node = root[_PREV]
            while node is not root:
                is_alive = values_toolkit.is_cache_value_valid(node[_VALUE])
                user_function_result = values_toolkit.retrieve_result_from_cache_value(node[_VALUE])
                user_function_arguments = key_argument_map[node[_KEY]]
                if predicate(user_function_arguments, user_function_result, is_alive):
                    removed = True
                    node_prev = node[_PREV]
                    # relink pointers of node.prev.next and node.next.prev
                    node_prev[_NEXT] = node[_NEXT]
                    node[_NEXT][_PREV] = node_prev
                    # clear the content of this node
                    key = node[_KEY]
                    node[_KEY] = node[_VALUE] = None
                    # delete from cache
                    del cache[key]
                    del key_argument_map[key]
                    # check whether the cache is full
                    full = (cache.__len__() >= max_size)
                    node = node_prev
                else:
                    node = node[_PREV]
        return removed

    # expose operations to wrapper
    wrapper.cache_clear = cache_clear
    wrapper.cache_info = cache_info
    wrapper.cache_is_empty = cache_is_empty
    wrapper.cache_is_full = cache_is_full
    wrapper.cache_contains_argument = cache_contains_argument
    wrapper.cache_contains_result = cache_contains_result
    wrapper.cache_for_each = cache_for_each
    wrapper.cache_arguments = cache_arguments
    wrapper.cache_results = cache_results
    wrapper.cache_items = cache_items
    wrapper.cache_remove_if = cache_remove_if
    wrapper._cache = cache
    wrapper._lru_root = root
    wrapper._root_name = '_lru_root'

    return wrapper

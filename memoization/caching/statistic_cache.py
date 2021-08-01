from threading import RLock

from memoization.model import DummyWithable, CacheInfo


def get_caching_wrapper(user_function, max_size, ttl, algorithm, thread_safe, order_independent, custom_key_maker):
    """Get a caching wrapper for statistics only, without any actual caching"""

    misses = 0                                          # number of misses of the cache
    lock = RLock() if thread_safe else DummyWithable()  # ensure thread-safe

    def wrapper(*args, **kwargs):
        """The actual wrapper"""
        nonlocal misses
        with lock:
            misses += 1
        return user_function(*args, **kwargs)

    def cache_clear():
        """Clear the cache and statistics information"""
        nonlocal misses
        with lock:
            misses = 0

    def cache_info():
        """
        Show statistics information

        :return: a CacheInfo object describing the cache
        """
        with lock:
            return CacheInfo(0, misses, 0, max_size, algorithm,
                             ttl, thread_safe, order_independent, custom_key_maker is not None)

    def cache_is_empty():
        """Return True if the cache contains no elements"""
        return True

    def cache_is_full():
        """Return True if the cache is full"""
        return True

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
        return False

    def cache_contains_result(return_value, alive_only=True):
        """
        Return True if the cache contains a cache item with the specified user function return value. O(n) time
        complexity.

        :param return_value:        A return value coming from the user function.

        :param alive_only:          Whether to check alive cache item only (default to True).

        :return:                    True if the desired cached item is present, False otherwise.
        """
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
        pass

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
        yield from ()

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
        yield from ()

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
        yield from ()

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
        return False

    # expose operations and members of wrapper
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
    wrapper._cache = None

    return wrapper


from typing import TypeVar, Callable, Any, Protocol, Union, List, Tuple, Dict, Iterable

from memoization.model import CacheInfo

T = TypeVar('T', bound=Callable[..., Any])


class CachedFunction(Protocol[T]):
    __call__: T
    __wrapped__: T

    def cache_clear(self) -> None:
        """Clear the cache and its statistics information"""

    def cache_info(self) -> CacheInfo:
        """
        Show statistics information

        :return: a CacheInfo object describing the cache
        """

    def cache_is_empty(self) -> bool:
        """Return True if the cache contains no elements"""

    def cache_is_full(self) -> bool:
        """Return True if the cache is full"""

    def cache_contains_argument(self, function_arguments: Union[List, Tuple, Dict[str, Any]],
                                alive_only: bool = ...) -> bool:
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

    def cache_contains_result(self, return_value: Any, alive_only: bool = ...) -> bool:
        """
        Return True if the cache contains a cache item with the specified user function return value. O(n) time
        complexity.

        :param return_value:        A return value coming from the user function.

        :param alive_only:          Whether to check alive cache item only (default to True).

        :return:                    True if the desired cached item is present, False otherwise.
        """

    def cache_for_each(self, consumer: Callable[[Tuple[Tuple, Dict], Any, bool], None]) -> None:
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
                                    is_alive is a boolean value indicating whether the cache is still alive
                                    (if a TTL is given).
        """

    def cache_arguments(self) -> Iterable[Tuple[Tuple, Dict]]:
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

    def cache_results(self) -> Iterable[Any]:
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

    def cache_items(self) -> Iterable[Tuple[Tuple[Tuple, Dict], Any]]:
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

    def cache_remove_if(self, predicate: Callable[[Tuple[Tuple, Dict], Any, bool], bool]) -> bool:
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
                                    is_alive is a boolean value indicating whether the cache is still alive
                                    (if a TTL is given).

        :return:                    True if at least one element is removed, False otherwise.
        """

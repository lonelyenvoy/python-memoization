from functools import partial, update_wrapper
import inspect
import warnings

import memoization.caching.statistic_cache as statistic_cache
import memoization.caching.plain_cache as plain_cache
from memoization.constant.flag import CachingAlgorithmFlag as CachingAlgorithmFlag  # for type-checking to work properly
from memoization.config.algorithm_mapping import get_cache_toolkit


# Public symbols
__all__ = ['cached', 'suppress_warnings', 'CachingAlgorithmFlag']
__version__ = '0.4.0'

# Whether warnings are enabled
_warning_enabled = True


# Insert the algorithm flags to the global namespace for convenience
globals().update(CachingAlgorithmFlag.__members__)


def cached(user_function=None, max_size=None, ttl=None,
           algorithm=CachingAlgorithmFlag.LRU, thread_safe=True, order_independent=False, custom_key_maker=None):
    """
    @cached decorator wrapper

    :param user_function:       The decorated function, to be cached.

    :param max_size:            The max number of items can be held in the cache.

    :param ttl:                 Time-To-Live.
                                Defining how long the cached data is valid (in seconds)
                                If not given, the data in cache is valid forever.
                                Valid only when max_size > 0 or max_size is None

    :param algorithm:           The algorithm used when caching.
                                Default: LRU (Least Recently Used)
                                Valid only when max_size > 0
                                Refer to CachingAlgorithmFlag for possible choices.

    :param thread_safe:         Whether the cache is thread safe.
                                Setting it to False enhances performance.

    :param order_independent:   Whether the cache is kwarg-order-independent.
                                For the following code snippet:
                                    f(a=1, b=1)
                                    f(b=1, a=1)
                                - If True, f(a=1, b=1) will be treated the same as f(b=1, a=1) and the cache
                                  will be hit once.
                                - If False, they will be treated as different calls and the cache will miss.
                                  Setting it to True adds performance overhead.
                                Valid only when (max_size > 0 or max_size is None) and custom_key_maker is None

    :param custom_key_maker:    Use this parameter to override the default cache key maker.
                                It should be a function with the same signature as user_function.
                                - The produced key must be unique, which means two sets of different arguments
                                  always map to two different keys.
                                - The produced key must be hashable and comparable with another key (the
                                  memoization library only needs to check for their equality).
                                - Key computation should be efficient, and keys should be small objects.
                                Valid only when max_size > 0 or max_size is None
                                e.g.
                                def get_employee_id(employee):
                                    return employee.id
                                @cached(custom_key_maker=get_employee_id)
                                def calculate_performance(employee):
                                    ...

    :return: decorator function
    """

    # Adapt to the usage of calling the decorator and that of not calling it
    # i.e. @cached and @cached()
    if user_function is None:
        return partial(cached, max_size=max_size, ttl=ttl, algorithm=algorithm,
                       thread_safe=thread_safe, order_independent=order_independent, custom_key_maker=custom_key_maker)

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
        raise TypeError('Expected algorithm to be an instance of CachingAlgorithmFlag')
    if not isinstance(thread_safe, bool):
        raise TypeError('Expected thread_safe to be a boolean value')
    if not isinstance(order_independent, bool):
        raise TypeError('Expected order_independent to be a boolean value')
    if custom_key_maker is not None and not hasattr(custom_key_maker, '__call__'):
        raise TypeError('Expected custom_key_maker to be callable or None')

    # Check custom key maker and wrap it
    if custom_key_maker is not None:
        if _warning_enabled:
            custom_key_maker_info = inspect.getfullargspec(custom_key_maker)
            user_function_info = inspect.getfullargspec(user_function)
            if custom_key_maker_info.args != user_function_info.args or \
                    custom_key_maker_info.varargs != user_function_info.varargs or \
                    custom_key_maker_info.varkw != user_function_info.varkw or \
                    custom_key_maker_info.kwonlyargs != user_function_info.kwonlyargs or \
                    custom_key_maker_info.defaults != user_function_info.defaults or \
                    custom_key_maker_info.kwonlydefaults != user_function_info.kwonlydefaults:
                warnings.warn('Expected custom_key_maker to have the same signature as the function being cached. '
                              'Call memoization.suppress_warnings() before using @cached to remove this message.',
                              SyntaxWarning)

        def custom_key_maker_wrapper(args, kwargs):
            return custom_key_maker(*args, **kwargs)
    else:
        custom_key_maker_wrapper = None

    # Create wrapper
    wrapper = _create_cached_wrapper(user_function, max_size, ttl, algorithm,
                                     thread_safe, order_independent, custom_key_maker_wrapper)
    wrapper.__signature__ = inspect.signature(user_function)  # copy the signature of user_function to the wrapper
    return update_wrapper(wrapper, user_function)  # update wrapper to make it look like the original function


def suppress_warnings(should_warn=False):
    """
    Disable/Enable warnings when @cached is used
    Must be called before using @cached

    :param should_warn: Whether warnings should be shown (False by default)
    """
    global _warning_enabled
    _warning_enabled = should_warn


def _create_cached_wrapper(user_function, max_size, ttl, algorithm, thread_safe, order_independent, custom_key_maker):
    """
    Factory that creates an actual executed function when a function is decorated with @cached
    """
    if max_size == 0:
        return statistic_cache.get_caching_wrapper(user_function, max_size, ttl, algorithm,
                                                   thread_safe, order_independent, custom_key_maker)
    elif max_size is None:
        return plain_cache.get_caching_wrapper(user_function, max_size, ttl, algorithm,
                                               thread_safe, order_independent, custom_key_maker)
    else:
        cache_toolkit = get_cache_toolkit(algorithm)
        return cache_toolkit.get_caching_wrapper(user_function, max_size, ttl, algorithm,
                                                 thread_safe, order_independent, custom_key_maker)


if __name__ == '__main__':
    import sys
    sys.stderr.write('python-memoization v' + __version__ +
                     ': A powerful caching library for Python, with TTL support and multiple algorithm options.\n')
    sys.stderr.write('Go to https://github.com/lonelyenvoy/python-memoization for usage and more details.\n')

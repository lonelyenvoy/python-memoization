from functools import partial, update_wrapper
import inspect
import warnings

import memoization.caching.statistic_cache as statistic_cache
import memoization.caching.plain_cache as plain_cache
from memoization.constant.flag import CachingAlgorithmFlag
from memoization.config.algorithm_mapping import get_cache_toolkit


# Public symbols
__all__ = ['cached', 'CachingAlgorithmFlag']
__version__ = '0.2.2'


# Insert the algorithm flags to the global namespace for convenience
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
    :param thread_safe: Whether the cache is thread safe
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
        raise TypeError('Expected algorithm to be an instance of CachingAlgorithmFlag')
    if not isinstance(thread_safe, bool):
        raise TypeError('Expected thread_safe to be a boolean value')

    # Warn on zero-argument functions
    user_function_info = inspect.getfullargspec(user_function)
    if len(user_function_info.args) == 0 and user_function_info.varargs is None and user_function_info.varkw is None \
            and max_size is None and ttl is None:
        warnings.warn('It makes no sense to do memoization on a function without arguments', SyntaxWarning)

    # Create wrapper
    wrapper = _create_cached_wrapper(user_function, max_size, ttl, algorithm, thread_safe)
    return update_wrapper(wrapper, user_function)  # update wrapper to make it look like the original function


def _create_cached_wrapper(user_function, max_size, ttl, algorithm, thread_safe):
    """
    Factory that creates an actual executed function when a function is decorated with @cached
    """
    if max_size == 0:
        return statistic_cache.get_caching_wrapper(user_function, max_size, ttl, algorithm, thread_safe)
    elif max_size is None:
        return plain_cache.get_caching_wrapper(user_function, max_size, ttl, algorithm, thread_safe)
    else:
        cache_toolkit = get_cache_toolkit(algorithm)
        return cache_toolkit.get_caching_wrapper(user_function, max_size, ttl, algorithm, thread_safe)


if __name__ == '__main__':
    import sys
    sys.stderr.write('python-memoization v' + __version__ +
                     ': A powerful caching library for Python, with TTL support and multiple algorithm options.\n')
    sys.stderr.write('Go to https://github.com/lonelyenvoy/python-memoization for usage and more details.\n')



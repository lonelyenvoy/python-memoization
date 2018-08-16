import collections
import inspect
import warnings
import json
import time
from functools import wraps
from functools import reduce

__version__ = '0.0.10'
_cache = {}


def cached(max_items=None, ttl=None):
    """
    @cached decorator wrapper.
    :param max_items: The max items can be held in memoization cache
                      * NOT RECOMMENDED *
                      This argument, if given, can dramatically slow down the performance.
    :param ttl: Time-To-Live
                Defining how long the cached data is valid (in seconds)
                If not given, the data in cache is valid forever.
    :return: decorator
    """
    @_include_undecorated_function()
    def decorator(func):
        """
        @cached decorator.
        :param func: The decorated function
        :return: wrapper
        """
        # type checks
        if not _is_function(func):
            raise TypeError('Unable to do memoization on non-function object ' + str(func))
        if max_items is not None and (not isinstance(max_items, int) or max_items <= 0):
            raise ValueError('Illegal max_items <' + str(max_items) + '>: must be a positive integer')
        if ttl is not None and ((not isinstance(ttl, int) and not isinstance(ttl, float)) or ttl <= 0):
            raise ValueError('Illegal ttl <' + str(ttl) + '>: must be a positive number')
        arg_spec = inspect.getargspec(func)
        if len(arg_spec.args) == 0 and arg_spec.varargs is None and arg_spec.keywords is None:
            warnings.warn('It\'s meaningless to do memoization on a function with no arguments', SyntaxWarning)

        # init cache for func
        initial_function_id = id(func)
        _cache[initial_function_id] = {} if max_items is None else collections.OrderedDict()

        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            The actual executed function when a function is decorated with @cached.
            """
            input_args = _hashable_args(args, kwargs)
            function_id = id(func)
            specified_cache = _cache[function_id]
            if input_args in specified_cache.keys() \
                    and (ttl is None or time.time() < specified_cache[input_args]['expires_at']):
                # already validly cached
                cache_unit = specified_cache[input_args]
                cache_unit['access_count'] += 1
                return cache_unit['result']
            else:
                # not yet cached
                output = func(*args, **kwargs)  # execute func
                if max_items is not None and _size_explicit(function_id) >= max_items:  # pop item when fully occupied
                    specified_cache.popitem(last=False)
                # make cache
                if ttl is not None:
                    specified_cache[input_args] = {'result': output, 'access_count': 0, 'expires_at': time.time() + ttl}
                else:
                    specified_cache[input_args] = {'result': output, 'access_count': 0}
                return output
        return wrapper
    return decorator


def clean(safe_access_count=1, func=None):
    """
    Remove the cached items, which are accessed fewer than a given value, of a certain function.
    :param safe_access_count: The access times that are safe from cleaning process
    :param func: The certain function that needs cleaning, if not given, cleaning process will be executed
                 for all functions
    """
    def del_unit(func_id, cache_value_items):
        for input_args, cache_unit in list(cache_value_items):
            if cache_unit['access_count'] < safe_access_count:
                del _cache[func_id][input_args]

    if func is None:
        for function_id, specified_cache in _cache.items():
            del_unit(function_id, specified_cache.items())
    else:
        assert _is_function(func)
        del_unit(_retrieve_safe_function_id(func), _cache[_retrieve_safe_function_id(func)].items())


def clear(func=None):
    """
    Remove all cached items of a certain function or all functions.
    :param func: The certain function that will be cleared, if not given, clearing process will be executed
                 for all functions
    """
    if func is None:
        for item in _cache.values():
            item.clear()
    else:
        assert _is_function(func)
        _cache[_retrieve_safe_function_id(func)].clear()


def size(func=None):
    """
    Get the cache size of a certain function or all functions.
    :param func: The certain function that needs size calculation
    :return: The cache size
    """
    if func is None:
        return reduce(lambda accumulation, cache_value: len(accumulation) + len(cache_value)
                      if isinstance(accumulation, dict) else accumulation + len(cache_value),
                      _cache.values())
    else:
        assert _is_function(func)
        return len(_cache[_retrieve_safe_function_id(func)])


def _size_explicit(func_id):
    """
    Get the cache size by function id.
    :param func_id: The given function id
    :return: The cache size
    """
    return len(_cache[func_id])


def _hashable_args(args, kwargs):
    """
    Turn arguments in any shape into a hashable string.
    :param args: args
    :param kwargs: kwargs
    :return: a hashable string
    """
    if kwargs == {}:
        return str(args)
    else:
        return str(args) + json.dumps(kwargs)


def _is_function(obj):
    """
    Check if a object is function.
    :param obj: The object to be checked
    :return: True if it's a function, False otherwise
    """
    return hasattr(obj, '__call__')


def _retrieve_undecorated_function(func):
    """
    Retrieve the original (undecorated) function by a given decorated one.
    :param func: The decorated function
    :return: The original function
    """
    if not hasattr(func, 'original'):
        raise TypeError('Unable to retrieve the undecorated function: The function '
                        + func.__name__ + ' is not decorated with @cached')
    return func.original


def _error_unrecognized_function(func):
    """
    Raise an error caused by an unrecognized function.
    :param func:
    :return:
    """
    if not _is_function(func):
        raise TypeError(str(func) + ' is not a function')
    else:
        raise NameError('Function <' + func.__name__ + '> not found')


def _retrieve_safe_function_id(func):
    """
    Retrieve the id of the original (undecorated) function by a given decorated one.
    :param func: The decorated function
    :return: The id of the original function
    """
    function_id = id(_retrieve_undecorated_function(func))
    if function_id not in _cache.keys():  # panic
        _error_unrecognized_function(func)
    return function_id


def _include_undecorated_function(key='original'):
    """
    Decorator to include original function in a decorated one

    e.g.
    @include_undecorated_function()
    def shout(f):
        def _():
            string = f()
            return string.upper()
        return _


    @shout
    def hello():
        return 'hello world'

    print hello()               # HELLO WORLD
    print hello.original()      # hello world

    :param key: The key to access the original function
    :return: decorator
    """
    def this_decorator(decorator):
        def wrapper(func):
            decorated = decorator(func)
            setattr(decorated, key, func)
            return decorated
        return wrapper
    return this_decorator


if __name__ == '__main__':
    import sys
    sys.stderr.write('python-memoization v' + __version__ +
                     ': A minimalist functional caching lib for Python, with TTL and auto memory management support.\n')
    sys.stderr.write('Go to https://github.com/lonelyenvoy/python-memoization for usage and more details.\n')

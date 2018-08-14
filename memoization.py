import sys
import inspect

_cache = {}
_access_count = {}


def cached(max_items=None):
    def decorator(func):
        # type checks
        if not hasattr(func, '__call__'):
            raise TypeError('Unable to do memoization on non-function value ' + func)
        arg_spec = inspect.getargspec(func)
        if len(arg_spec.args) == 0 and arg_spec.varargs is None and arg_spec.keywords is None:
            raise TypeError('It\'s meaningless to do memoization on a function with no arguments')

        # init cache for func
        initial_function_id = id(func)
        _cache[initial_function_id] = {}
        _access_count[initial_function_id] = {}

        def wrapper(*args, **kwargs):
            input_args = _hashable_args(args, kwargs)
            function_id = id(func)
            specified_cache = _cache[function_id]
            specified_access_count = _access_count[function_id]
            if input_args in specified_cache.keys():  # already cached
                specified_access_count[input_args] += 1
                return specified_cache[input_args]
            else:  # not yet cached
                output = func(*args, **kwargs)  # execute func
                specified_cache[input_args] = output  # make cache
                specified_access_count[input_args] = 0
                return output
        return wrapper
    return decorator


def clean(safe_access_count=1):
    for func, counter in _access_count:
        for input_args, count in counter:
            if count < safe_access_count:
                del _cache[func][input_args]


def clear(func=None):
    if func is None:
        _cache.clear()
        _access_count.clear()
    else:
        function_id = id(func)
        if function_id not in _cache.keys():
            raise NameError('Function <' + func + '> not found')
        _cache[function_id].clear()
        _access_count[function_id].clear()


def size():
    return sys.getsizeof(_cache)


def _hashable_args(args, kwargs):
    kwargs_str = ''
    for key, value in kwargs:
        kwargs_str += key + '=' + value + ';'
    return str(args) + kwargs_str


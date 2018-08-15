import sys
import inspect
import warnings
from functools import wraps

_cache = {}


def cached(max_items=None):
    def decorator(func):
        # type checks
        if not _is_function(func):
            raise TypeError('Unable to do memoization on non-function object ' + str(func))
        arg_spec = inspect.getargspec(func)
        if len(arg_spec.args) == 0 and arg_spec.varargs is None and arg_spec.keywords is None:
            warnings.warn('It\'s meaningless to do memoization on a function with no arguments', SyntaxWarning)

        # init cache for func
        initial_function_id = id(func)
        _cache[initial_function_id] = {}

        @wraps(func)
        def wrapper(*args, **kwargs):
            input_args = _hashable_args(args, kwargs)
            function_id = id(func)
            specified_cache = _cache[function_id]
            if input_args in specified_cache.keys():  # already cached
                cache_unit = specified_cache[input_args]
                cache_unit['access_count'] += 1
                return cache_unit['result']
            else:  # not yet cached
                output = func(*args, **kwargs)  # execute func
                specified_cache[input_args] = {'result': output, 'access_count': 0}  # make cache
                return output
        return wrapper
    return decorator


def clean(safe_access_count=1, func=None):
    if func is None:
        for function_id, specified_cache in _cache.items():
            for input_args, cache_unit in specified_cache.items():
                if cache_unit['access_count'] < safe_access_count:
                    del _cache[function_id][input_args]
    else:
        function_id = id(_retrieve_undecorated_function(func))
        if function_id not in _cache.keys():  # panic
            if not _is_function(func):
                raise TypeError(str(func) + ' is not a function')
            else:
                raise NameError('Function <' + func.__name__ + '> not found')
        for input_args, cache_unit in _cache[function_id].items():
            if cache_unit['access_count'] < safe_access_count:
                del _cache[function_id][input_args]


def clear(func=None):
    if func is None:
        for item in _cache.values():
            item.clear()
    else:
        function_id = id(_retrieve_undecorated_function(func))
        if function_id not in _cache.keys():  # panic
            if not _is_function(func):
                raise TypeError(str(func) + ' is not a function')
            else:
                raise NameError('Function <' + func.__name__ + '> not found')
        _cache[function_id].clear()


def size():
    return sys.getsizeof(_cache)


def _hashable_args(args, kwargs):
    kwargs_str = ''
    for key, value in kwargs:
        kwargs_str += key + '=' + value + ';'
    return str(args) + kwargs_str


def _is_function(obj):
    return hasattr(obj, '__call__')


def _retrieve_undecorated_function(func):
    if func.func_closure is None:
        raise TypeError('Unable to retrieve the undecorated function: The function '
                        + func.__name__ + ' is not decorated')
    return func.func_closure[0].cell_contents

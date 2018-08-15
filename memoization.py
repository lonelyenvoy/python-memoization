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
    def del_unit(func_id, cache_value_items):
        for input_args, cache_unit in cache_value_items:
            if cache_unit['access_count'] < safe_access_count:
                del _cache[func_id][input_args]

    if func is None:
        for function_id, specified_cache in _cache.items():
            del_unit(function_id, specified_cache.items())
    else:
        del_unit(_retrieve_safe_function_id(func), _cache[_retrieve_safe_function_id(func)].items())


def clear(func=None):
    if func is None:
        for item in _cache.values():
            item.clear()
    else:
        _cache[_retrieve_safe_function_id(func)].clear()


def size(func=None):
    if func is None:
        return reduce(lambda accumulation, cache_value: len(accumulation) + len(cache_value)
                      if isinstance(accumulation, dict) else accumulation + len(cache_value),
                      _cache.values())
    else:
        return len(_cache[_retrieve_safe_function_id(func)])


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


def _error_unrecognized_function(func):
    if not _is_function(func):
        raise TypeError(str(func) + ' is not a function')
    else:
        raise NameError('Function <' + func.__name__ + '> not found')


def _retrieve_safe_function_id(func):
    function_id = id(_retrieve_undecorated_function(func))
    if function_id not in _cache.keys():  # panic
        _error_unrecognized_function(func)
    return function_id

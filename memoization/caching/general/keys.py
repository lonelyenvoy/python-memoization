from memoization.model import HashedList


def make_key(args, kwargs, kwargs_mark=(object(), )):
    """
    Make a cache key
    """
    key = args
    if kwargs:
        key += kwargs_mark
        for kwarg_key in sorted(kwargs.keys()):
            key += (kwarg_key, kwargs[kwarg_key])
    try:
        hash_value = hash(key)
    except TypeError:  # process unhashable types
        return str(key)
    else:
        return HashedList(key, hash_value)

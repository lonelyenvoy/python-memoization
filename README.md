# python-memoization

[![Version][aucsvg]][auc] [![Supports Python][pythonsvg]][python] [![Build Status][travismaster]][travis] [![PRs welcome][prsvg]][pr] [![Repository][repositorysvg]][repository] [![License][licensesvg]][license]

[aucsvg]: https://img.shields.io/badge/memoization-v0.1.1_alpha-brightgreen.svg
[auc]: https://github.com/lonelyenvoy/python-memoization

[pythonsvg]: https://img.shields.io/badge/python-2.6,_2.7,_3.4,_3.5,_3.6,_3.7,_3.8-brightgreen.svg
[python]: https://www.python.org

[travismaster]: https://travis-ci.org/lonelyenvoy/python-memoization.svg?branch=master
[travis]: https://travis-ci.org/lonelyenvoy/python-memoization

[prsvg]: https://img.shields.io/badge/PRs-welcome-blue.svg
[pr]: https://github.com/lonelyenvoy/python-memoization#contributing

[repositorysvg]: https://img.shields.io/badge/PyPI-pending-blue.svg
[repository]: https://pypi.org/project/memoization

[licensesvg]: https://img.shields.io/badge/License-MIT-blue.svg
[license]: https://github.com/lonelyenvoy/python-memoization/blob/master/LICENSE

A powerful caching library for Python, with TTL support and multiple algorithm options.


## Why choose this library?

Perhaps you know about [functools.lru_cache](https://docs.python.org/3/library/functools.html#functools.lru_cache) 
in Python 3, and you may be wondering why I am reinventing the wheel based on it. 

Well, because this one is more powerful. Please find below the comparison with lru_cache.

|Features|functools.lru_cache|memoization|
|--------|-------------------|-----------|
|Configurable max size|✔️|✔️|
|Thread safety|✔️|✔️|
|Flexible argument typing (typed & untyped)|✔️|Always typed|
|Cache statistics|✔️|✔️|
|LRU (Least Recently Used) as caching algorithm|✔️|✔️|
|LFU (Least Frequently Used) as caching algorithm|No support|✔️|
|FIFO (First In First Out) as caching algorithm|No support|✔️|
|TTL (Time-To-Live) support|No support|✔️|
|Support for unhashable arguments (dict, list, etc.)|No support|✔️|
|Partial cache clearing|No support|Pending implementation in v0.2.x|
|Python version|3.2+|2.6, 2.7, 3.4+|

To support function arguments with unhashable types, the caching is always typed, 
which means ```f(3)``` and ```f(3.0)``` will be treated as different calls and cached separately.

## Installation

```bash
pip install memoization
```

## Usage in 2 lines

```python
def fun(arg):
    return do_something_slow(arg)
```

Wanna caching this function? That's what you need:

```python
from memoization import cached

@cached
def fun(arg):
    return do_something_slow(arg)
```

The results of ```fun()``` are now magically cached! Repetitive calls to ```fun()``` with the same arguments run ```fun()``` only once, enhancing performance.


## Advanced features

### TTL (Time-To-Live)

```python
@cached(ttl=5)  # the cache expires after 5 seconds
def read_user_info(user):
    return expensive_db_query(user)
```

For impure functions, TTL will be a solution. This will be useful when the function returns resources that is valid only for a short time, e.g. fetching something from DB.

### Limited cache capacity
 
```python
@cached(max_size=128)  # the cache holds no more than 128 items
def get_compiled_binary(filename):
    return a_very_large_object(filename)
```

By default, if you don't specify ```max_size```, the cache can hold unlimited number of items.
When the cache is fully occupied, the former data will be overwritten by a certain algorithm described below.

### Choosing your caching algorithm

```python
from memoization import cached, CachingAlgorithmFlag

@cached(max_size=128, algorithm=CachingAlgorithmFlag.LFU)  # the cache overwrites items using the LFU algorithm
def func(arguments):
    ...
```

Possible values for ```algorithm``` are 
_Least Recently Used_ ```CachingAlgorithmFlag.LRU``` (default), 
_Least Frequently Used_ ```CachingAlgorithmFlag.LFU``` and 
_First In First Out_ ```CachingAlgorithmFlag.FIFO```.
This option is valid only when a ```max_size``` is explicitly specified.

### Thread safe?

```python
@cached(thread_safe=False)
def func(arguments):
    ...
```

```thread_safe``` is ```True``` by default. Setting it to ```False``` enhances performance.

### Knowing how well the cache is behaving

```python
>>> @cached
... def f(x): return x
... 
>>> f.cache_info()
CacheInfo(hits=0, misses=0, current_size=0, max_size=None, algorithm=<CachingAlgorithmFlag.LRU: 2>, ttl=None, thread_safe=True)
```

With ```cache_info```, you can retrieve the number of ```hits``` and ```misses``` of the cache, and other information indicating the caching status.

### Other APIs

- Access the original function ```f``` by ```f.__wrapped__```.
- Clear the cache by ```f.cache_clear()```.

## Contributing

This project welcomes contributions from anyone.
- [Submit bugs](https://github.com/lonelyenvoy/python-memoization/issues) and help me verify fixes.
- [Submit pull requests](https://github.com/lonelyenvoy/python-memoization/pulls) for bug fixes and features and discuss existing proposals. Please make sure that your PR passes the tests in ```memoization/test.py```.

## License

[The MIT License](https://github.com/lonelyenvoy/python-memoization/blob/master/LICENSE)

# python-memoization

[![Version][aucsvg]][auc] [![Supports Python][pythonsvg]][python] [![Build Status][travismaster]][travis]
[![Coverage Status][coverallssvg]][coveralls] [![Repository][repositorysvg]][repository] [![Downloads][downloadssvg]][repository]
[![PRs welcome][prsvg]][pr] [![License][licensesvg]][license]

[aucsvg]: https://img.shields.io/badge/memoization-v0.1.4-brightgreen.svg
[auc]: https://github.com/lonelyenvoy/python-memoization

[pythonsvg]: https://img.shields.io/pypi/pyversions/memoization.svg
[python]: https://www.python.org

[travismaster]: https://travis-ci.org/lonelyenvoy/python-memoization.svg?branch=master
[travis]: https://travis-ci.org/lonelyenvoy/python-memoization

[coverallssvg]: https://coveralls.io/repos/github/lonelyenvoy/python-memoization/badge.svg?branch=master
[coveralls]: https://coveralls.io/github/lonelyenvoy/python-memoization?branch=master

[repositorysvg]: https://img.shields.io/pypi/v/memoization.svg
[repository]: https://pypi.org/project/memoization

[downloadssvg]: https://img.shields.io/pypi/dm/memoization.svg

[prsvg]: https://img.shields.io/badge/PRs-welcome-blue.svg
[pr]: https://github.com/lonelyenvoy/python-memoization#contributing

[licensesvg]: https://img.shields.io/badge/License-MIT-blue.svg
[license]: https://github.com/lonelyenvoy/python-memoization/blob/master/LICENSE

A powerful caching library for Python, with TTL support and multiple algorithm options.


## Why choose this library?

Perhaps you know about [```functools.lru_cache```](https://docs.python.org/3/library/functools.html#functools.lru_cache)
in Python 3, and you may be wondering why I am reinventing the wheel.

Well, actually not. This lib is based on ```functools```. Please find below the comparison with ```lru_cache```.

|Features|```functools.lru_cache```|```memoization```|
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

```memoization``` solves some drawbacks of ```functools.lru_cache```:

1. ```lru_cache``` does not support __unhashable types__, which means function arguments cannot contain dict or list.

```python
>>> from functools import lru_cache
>>> @lru_cache()
... def f(x): return x
... 
>>> f([1, 2])  # unsupported
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: unhashable type: 'list'
```

2. ```lru_cache``` is vulnerable to [__hash collision attack__](https://learncryptography.com/hash-functions/hash-collision-attack)
   and can be hacked or compromised. In ```memoization```, caching is always typed, which means ```f(3)``` and 
   ```f(3.0)``` will be treated as different calls and cached separately. This prevents the attack from happening
   (or at least makes it a lot harder).

```python
>>> hash((1,))
3430019387558
>>> hash(3430019387558.0)  # two different arguments have an identical hash value
3430019387558
```


## Installation

```bash
pip install memoization
```

## Usage in 2 lines

```python
from memoization import cached

@cached
def func(arg):
    ...  # do something slow
```

Simple enough - the results of ```func()``` are cached. 
Repetitive calls to ```func()``` with the same arguments run ```func()``` only once, enhancing performance.


## Advanced features

Configurable options include `ttl`, `max_size`, `algorithm` and `thread_safe`.

### TTL (Time-To-Live)

```python
@cached(ttl=5)  # the cache expires after 5 seconds
def expensive_db_query(user_id):
    ...
```

For impure functions, TTL (in second) will be a solution. This will be useful when the function returns resources that is valid only for a short time, e.g. fetching something from databases.

### Limited cache capacity
 
```python
@cached(max_size=128)  # the cache holds no more than 128 items
def get_a_very_large_object(filename):
    ...
```

By default, if you don't specify ```max_size```, the cache can hold unlimited number of items.
When the cache is fully occupied, the former data will be overwritten by a certain algorithm described below.

### Choosing your caching algorithm

```python
from memoization import cached, CachingAlgorithmFlag

@cached(max_size=128, algorithm=CachingAlgorithmFlag.LFU)  # the cache overwrites items using the LFU algorithm
def func(arg):
    ...
```

Possible values for ```algorithm``` are:

- `CachingAlgorithmFlag.LRU`: _Least Recently Used_  (default)
- `CachingAlgorithmFlag.LFU`: _Least Frequently Used_ 
- `CachingAlgorithmFlag.FIFO`: _First In First Out_ 

This option is valid only when a ```max_size``` is explicitly specified.

### Thread safe?

```python
@cached(thread_safe=False)
def func(arg):
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

- `hits`: the number of cache hits
- `misses`: the number of cache misses
- `current_size`: the number of items that were cached
- `max_size`: the maximum number of items that can be cached (user-specified)
- `algorithm`: caching algorithm (user-specified)
- `ttl`: Time-To-Live value (user-specified)
- `thread_safe`: whether the cache is thread safe (user-specified)

### Other APIs

- Access the original function ```f``` by ```f.__wrapped__```.
- Clear the cache by ```f.cache_clear()```.

## Contributing

This project welcomes contributions from anyone.
- [Submit bugs](https://github.com/lonelyenvoy/python-memoization/issues) and help me verify fixes.
- [Submit pull requests](https://github.com/lonelyenvoy/python-memoization/pulls) for bug fixes and features and discuss existing proposals. Please make sure that your PR passes the tests in ```test/```.

## License

[The MIT License](https://github.com/lonelyenvoy/python-memoization/blob/master/LICENSE)

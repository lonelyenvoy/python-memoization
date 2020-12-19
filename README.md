# python-memoization

[![Repository][repositorysvg]][repository] [![Build Status][travismaster]][travis] [![Codacy Badge][codacysvg]][codacy]
[![Coverage Status][coverallssvg]][coveralls] [![Downloads][downloadssvg]][repository]
<br>
[![PRs welcome][prsvg]][pr] [![License][licensesvg]][license] [![Supports Python][pythonsvg]][python]


A powerful caching library for Python, with TTL support and multiple algorithm options.

If you like this work, please [star](https://github.com/lonelyenvoy/python-memoization) it on GitHub.

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
|Extensibility for new caching algorithms|No support|✔️|
|TTL (Time-To-Live) support|No support|✔️|
|Support for unhashable arguments (dict, list, etc.)|No support|✔️|
|Custom cache keys|No support|✔️|
|Partial cache clearing|No support|Pending implementation in v0.3.x|
|Python version|3.2+|3.4+|

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
   and can be hacked or compromised. Using this technique, attackers can make your program __unexpectedly slow__ by
   feeding the cached function with certain cleverly designed inputs. However, in ```memoization```, caching is always
   typed, which means ```f(3)``` and ```f(3.0)``` will be treated as different calls and cached separately. Also,
   you can build your own cache key with a unique hashing strategy. These measures __prevents the attack__ from
   happening (or at least makes it a lot harder).

```python
>>> hash((1,))
3430019387558
>>> hash(3430019387558.0)  # two different arguments have an identical hash value
3430019387558
```

3. Unlike `lru_cache`, `memoization` is designed to be highly extensible, which make it easy for developers to add and integrate
__any caching algorithms__ (beyond FIFO, LRU and LFU) into this library. See [Contributing Guidance](https://github.com/lonelyenvoy/python-memoization/blob/master/CONTRIBUTING.md) for further detail.


## Installation

```bash
pip install -U memoization
```


## 1-Minute Tutorial

```python
from memoization import cached

@cached
def func(arg):
    ...  # do something slow
```

Simple enough - the results of ```func()``` are cached. 
Repetitive calls to ```func()``` with the same arguments run ```func()``` only once, enhancing performance.

>:warning:__WARNING:__ for functions with unhashable arguments, the default setting may not enable `memoization` to work properly. See [custom cache keys](https://github.com/lonelyenvoy/python-memoization#custom-cache-keys) section below for details.

## 15-Minute Tutorial

You will learn about the advanced features in the following tutorial, which enable you to customize `memoization` .

Configurable options include `ttl`, `max_size`, `algorithm`, `thread_safe`, `order_independent` and `custom_key_maker`.

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

### Order-independent cache key

By default, the following function calls will be treated differently and cached twice, which means the cache misses at the second call.

```python
func(a=1, b=1)
func(b=1, a=1)
```

You can avoid this behavior by passing an `order_independent` argument to the decorator, although it will slow down the performance a little bit. 

```python
@cached(order_independent=True)
def func(**kwargs):
    ...
```

### Custom cache keys

Prior to memorize your function inputs and outputs (i.e. putting them into a cache), `memoization` needs to
build a __cache key__ using the inputs, so that the outputs can be retrieved later.

> By default, `memoization` tries to combine all your function
arguments and calculate its hash value using `hash()`. If it turns out that parts of your arguments are
unhashable, `memoization` will fall back to turning them into a string using `str()`. This behavior relies
on the assumption that the string exactly represents the internal state of the arguments, which is true for
built-in types.

However, this is not true for all objects. __If you pass objects which are
instances of non-built-in classes, sometimes you will need to override the default key-making procedure__,
because the `str()` function on these objects may not hold the correct information about their states.

Here are some suggestions. __Implementations of a valid key maker__:

- MUST be a function with the same signature as the cached function.
- MUST produce unique keys, which means two sets of different arguments always map to two different keys.
- MUST produce hashable keys, and a key is comparable with another key (`memoization` only needs to check for their equality).
- should compute keys efficiently and produce small objects as keys.

Example:

```python
def get_employee_id(employee):
    return employee.id

@cached(custom_key_maker=get_employee_id)
def calculate_performance(employee):
    ...
```

Note that writing a robust key maker function can be challenging in some situations. If you find it difficult,
feel free to ask me for help by submitting an [issue](https://github.com/lonelyenvoy/python-memoization/issues).


### Knowing how well the cache is behaving

```python
>>> @cached
... def f(x): return x
... 
>>> f.cache_info()
CacheInfo(hits=0, misses=0, current_size=0, max_size=None, algorithm=<CachingAlgorithmFlag.LRU: 2>, ttl=None, thread_safe=True, order_independent=False, use_custom_key=False)
```

With ```cache_info```, you can retrieve the number of ```hits``` and ```misses``` of the cache, and other information indicating the caching status.

- `hits`: the number of cache hits
- `misses`: the number of cache misses
- `current_size`: the number of items that were cached
- `max_size`: the maximum number of items that can be cached (user-specified)
- `algorithm`: caching algorithm (user-specified)
- `ttl`: Time-To-Live value (user-specified)
- `thread_safe`: whether the cache is thread safe (user-specified)
- `order_independent`: whether the cache is kwarg-order-independent (user-specified)
- `use_custom_key`: whether a custom key maker is used

### Other APIs

- Access the original function ```f``` by ```f.__wrapped__```.
- Clear the cache by ```f.cache_clear()```.


## Contributing

This project welcomes contributions from anyone.
- [Read Contributing Guidance](https://github.com/lonelyenvoy/python-memoization/blob/master/CONTRIBUTING.md) first.
- [Submit bugs](https://github.com/lonelyenvoy/python-memoization/issues) and help me verify fixes.
- [Submit pull requests](https://github.com/lonelyenvoy/python-memoization/pulls) for bug fixes and features and discuss existing proposals. Please make sure that your PR passes the tests in ```test.py```.
- [See contributors](https://github.com/lonelyenvoy/python-memoization/blob/master/CONTRIBUTORS.md) of this project.


## License

[The MIT License](https://github.com/lonelyenvoy/python-memoization/blob/master/LICENSE)


[pythonsvg]: https://img.shields.io/pypi/pyversions/memoization.svg
[python]: https://www.python.org

[travismaster]: https://travis-ci.org/lonelyenvoy/python-memoization.svg?branch=master
[travis]: https://travis-ci.org/lonelyenvoy/python-memoization

[coverallssvg]: https://coveralls.io/repos/github/lonelyenvoy/python-memoization/badge.svg?branch=master
[coveralls]: https://coveralls.io/github/lonelyenvoy/python-memoization?branch=master

[repositorysvg]: https://img.shields.io/pypi/v/memoization
[repository]: https://pypi.org/project/memoization

[downloadssvg]: https://img.shields.io/pypi/dm/memoization

[prsvg]: https://img.shields.io/badge/pull_requests-welcome-blue.svg
[pr]: https://github.com/lonelyenvoy/python-memoization#contributing

[licensesvg]: https://img.shields.io/badge/license-MIT-blue.svg
[license]: https://github.com/lonelyenvoy/python-memoization/blob/master/LICENSE

[codacysvg]: https://api.codacy.com/project/badge/Grade/52c68fb9de6b4b149e77e8e173616db6
[codacy]: https://www.codacy.com/manual/petrinchor/python-memoization?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=lonelyenvoy/python-memoization&amp;utm_campaign=Badge_Grade

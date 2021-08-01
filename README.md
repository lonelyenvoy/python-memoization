# python-memoization

[![Repository][repositorysvg]][repository] [![Build Status][travismaster]][travis] [![Codacy Badge][codacysvg]][codacy]
[![Coverage Status][coverallssvg]][coveralls] [![Downloads][downloadssvg]][repository]
<br>
[![PRs welcome][prsvg]][pr] [![License][licensesvg]][license] [![Supports Python][pythonsvg]][python]


A powerful caching library for Python, with TTL support and multiple algorithm options.

If you like this work, please [star](https://github.com/lonelyenvoy/python-memoization) it on GitHub.

## Why choose this library?

Perhaps you know about [```functools.lru_cache```](https://docs.python.org/3/library/functools.html#functools.lru_cache)
in Python 3, and you may be wondering why we are reinventing the wheel.

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
|On-demand partial cache clearing|No support|✔️|
|Iterating through the cache|No support|✔️|
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
>>> hash(3430019387558.0)  # two different arguments with an identical hash value
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
    return employee.id  # returns a string or a integer

@cached(custom_key_maker=get_employee_id)
def calculate_performance(employee):
    ...
```

Note that writing a robust key maker function can be challenging in some situations. If you find it difficult,
feel free to ask for help by submitting an [issue](https://github.com/lonelyenvoy/python-memoization/issues).


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

- Access the original undecorated function `f` by `f.__wrapped__`.
- Clear the cache by `f.cache_clear()`.
- Check whether the cache is empty by `f.cache_is_empty()`.
- Check whether the cache is full by `f.cache_is_full()`.
- Disable `SyntaxWarning` by `memoization.suppress_warnings()`.

## Advanced API References

<details>
<summary>Details</summary>

### Checking whether the cache contains something

#### cache_contains_argument(function_arguments, alive_only)

```
Return True if the cache contains a cached item with the specified function call arguments

:param function_arguments:  Can be a list, a tuple or a dict.
                            - Full arguments: use a list to represent both positional arguments and keyword
                              arguments. The list contains two elements, a tuple (positional arguments) and
                              a dict (keyword arguments). For example,
                                f(1, 2, 3, a=4, b=5, c=6)
                              can be represented by:
                                [(1, 2, 3), {'a': 4, 'b': 5, 'c': 6}]
                            - Positional arguments only: when the arguments does not include keyword arguments,
                              a tuple can be used to represent positional arguments. For example,
                                f(1, 2, 3)
                              can be represented by:
                                (1, 2, 3)
                            - Keyword arguments only: when the arguments does not include positional arguments,
                              a dict can be used to represent keyword arguments. For example,
                                f(a=4, b=5, c=6)
                              can be represented by:
                                {'a': 4, 'b': 5, 'c': 6}

:param alive_only:          Whether to check alive cache item only (default to True).

:return:                    True if the desired cached item is present, False otherwise.
```

#### cache_contains_result(return_value, alive_only)

```
Return True if the cache contains a cache item with the specified user function return value. O(n) time
complexity.

:param return_value:        A return value coming from the user function.

:param alive_only:          Whether to check alive cache item only (default to True).

:return:                    True if the desired cached item is present, False otherwise.
```

### Iterating through the cache

#### cache_arguments()

```
Get user function arguments of all alive cache elements

see also: cache_items()

Example:
   @cached
   def f(a, b, c, d):
       ...
   f(1, 2, c=3, d=4)
   for argument in f.cache_arguments():
       print(argument)  # ((1, 2), {'c': 3, 'd': 4})

:return: an iterable which iterates through a list of a tuple containing a tuple (positional arguments) and
        a dict (keyword arguments)
```

#### cache_results()

```
Get user function return values of all alive cache elements

see also: cache_items()

Example:
   @cached
   def f(a):
       return a
   f('hello')
   for result in f.cache_results():
       print(result)  # 'hello'

:return: an iterable which iterates through a list of user function result (of any type)
```

#### cache_items()

```
Get cache items, i.e. entries of all alive cache elements, in the form of (argument, result).

argument: a tuple containing a tuple (positional arguments) and a dict (keyword arguments).
result: a user function return value of any type.

see also: cache_arguments(), cache_results().

Example:
   @cached
   def f(a, b, c, d):
       return 'the answer is ' + str(a)
   f(1, 2, c=3, d=4)
   for argument, result in f.cache_items():
       print(argument)  # ((1, 2), {'c': 3, 'd': 4})
       print(result)    # 'the answer is 1'

:return: an iterable which iterates through a list of (argument, result) entries
```

#### cache_for_each()

```
Perform the given action for each cache element in an order determined by the algorithm until all
elements have been processed or the action throws an error

:param consumer:           an action function to process the cache elements. Must have 3 arguments:
                             def consumer(user_function_arguments, user_function_result, is_alive): ...
                           user_function_arguments is a tuple holding arguments in the form of (args, kwargs).
                             args is a tuple holding positional arguments.
                             kwargs is a dict holding keyword arguments.
                             for example, for a function: foo(a, b, c, d), calling it by: foo(1, 2, c=3, d=4)
                             user_function_arguments == ((1, 2), {'c': 3, 'd': 4})
                           user_function_result is a return value coming from the user function.
                           is_alive is a boolean value indicating whether the cache is still alive
                           (if a TTL is given).
```

### Removing something from the cache

#### cache_clear()

```
Clear the cache and its statistics information
```

#### cache_remove_if(predicate)

```
Remove all cache elements that satisfy the given predicate

:param predicate:           a predicate function to judge whether the cache elements should be removed. Must
                            have 3 arguments, and returns True or False:
                              def consumer(user_function_arguments, user_function_result, is_alive): ...
                            user_function_arguments is a tuple holding arguments in the form of (args, kwargs).
                              args is a tuple holding positional arguments.
                              kwargs is a dict holding keyword arguments.
                              for example, for a function: foo(a, b, c, d), calling it by: foo(1, 2, c=3, d=4)
                              user_function_arguments == ((1, 2), {'c': 3, 'd': 4})
                            user_function_result is a return value coming from the user function.
                            is_alive is a boolean value indicating whether the cache is still alive
                            (if a TTL is given).

:return:                    True if at least one element is removed, False otherwise.
```

</details>

## Q&A

1. **Q: There are duplicated code in `memoization` and most of them can be eliminated by using another level of
abstraction (e.g. classes and multiple inheritance). Why not refactor?**

   A: We would like to keep the code in a proper level of abstraction. However, these abstractions make it run slower.
As this is a caching library focusing on speed, we have to give up some elegance for better performance. Refactoring
is our future work.


2. **Q: I have submitted an issue and not received a reply for a long time. Anyone can help me?**

   A: Sorry! We are not working full-time, but working voluntarily on this project, so you might experience some delay.
We appreciate your patience.


## Contributing

This project welcomes contributions from anyone.
- [Read Contributing Guidance](https://github.com/lonelyenvoy/python-memoization/blob/master/CONTRIBUTING.md) first.
- [Submit bugs](https://github.com/lonelyenvoy/python-memoization/issues) and help us verify fixes.
- [Submit pull requests](https://github.com/lonelyenvoy/python-memoization/pulls) for bug fixes and features and discuss existing proposals. Please make sure that your PR passes the tests in ```test.py```.
- [See contributors](https://github.com/lonelyenvoy/python-memoization/blob/master/CONTRIBUTORS.md) of this project.


## License

[The MIT License](https://github.com/lonelyenvoy/python-memoization/blob/master/LICENSE)


[pythonsvg]: https://img.shields.io/pypi/pyversions/memoization.svg
[python]: https://www.python.org

[travismaster]: https://travis-ci.com/lonelyenvoy/python-memoization.svg?branch=master
[travis]: https://travis-ci.com/lonelyenvoy/python-memoization

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

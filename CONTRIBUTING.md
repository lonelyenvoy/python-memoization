# Contributing

Thank you for your contribution to this project. If your solution works well, I will merge your pull requests ASAP. 
**Feel free to add yourself to [`CONTRIBUTORS.md`](https://github.com/lonelyenvoy/python-memoization/blob/master/CONTRIBUTORS.md) :-D**

## Bugs...

- If you find a bug, please report it with an [issue](https://github.com/lonelyenvoy/python-memoization/issues).
- If you want to fix a bug, please submit [pull requests](https://github.com/lonelyenvoy/python-memoization/pulls).

## Want to implement a cooler caching algorithm?

If you find the given algorithms (FIFO, LRU, and LFU) unable to satisfiy your requirements, 
you can add any algorithms to this project. Since it is designed to be extensible, 
this can be easily done in a few steps:

### Step 1: Register your algorithm in `CachingAlgorithmFlag`

Please locate this file: `memoization.constant.flag.CachingAlgorithmFlag`

```python
class CachingAlgorithmFlag(enum.IntFlag):
    """
    Use this class to specify which caching algorithm you would like to use
    """
    FIFO = 1    # First In First Out
    LRU = 2     # Least Recently Used
    LFU = 4     # Least Frequently Used

```

By default, these three internal algorithms are registered. 
Add your algorithms here, like `LRU_K = 8`. Note that the flag value should be a power of 2.


### Step 2: Write your caching toolkit with a wrapper function

Please create a new python file in `memoization.caching` with the filename
containing the name of your algorithm and a postfix `_cache`, like `lru_k_cache.py`.

In this file, implement a `get_caching_wrapper` function, which creates a wrapper 
for any given user function. The signature of this function should be:
```python
def get_caching_wrapper(user_function, max_size, ttl, algorithm, thread_safe):
    ...
```

Note that you should also attach several members to the created wrapper, 
so that users can do some operations. 

This two functions are *required*:

```python
# To see the statistics information
wrapper.cache_info()

# To clear the cache
wrapper.cache_clear()
```

For testing purposes, this two members are *optional*, but recommended:
```python
# Access to the cache which is typically a hash map with function 
# arguments as its key and function return values as its value
wrapper._cache

# Get an ordered list which represents the internal caching orders,
# from the most important key-value entry (aka the least possible one 
# to be evicted from cache) to the least important one (aka the most 
# possible one to be evicted)
wrapper._get_caching_list()
```

Please refer to `fifo_cache.py` as an example. Your code should looks like:

```python
def get_caching_wrapper(user_function, max_size, ttl, algorithm, thread_safe):
    """
    Get a caching wrapper for LRU_K cache
    """

    def wrapper(*args, **kwargs):
        """
        The actual wrapper
        """
        ...

    def cache_clear():
        """
        Clear the cache and its statistics information
        """
        ...

    def cache_info():
        """
        Show statistics information
        :return: a CacheInfo object describing the cache
        """
        ...

    # expose operations to wrapper
    wrapper.cache_clear = cache_clear
    wrapper.cache_info = cache_info
    wrapper._cache = ...
    wrapper._get_caching_list = ...

    return wrapper

```

### Step 3: Add a mapping from `CachingAlgorithmFlag` to `algorithm_mapping`

Please locate this file: `memoization.config.algorithm_mapping`

Inside it you will see a mapping, which is by default:

```python
algorithm_mapping = {
    CachingAlgorithmFlag.FIFO: fifo_cache,
    CachingAlgorithmFlag.LRU: lru_cache,
    CachingAlgorithmFlag.LFU: lfu_cache,
}
```

Add your newly created caching toolkits to the dictionary like:
```python
import memoization.caching.lru_k_cache as lru_k_cache

...
algorithm_mapping = {
    ...
    CachingAlgorithmFlag.LRU_K: lru_k_cache,
}
```


### Step 4: Validate your design

Please run the script `memoization.util.algorithm_extension_validator` to perform
type checking on your newly implemented algorithm. The validator will tell you 
if anything goes wrong. If your code works well, you will see:

```
[Validation OK]
Congratulations! Your extended algorithm passed the validation. Thanks for your efforts.
Please understand that this validator only ensure that the typings of your extension are correct. You are still required to write test cases for your algorithms.
```

Remember that this validator does **NOT** automatically tests your algorithms, 
nor does it substitute `test.py`. You are required to write test cases and make 
your code pass them before you submit a pull request.


### Step 5: Enjoy!


## Acknowledgements

Thank you again, developer, for helping me improve this project.

# python-memoization

[![auc][aucsvg]][auc] [![License][licensesvg]][license]

[aucsvg]: https://img.shields.io/badge/memoization-v0.0.6-brightgreen.svg
[auc]: https://github.com/lonelyenvoy/python-memoization

[licensesvg]: https://img.shields.io/badge/License-MIT-blue.svg
[license]: https://github.com/lonelyenvoy/python-memoization/blob/master/LICENSE

A minimalist functional caching lib for Python, with TTL and auto memory management support.


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

@cached()
def fun(arg):
    return do_something_slow(arg)
```

Repetitive calls to ```fun()``` with the same arguments then run ```fun()``` only once.


## Advanced topics

### TTL (Time-To-Live)

```python
@cached(ttl=5)  # cache expires after 5 seconds
def read_user_info(user):
    return expensive_db_query(user)
```

For impure functions, TTL will be a solution.

### Limited cache capacity
 
```python
@cached(max_items=1000)  # cache holds no more than 1000 items
def get_compiled_binary(filename):
    return a_very_large_object(filename)
```

When the cache is fully occupied, the data first came will be overwritten.


## Contributing

Any improvement or bug-fixing is welcome. Create a [pull request](https://github.com/lonelyenvoy/python-memoization/pulls) when you are done.

## License

[The MIT License](https://github.com/lonelyenvoy/python-memoization/blob/master/LICENSE)

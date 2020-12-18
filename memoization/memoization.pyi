from typing import Any, Callable, Optional, overload
from typing_extensions import Protocol

from memoization.constant.flag import CachingAlgorithmFlag as CachingAlgorithmFlagType
from memoization.model import CacheInfo


class CachedFunction(Protocol):
    def __call__(self, *args, **kwargs) -> Any: ...
    __wrapped__: Callable
    cache_clear: Callable[[], None]
    cache_info: Callable[[], CacheInfo]

# Bare decorator usage - @cache
@overload
def cached(user_function: Callable = ...) -> CachedFunction: ...

# Decorator with optional arguments - @cached(...)
@overload
def cached(max_size: Optional[int] = ...,
           ttl: Optional[float] = ...,
           algorithm: CachingAlgorithmFlagType = ...,
           thread_safe: bool = ...,
           order_independent: bool = ...,
           custom_key_maker: Optional[Callable] = ...) -> Callable[[Callable], Callable]: ...

CachingAlgorithmFlag = CachingAlgorithmFlagType

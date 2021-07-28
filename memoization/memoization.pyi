from typing import Any, Callable, Optional, overload, TypeVar, Hashable

from memoization.constant.flag import CachingAlgorithmFlag as CachingAlgorithmFlagType
from memoization.type.model import CachedFunction

T = TypeVar('T', bound=Callable[..., Any])

__version__: str

# Decorator with optional arguments - @cached(...)
@overload
def cached(max_size: Optional[int] = ...,
           ttl: Optional[float] = ...,
           algorithm: Optional[int] = ...,
           thread_safe: Optional[bool] = ...,
           order_independent: Optional[bool] = ...,
           custom_key_maker: Optional[Callable[..., Hashable]] = ...) -> Callable[[T], CachedFunction[T]]: ...

# Bare decorator usage - @cache
@overload
def cached(user_function: T = ...) -> CachedFunction[T]: ...

def suppress_warnings(should_warn: bool = ...) -> None: ...

CachingAlgorithmFlag = CachingAlgorithmFlagType

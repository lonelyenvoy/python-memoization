from typing import TypeVar, Callable, Any, Protocol

from memoization.model import CacheInfo

T = TypeVar('T', bound=Callable[..., Any])


class CachedFunction(Protocol[T]):
    __call__: T
    __wrapped__: T
    def cache_clear(self) -> None: ...
    def cache_info(self) -> CacheInfo: ...

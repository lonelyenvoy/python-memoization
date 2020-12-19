from types import ModuleType
from typing import Callable, Any, Optional, Hashable, TypeVar

from memoization.type.model import CachedFunction

T = TypeVar('T', bound=Callable[..., Any])

class CacheToolkit(ModuleType):
    def get_caching_wrapper(self,
                            user_function: T,
                            max_size: Optional[int],
                            ttl: Optional[float],
                            algorithm: Optional[int],
                            thread_safe: Optional[bool],
                            order_independent: Optional[bool],
                            custom_key_maker: Optional[Callable[..., Hashable]]) -> CachedFunction[T]: ...

def get_cache_toolkit(algorithm: int = ...) -> CacheToolkit: ...

from typing import Callable, Optional, Any, TypeVar, Protocol, Hashable

from memoization.type.model import CachedFunction

T = TypeVar('T', bound=Callable[..., Any])


def get_caching_wrapper(user_function: T,
                        max_size: Optional[int],
                        ttl: Optional[float],
                        algorithm: Optional[int],
                        thread_safe: Optional[bool],
                        order_independent: Optional[bool],
                        custom_key_maker: Optional[Callable[..., Hashable]]) -> CachedFunction[T]: ...

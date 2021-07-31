from typing import TypeVar, Callable, Any, Protocol, Union, List, Tuple, Dict, Optional

from memoization.model import CacheInfo

T = TypeVar('T', bound=Callable[..., Any])


class CachedFunction(Protocol[T]):
    __call__: T
    __wrapped__: T
    def cache_clear(self) -> None: ...
    def cache_info(self) -> CacheInfo: ...
    def cache_is_empty(self) -> bool: ...
    def cache_is_full(self) -> bool: ...
    def cache_contains_argument(self, function_arguments: Union[List, Tuple, Dict[str, Any]], alive_only: bool = ...) -> bool: ...
    def cache_contains_key(self, key: Any, alive_only: bool = ...) -> bool: ...
    def cache_contains_result(self, return_value: Any, alive_only: bool = ...) -> bool: ...
    def cache_for_each(self, consumer: Callable[[Any, Any, bool], None]) -> None: ...
    def cache_remove_if(self, predicate: Callable[[Any, Any, bool], bool]) -> bool: ...
    def cache_make_key(self, args: Tuple, kwargs: Optional[Dict[str, Any]], kwargs_mark: Tuple[object] = ...) -> Any: ...

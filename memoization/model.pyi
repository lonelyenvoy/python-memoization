from typing import Any, Tuple, Optional

class DummyWithable:
    __slots__: Tuple[str] = ...
    def __enter__(self) -> None: ...
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...

class HashedList:
    hash_value: int = ...
    __slots__: Tuple[str]
    def __init__(self, tup: Tuple[Any], hash_value: int) -> None: ...
    def __hash__(self) -> int: ...

class CacheInfo:
    hits: int
    misses: int
    current_size: int
    max_size: Optional[int]
    algorithm: int
    ttl: Optional[float]
    thread_safe: bool
    order_independent: bool
    use_custom_key: bool
    def __init__(
            self,
            hits: int,
            misses: int,
            current_size: int,
            max_size: Optional[int],
            algorithm: int,
            ttl: Optional[float],
            thread_safe: bool,
            order_independent: bool,
            use_custom_key: bool,
    ): ...

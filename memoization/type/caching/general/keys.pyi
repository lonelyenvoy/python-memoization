from typing import Any, Tuple, Dict, Union, Optional

from memoization.model import HashedList


def make_key(args: Tuple[Any],
             kwargs: Optional[Dict[str, Any]],
             kwargs_mark: Tuple[object] = ...) -> Union[str, HashedList]: ...

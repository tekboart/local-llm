from typing import Sequence, Iterator, Any

from collections.abc import Sequence
from typing import Any, Generator, Optional

def flatten(
    nested_sequence: Sequence[Any],
    max_depth: Optional[int] = None,
    _depth: int = 0,
    _seen: Optional[set] = None
) -> Generator[Any, None, None]:
    """
    Flattens a nested sequence up to `max_depth` levels.
    Strings and bytes are treated as atomic elements.
    Cyclic references are safely ignored.
    """
    if _seen is None:
        _seen = set()

    obj_id = id(nested_sequence)
    if obj_id in _seen:  # Prevent infinite loops
        return
    _seen.add(obj_id)

    for item in nested_sequence:
        if (
            isinstance(item, Sequence)
            and not isinstance(item, (str, bytes))
            and (max_depth is None or _depth < max_depth)
        ):
            yield from flatten(item, max_depth=max_depth, _depth=_depth + 1, _seen=_seen)
        else:
            yield item

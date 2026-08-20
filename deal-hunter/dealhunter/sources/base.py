"""Source adapter interface.

A Source knows how to fetch a batch of normalized ``Listing`` objects from one
place. Keep network code isolated here so the rest of the pipeline stays pure
and testable.
"""

from __future__ import annotations

import abc
from typing import Iterable

from ..models import Listing


class Source(abc.ABC):
    name: str = "source"

    @abc.abstractmethod
    def fetch(self) -> Iterable[Listing]:
        """Return current listings. Implementations should be defensive:
        network/parse errors should raise, and the pipeline will isolate a
        failing source without killing the whole run."""
        raise NotImplementedError

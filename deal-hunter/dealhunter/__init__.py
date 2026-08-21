"""Deal Hunter — agent that finds under-priced listings and reports them.

The package is intentionally small and dependency-light so it can run as a
scheduled cloud agent (a "Routine"). The pure logic (pricing, scoring, memory,
digest) has no network dependency and is unit-tested; only the source adapters
touch the network.
"""

__version__ = "0.1.0"

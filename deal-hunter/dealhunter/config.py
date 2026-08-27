"""Load and validate configuration.

Config is YAML if PyYAML is available, else JSON — kept dependency-optional so a
minimal environment can still run with a JSON config.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Config:
    sources: list[dict] = field(default_factory=lambda: [{"type": "sample"}])
    watch_terms: list[str] = field(default_factory=list)
    baselines: dict[str, float] = field(default_factory=dict)
    min_discount: float = 0.20
    min_score: float = 25.0
    min_samples: int = 3
    max_deals: int = 25
    max_per_category: int = 0        # 0 = off; N = show up to N deals per category
    max_price: float = 0.0           # >0 switches to "list everything at/under this price"
    min_price: float = 0.0           # in max_price mode, ignore anything cheaper than this
    list_all: bool = False           # list every fetched listing (jobs: price not relevant)
    state_path: str = "state/seen.json"
    output_path: str = "digests/latest.md"
    translate: bool = False          # enable free NL->RU translation in the digest
    translate_from: str = "nl"
    translate_to: str = "ru"

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Config":
        cfg = Config()
        for key, value in (data or {}).items():
            if hasattr(cfg, key):
                setattr(cfg, key, value)
        cfg.baselines = {str(k): float(v) for k, v in (cfg.baselines or {}).items()}
        return cfg


def load_config(path: str | None) -> Config:
    if not path:
        return Config()
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    data: dict[str, Any]
    if path.endswith((".yaml", ".yml")):
        try:
            import yaml  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "PyYAML is required for YAML config; use JSON or "
                "`pip install pyyaml`"
            ) from exc
        data = yaml.safe_load(text) or {}
    else:
        data = json.loads(text or "{}")
    return Config.from_dict(data)

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    soda_domain: str
    dataset_id: str
    lookback_hours: int
    page_limit: int
    max_pages: int


def load_settings() -> Settings:
    def _get_int(name: str, default: int) -> int:
        val = os.getenv(name, str(default)).strip()
        return int(val)

    soda_domain = os.getenv("SODA_DOMAIN", "data.texas.gov").strip()
    dataset_id = os.getenv("DATASET_ID", "qh8x-rm8r").strip()

    return Settings(
        soda_domain=soda_domain,
        dataset_id=dataset_id,
        lookback_hours=_get_int("LOOKBACK_HOURS", 24),
        page_limit=_get_int("PAGE_LIMIT", 1000),
        max_pages=_get_int("MAX_PAGES", 2),
    )


from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import requests


class SodaClient:
    def __init__(self, domain: str, dataset_id: str, timeout_s: int = 30) -> None:
        self.domain = domain
        self.dataset_id = dataset_id
        self.timeout_s = timeout_s

    @property
    def resource_url(self) -> str:

        return f"https://{self.domain}/resource/{self.dataset_id}.json"

    def fetch_updated_since(
        self,
        lookback_hours: int,
        page_limit: int,
        max_pages: int,
    ) -> list[dict[str, Any]]:
        """
        Fetch records updated in the last `lookback_hours`, paging with $limit/$offset.
        """
        since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

        since_str = since.replace(microsecond=0).isoformat().replace("+00:00", "Z")

        all_rows: list[dict[str, Any]] = []
        offset = 0

        for page in range(max_pages):
            params = {
                "$limit": page_limit,
                "$offset": offset,
                "$where": f":updated_at >= '{since_str}'",
                "$order": ":updated_at ASC",
            }

            resp = requests.get(self.resource_url, params=params, timeout=self.timeout_s)
            resp.raise_for_status()
            rows = resp.json()

            if not isinstance(rows, list):
                raise ValueError(f"Unexpected response type: {type(rows)}")

            all_rows.extend(rows)

        
            if len(rows) < page_limit:
                break

            offset += page_limit

        return all_rows

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from services.ingest.src.config import load_settings
from services.ingest.src.soda_client import SodaClient


def main() -> None:
    load_dotenv()

    settings = load_settings()
    client = SodaClient(domain=settings.soda_domain, dataset_id=settings.dataset_id)

    rows = client.fetch_updated_since(
        lookback_hours=settings.lookback_hours,
        page_limit=settings.page_limit,
        max_pages=settings.max_pages,
    )

    run_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path("data/raw") / f"dataset={settings.dataset_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"run={run_ts}.json"
    out_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    print("=== Texas Procurement Watch: Local Ingest ===")
    print(f"Domain:        {settings.soda_domain}")
    print(f"Dataset ID:    {settings.dataset_id}")
    print(f"Lookback:      {settings.lookback_hours} hours")
    print(f"Pulled rows:   {len(rows)}")
    print(f"Saved to:      {out_path}")

    if rows:
        print("\nSample keys from first row:")
        print(sorted(rows[0].keys())[:25])


if __name__ == "__main__":
    main()

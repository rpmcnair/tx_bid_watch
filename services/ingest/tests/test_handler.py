from __future__ import annotations

from src import handler
from src.watch import WatchResult
from src.config import Settings


def test_lambda_handler_returns_dict(monkeypatch):
    monkeypatch.setattr(
        handler,
        "load_settings",
        lambda: Settings(
            soda_domain="data.texas.gov",
            dataset_id="qh8x-rm8r",
            lookback_hours=24,
            page_limit=1000,
            max_pages=2,
            raw_bucket=None,
            raw_prefix="raw",
        ),
    )

    monkeypatch.setattr(
        handler,
        "run_watch",
        lambda settings: WatchResult(
            run_ts="20260224T111111Z",
            dataset_id="qh8x-rm8r",
            domain="data.texas.gov",
            lookback_hours=24,
            pulled_rows=0,
            output_path="data/raw/...",
        ),
    )

    out = handler.lambda_handler({}, None)
    assert isinstance(out, dict)
    assert out["dataset_id"] == "qh8x-rm8r"
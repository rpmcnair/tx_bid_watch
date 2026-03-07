from __future__ import annotations

from src.config import Settings
from src import watch


def test_run_watch_uses_s3_when_bucket_set(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    fake_rows = [{"id": 1}]
    monkeypatch.setattr(watch, "_run_timestamp", lambda: "20260224T111111Z")

    class DummyClient:
        def __init__(self, domain: str, dataset_id: str) -> None:
            pass

        def fetch_updated_since(self, lookback_hours: int, page_limit: int, max_pages: int):
            return fake_rows

    monkeypatch.setattr(watch, "SodaClient", DummyClient)

    # avoid real boto3 by patching the writer
    monkeypatch.setattr(watch, "write_raw_json_s3", lambda **kwargs: "raw/dataset=qh8x-rm8r/run=20260224T111111Z.json")

    settings = Settings(
        soda_domain="data.texas.gov",
        dataset_id="qh8x-rm8r",
        lookback_hours=24,
        page_limit=1000,
        max_pages=2,
        raw_bucket="my-bucket",
        raw_prefix="raw",
    )

    result = watch.run_watch(settings)
    assert result.output_path == "s3://my-bucket/raw/dataset=qh8x-rm8r/run=20260224T111111Z.json"
    assert result.pulled_rows == 1
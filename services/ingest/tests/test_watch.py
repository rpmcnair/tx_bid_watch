from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from src import watch
from src.config import Settings


def test_run_timestamp_format():
    ts = watch._run_timestamp()
    # format: YYYYMMDDTHHMMSSZ
    assert re.fullmatch(r"\d{8}T\d{6}Z", ts), f"Bad timestamp format: {ts}"


def test_write_raw_json_local_writes_expected_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    rows = [{"a": 1}, {"a": 2}]
    dataset_id = "qh8x-rm8r"
    run_ts = "20260224T123456Z"

    out_path = watch.write_raw_json_local(rows, dataset_id, run_ts)

    expected = tmp_path / "data" / "raw" / f"dataset={dataset_id}" / f"run={run_ts}.json"
    assert out_path.resolve() == expected.resolve()
    assert expected.exists()

    loaded = json.loads(expected.read_text(encoding="utf-8"))
    assert loaded == rows


def test_run_watch_orchestrates_fetch_and_write(tmp_path, monkeypatch):
    """
    - Patch SodaClient so no network happens
    - Run in tmp cwd so we don't write into the real repo
    - Verify WatchResult metadata and output file
    """
    monkeypatch.chdir(tmp_path)

    fake_rows = [{"id": 1}, {"id": 2}, {"id": 3}]
    fixed_ts = "20260224T111111Z"

    monkeypatch.setattr(watch, "_run_timestamp", lambda: fixed_ts)

    class DummyClient:
        def __init__(self, domain: str, dataset_id: str) -> None:
            self.domain = domain
            self.dataset_id = dataset_id

        def fetch_updated_since(self, lookback_hours: int, page_limit: int, max_pages: int):
            assert lookback_hours == 24
            assert page_limit == 1000
            assert max_pages == 2
            return fake_rows

    monkeypatch.setattr(watch, "SodaClient", DummyClient)

    settings = Settings(
        soda_domain="data.texas.gov",
        dataset_id="qh8x-rm8r",
        lookback_hours=24,
        page_limit=1000,
        max_pages=2,
    )

    result = watch.run_watch(settings)

    assert result.run_ts == fixed_ts
    assert result.dataset_id == "qh8x-rm8r"
    assert result.domain == "data.texas.gov"
    assert result.lookback_hours == 24
    assert result.pulled_rows == 3

    expected_path = tmp_path / "data" / "raw" / "dataset=qh8x-rm8r" / f"run={fixed_ts}.json"
    assert Path(result.output_path).resolve() == expected_path.resolve()
    assert expected_path.exists()

    loaded = json.loads(expected_path.read_text(encoding="utf-8"))
    assert loaded == fake_rows
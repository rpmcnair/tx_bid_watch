from __future__ import annotations

from typing import Any
import pytest

from src import soda_client


class DummyResp:
    def __init__(self, json_data: Any, status_ok: bool = True) -> None:
        self._json_data = json_data
        self._status_ok = status_ok

    def raise_for_status(self) -> None:
        if not self._status_ok:
            raise RuntimeError("HTTP error")

    def json(self) -> Any:
        return self._json_data


def test_resource_url():
    c = soda_client.SodaClient(domain="data.texas.gov", dataset_id="qh8x-rm8r")
    assert c.resource_url == "https://data.texas.gov/resource/qh8x-rm8r.json"


def test_fetch_updated_since_single_page_stops_when_less_than_limit(monkeypatch):
    c = soda_client.SodaClient(domain="data.texas.gov", dataset_id="qh8x-rm8r")

    calls = []

    def fake_get(url, params=None, timeout=None):
        calls.append((url, params, timeout))
        # Return fewer than page_limit => should stop after one page
        return DummyResp([{"id": 1}, {"id": 2}], status_ok=True)

    monkeypatch.setattr(soda_client.requests, "get", fake_get)

    rows = c.fetch_updated_since(lookback_hours=24, page_limit=1000, max_pages=5)

    assert rows == [{"id": 1}, {"id": 2}]
    assert len(calls) == 1
    url, params, timeout = calls[0]
    assert url == c.resource_url
    assert params["$limit"] == 1000
    assert params["$offset"] == 0
    assert "$where" in params and ":updated_at" in params["$where"]
    assert params["$order"] == ":updated_at ASC"
    assert timeout == 30


def test_fetch_updated_since_paginates_and_increments_offset(monkeypatch):
    c = soda_client.SodaClient(domain="data.texas.gov", dataset_id="qh8x-rm8r")

    calls = []
    # page_limit=2
    page1 = [{"id": 1}, {"id": 2}]  # == limit -> continue
    page2 = [{"id": 3}]            # < limit -> stop

    def fake_get(url, params=None, timeout=None):
        calls.append((url, params, timeout))
        if params["$offset"] == 0:
            return DummyResp(page1, status_ok=True)
        elif params["$offset"] == 2:
            return DummyResp(page2, status_ok=True)
        else:
            return DummyResp([], status_ok=True)

    monkeypatch.setattr(soda_client.requests, "get", fake_get)

    rows = c.fetch_updated_since(lookback_hours=24, page_limit=2, max_pages=10)

    assert rows == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert len(calls) == 2
    assert calls[0][1]["$offset"] == 0
    assert calls[1][1]["$offset"] == 2


def test_fetch_updated_since_respects_max_pages(monkeypatch):
    c = soda_client.SodaClient(domain="data.texas.gov", dataset_id="qh8x-rm8r")

    calls = []
    # Always returns exactly page_limit rows, so only max_pages stops it.
    def fake_get(url, params=None, timeout=None):
        calls.append((url, params, timeout))
        return DummyResp([{"id": params["$offset"] + 1}, {"id": params["$offset"] + 2}], status_ok=True)

    monkeypatch.setattr(soda_client.requests, "get", fake_get)

    rows = c.fetch_updated_since(lookback_hours=24, page_limit=2, max_pages=3)

    # 3 pages * 2 rows each
    assert len(rows) == 6
    assert len(calls) == 3
    assert [calls[i][1]["$offset"] for i in range(3)] == [0, 2, 4]


def test_fetch_updated_since_raises_on_non_list_json(monkeypatch):
    c = soda_client.SodaClient(domain="data.texas.gov", dataset_id="qh8x-rm8r")

    def fake_get(url, params=None, timeout=None):
        return DummyResp({"not": "a list"}, status_ok=True)

    monkeypatch.setattr(soda_client.requests, "get", fake_get)

    with pytest.raises(ValueError):
        _ = c.fetch_updated_since(lookback_hours=24, page_limit=2, max_pages=1)


def test_fetch_updated_since_raises_on_http_error(monkeypatch):
    c = soda_client.SodaClient(domain="data.texas.gov", dataset_id="qh8x-rm8r")

    def fake_get(url, params=None, timeout=None):
        return DummyResp([], status_ok=False)

    monkeypatch.setattr(soda_client.requests, "get", fake_get)

    with pytest.raises(RuntimeError):
        _ = c.fetch_updated_since(lookback_hours=24, page_limit=2, max_pages=1)
import importlib
from src import config


def reload_config():
    importlib.reload(config)
    return config


def test_load_settings_reads_env_vars(monkeypatch):
    monkeypatch.setenv("SODA_DOMAIN", "example.com")
    monkeypatch.setenv("DATASET_ID", "abcd-1234")
    monkeypatch.setenv("LOOKBACK_HOURS", "48")
    monkeypatch.setenv("PAGE_LIMIT", "500")
    monkeypatch.setenv("MAX_PAGES", "10")

    cfg_mod = reload_config()
    s = cfg_mod.load_settings()

    assert s.soda_domain == "example.com"
    assert s.dataset_id == "abcd-1234"
    assert s.lookback_hours == 48
    assert s.page_limit == 500
    assert s.max_pages == 10
    assert s.raw_bucket is None
    assert s.raw_prefix == "raw"


def test_load_settings_defaults_when_env_missing(monkeypatch):
    monkeypatch.delenv("SODA_DOMAIN", raising=False)
    monkeypatch.delenv("DATASET_ID", raising=False)
    monkeypatch.delenv("LOOKBACK_HOURS", raising=False)
    monkeypatch.delenv("PAGE_LIMIT", raising=False)
    monkeypatch.delenv("MAX_PAGES", raising=False)

    cfg_mod = reload_config()
    s = cfg_mod.load_settings()

    assert s.soda_domain == "data.texas.gov"
    assert s.dataset_id == "qh8x-rm8r"
    assert s.lookback_hours == 24
    assert s.page_limit == 1000
    assert s.max_pages == 2
    assert s.raw_bucket is None
    assert s.raw_prefix == "raw"


def test_load_settings_strips_whitespace(monkeypatch):
    monkeypatch.setenv("SODA_DOMAIN", "  data.texas.gov  ")
    monkeypatch.setenv("DATASET_ID", "  qh8x-rm8r  ")

    cfg_mod = reload_config()
    s = cfg_mod.load_settings()

    assert s.soda_domain == "data.texas.gov"
    assert s.dataset_id == "qh8x-rm8r"
"""Tests for ISIN → symbol resolution (services/prices/isin_resolver).

A fake mapping provider stands in for OpenFIGI (no network). Covers venue
selection, the static-map / DB-cache / provider layering, miss caching, and that
a provider outage neither caches nor breaks.
"""

from sqlalchemy.orm import Session

from app.models import IsinSymbol
from app.services.prices import isin_resolver, symbols


class FakeFigi:
    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping
        self.calls: list[list[str]] = []

    def map_isins(self, isins: list[str]) -> dict[str, str]:
        self.calls.append(list(isins))
        return {i: self.mapping[i] for i in isins if i in self.mapping}


class _Pos:
    def __init__(self, ticker: str, isin: str | None, asset_class: str = "stock") -> None:
        self.ticker = ticker
        self.isin = isin
        self.asset_class = asset_class


# --- venue selection -------------------------------------------------------


def test_pick_symbol_prefers_home_eur_venue() -> None:
    listings = [
        {"ticker": "ASML", "exchCode": "US"},
        {"ticker": "ASML", "exchCode": "NA"},  # Amsterdam = NL home
        {"ticker": "ASML", "exchCode": "GR"},  # Xetra
    ]
    assert isin_resolver._pick_symbol("NL0010273215", listings) == "ASML.AS"


def test_pick_symbol_us_isin_picks_bare_ticker() -> None:
    listings = [
        {"ticker": "AAPL", "exchCode": "UW"},  # Nasdaq
        {"ticker": "APC", "exchCode": "GR"},  # Xetra dual-listing
    ]
    assert isin_resolver._pick_symbol("US0378331005", listings) == "AAPL"


def test_pick_symbol_etf_isin_prefers_xetra_over_london() -> None:
    listings = [
        {"ticker": "VWCE", "exchCode": "LN"},  # London
        {"ticker": "VWCE", "exchCode": "GR"},  # Xetra
    ]
    assert isin_resolver._pick_symbol("IE00BK5BQT80", listings) == "VWCE.DE"


def test_pick_symbol_unknown_venue_returns_none() -> None:
    assert isin_resolver._pick_symbol("XX0000000000", [{"ticker": "FOO", "exchCode": "ZZ"}]) is None


# --- resolve layering + caching --------------------------------------------


def test_resolve_uses_static_map_without_calling_provider(db: Session) -> None:
    prov = FakeFigi({})
    out = isin_resolver.resolve(db, ["IE00BK5BQT80"], provider=prov)  # in curated map
    assert out["IE00BK5BQT80"] == "VWCE.DE"
    assert prov.calls == []


def test_resolve_calls_openfigi_then_caches(db: Session) -> None:
    # DE0007164600 (SAP) is NOT in the curated map, so it goes to the provider.
    prov = FakeFigi({"DE0007164600": "SAP.DE"})

    out1 = isin_resolver.resolve(db, ["DE0007164600"], provider=prov)
    assert out1 == {"DE0007164600": "SAP.DE"}
    assert prov.calls == [["DE0007164600"]]

    out2 = isin_resolver.resolve(db, ["DE0007164600"], provider=prov)
    assert out2 == {"DE0007164600": "SAP.DE"}
    assert prov.calls == [["DE0007164600"]]  # cached → not re-queried
    assert db.query(IsinSymbol).count() == 1


def test_resolve_caches_misses(db: Session) -> None:
    prov = FakeFigi({})  # resolves nothing
    assert isin_resolver.resolve(db, ["XX1111111111"], provider=prov) == {}
    assert prov.calls == [["XX1111111111"]]

    isin_resolver.resolve(db, ["XX1111111111"], provider=prov)
    assert prov.calls == [["XX1111111111"]]  # miss cached → not re-queried
    assert db.query(IsinSymbol).filter_by(isin="XX1111111111").one().symbol is None


def test_resolve_transient_failure_is_not_cached(db: Session) -> None:
    class Boom:
        def map_isins(self, isins: list[str]) -> dict[str, str]:
            raise RuntimeError("rate limited")

    assert isin_resolver.resolve(db, ["DE0007164600"], provider=Boom()) == {}
    assert db.query(IsinSymbol).count() == 0  # nothing cached on outage


# --- candidate_symbols integration -----------------------------------------


def test_candidate_symbols_uses_resolved_isin_map() -> None:
    # DE0007164600 isn't curated, so the resolved map is what supplies the symbol.
    pos = _Pos(ticker="SAP", isin="DE0007164600")
    assert symbols.candidate_symbols(pos, isin_map={"DE0007164600": "SAP.DE"})[0] == "SAP.DE"


def test_candidate_symbols_curated_map_beats_resolved() -> None:
    pos = _Pos(ticker="VWCE", isin="IE00BK5BQT80")
    cands = symbols.candidate_symbols(pos, isin_map={"IE00BK5BQT80": "WRONG.XX"})
    assert cands[0] == "VWCE.DE"  # hand-verified curated map wins

"""Tests for ISIN → symbol resolution (services/prices/isin_resolver).

A fake mapping provider stands in for OpenFIGI (no network). Covers venue
selection, the static-map / DB-cache / provider layering, miss caching, and that
a provider outage neither caches nor breaks.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import IsinSymbol
from app.services.prices import isin_resolver, symbols


class FakeFigi:
    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping
        self.calls: list[list[str]] = []

    def map_isins(self, isins: list[str]) -> tuple[dict[str, str], list[str]]:
        self.calls.append(list(isins))
        resolved = {i: self.mapping[i] for i in isins if i in self.mapping}
        return resolved, list(isins)  # attempted = all


class PartialFigi:
    """A provider that answered only the first `k` ISINs (a later batch failed)."""

    def __init__(self, mapping: dict[str, str], k: int) -> None:
        self.mapping = mapping
        self.k = k
        self.calls: list[list[str]] = []

    def map_isins(self, isins: list[str]) -> tuple[dict[str, str], list[str]]:
        self.calls.append(list(isins))
        attempted = list(isins)[: self.k]
        resolved = {i: self.mapping[i] for i in attempted if i in self.mapping}
        return resolved, attempted


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


def test_pick_symbol_prefers_majority_ticker_over_better_scored_venue() -> None:
    """Real bug, found live: a Jersey-domiciled silver ETC (JE00B1VS3333)
    trades as PHAG on 7 EU venues but as VZLC on a delisted German one.
    Scoring every listing by venue alone picked VZLC.DE (best-scored suffix,
    but for a listing that doesn't actually quote) over the correct PHAG.AS."""
    listings = [
        {"ticker": "PHAG", "exchCode": "NA"},  # Amsterdam
        {"ticker": "PHAG", "exchCode": "LN"},  # London
        {"ticker": "PHAG", "exchCode": "SW"},  # SIX Swiss
        {"ticker": "VZLC", "exchCode": "GR"},  # Xetra — best-scored suffix, wrong ticker
    ]
    assert isin_resolver._pick_symbol("JE00B1VS3333", listings) == "PHAG.AS"


def test_pick_symbol_canadian_venues_resolve_to_toronto() -> None:
    """Real bug, found live: Constellation Software (CA21037X1006) — OpenFIGI
    reports it across several Canadian venue codes (main board + ATSs), none
    of which were mapped, so it never priced at all."""
    listings = [
        {"ticker": "CSU", "exchCode": "CT"},
        {"ticker": "CSU", "exchCode": "TR"},
        {"ticker": "CNSWF", "exchCode": "US"},  # US OTC listing — not the primary one
    ]
    assert isin_resolver._pick_symbol("CA21037X1006", listings) == "CSU.TO"


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


# --- partial failure + concurrency robustness ------------------------------


def test_resolve_does_not_cache_unanswered_isins(db: Session) -> None:
    # k=1 → only the first (sorted) ISIN is answered; the other must stay uncached.
    prov = PartialFigi({"DE0007164600": "SAP.DE", "FR0000131104": "BNP.PA"}, k=1)
    out = isin_resolver.resolve(db, ["FR0000131104", "DE0007164600"], provider=prov)

    assert out == {"DE0007164600": "SAP.DE"}  # DE0... sorts first → answered
    assert db.query(IsinSymbol).filter_by(isin="DE0007164600").count() == 1
    assert db.query(IsinSymbol).filter_by(isin="FR0000131104").count() == 0  # not poisoned

    # Second call serves DE from cache and re-queries only the un-cached FR.
    isin_resolver.resolve(db, ["FR0000131104", "DE0007164600"], provider=prov)
    assert prov.calls[-1] == ["FR0000131104"]


def test_openfigi_provider_keeps_earlier_batches_on_later_failure(monkeypatch) -> None:
    import httpx

    calls: list[list[str]] = []

    class Resp:
        def __init__(self, payload: object) -> None:
            self._payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> object:
            return self._payload

    def fake_post(url, json=None, headers=None, timeout=None):  # noqa: ANN001
        calls.append([job["idValue"] for job in json])
        if len(calls) == 1:  # batch 1 resolves the first ISIN
            data = [{"data": [{"ticker": "SAP", "exchCode": "GR"}]}]
            data += [{"warning": "none"}] * (len(json) - 1)
            return Resp(data)
        raise httpx.HTTPError("429 rate limited")  # batch 2 fails

    monkeypatch.setattr(httpx, "post", fake_post)

    prov = isin_resolver.OpenFigiProvider(api_key="")  # no key → batch size 10
    isins = [f"DE00000000{i:02d}" for i in range(12)]  # 12 ISINs → 2 batches
    resolved, attempted = prov.map_isins(isins)

    assert len(calls) == 2  # tried batch 2, which failed
    assert len(attempted) == 10  # only batch 1's ISINs counted as answered
    assert resolved[isins[0]] == "SAP.DE"  # earlier batch's success preserved


def test_resolve_swallows_commit_integrity_error(db: Session, monkeypatch) -> None:
    prov = FakeFigi({"DE0007164600": "SAP.DE"})

    def boom_commit() -> None:
        raise IntegrityError("duplicate key", None, Exception("dup"))

    monkeypatch.setattr(db, "commit", boom_commit)

    # A racing writer caused the PK conflict; resolve must degrade, not raise.
    out = isin_resolver.resolve(db, ["DE0007164600"], provider=prov)
    assert out == {"DE0007164600": "SAP.DE"}

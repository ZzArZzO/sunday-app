"""Tests for the read-only exchange connector (services/connectors/exchange).

Uses a fake CCXT-style fetcher — no network, no ccxt needed. The credential
encryption roundtrip + full DB sync (which need the optional `cryptography` dep)
live in test_connectors_exchange_secrets.py.
"""

from decimal import Decimal

from app.services.connectors import exchange as ex
from app.services.connectors.snapshot import TokenBalance


class FakeFetcher:
    def __init__(self, balances: list[TokenBalance]) -> None:
        self._balances = balances
        self.seen: tuple[str, str, str] | None = None

    def fetch_balances(self, exchange: str, api_key: str, api_secret: str) -> list[TokenBalance]:
        self.seen = (exchange, api_key, api_secret)
        return self._balances


def test_is_supported() -> None:
    assert ex.is_supported("kraken")
    assert ex.is_supported("Coinbase")
    assert not ex.is_supported("ftx")


def test_connector_maps_balances_to_buys() -> None:
    fetcher = FakeFetcher([TokenBalance("BTC", Decimal("0.5")), TokenBalance("EUR", Decimal("0"))])
    txns = ex.ExchangeConnector(
        exchange="kraken", api_key="k", api_secret="s", fetcher=fetcher
    ).fetch()
    assert [t.ticker for t in txns] == ["BTC"]  # zero balance skipped
    assert txns[0].asset_class == "crypto"
    assert fetcher.seen == ("kraken", "k", "s")


def test_get_fetcher_disabled_without_config() -> None:
    # No connection_secret_key by default → exchange sync dormant.
    assert ex.get_fetcher() is None

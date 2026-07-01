"""Tests for the read-only crypto address connector (services/connectors/crypto_address).

Uses a fake balance provider — no network. Covers validation, balance mapping,
the snapshot→canonical-transaction translation, and live re-sync (replace) +
error handling, which is what the route relies on.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models import Connection, Lot, Portfolio, User
from app.services.connectors import crypto_address as ca


class FakeTxProvider:
    def __init__(self, history: dict) -> None:
        self._history = history

    def fetch_transactions(self, address: str) -> dict:
        return self._history


class FakeProvider:
    def __init__(self, balances: list[ca.TokenBalance], *, fail: bool = False) -> None:
        self._balances = balances
        self._fail = fail

    def fetch_balances(self, address: str) -> list[ca.TokenBalance]:
        if self._fail:
            raise RuntimeError("indexer down")
        return self._balances


def _seed(db: Session) -> Portfolio:
    user = User(id=1, email="demo@test.local")
    db.add(user)
    db.flush()
    portfolio = Portfolio(user_id=user.id, name="Main")
    db.add(portfolio)
    db.flush()
    user.portfolios.append(portfolio)
    return portfolio


def _addr_conn(db: Session, portfolio: Portfolio, address: str) -> Connection:
    conn = Connection(
        portfolio_id=portfolio.id, kind="address", label="wallet", config={"address": address}
    )
    db.add(conn)
    db.flush()
    portfolio.connections.append(conn)
    return conn


_SOL_ADDR = "So11111111111111111111111111111111111111112"  # wrapped SOL mint (43 chars)


def test_evm_address_validation() -> None:
    assert ca.is_valid_evm_address("0x" + "a" * 40)
    assert not ca.is_valid_evm_address("0x123")
    assert not ca.is_valid_evm_address("not-an-address")


def test_solana_address_validation() -> None:
    assert ca.is_valid_solana_address(_SOL_ADDR)
    assert not ca.is_valid_solana_address("0x" + "a" * 40)  # EVM, not base58
    assert not ca.is_valid_solana_address("tooshort")
    assert not ca.is_valid_solana_address("0OIl" + "1" * 40)  # excluded base58 chars


def test_normalize_address_lowercases_evm_keeps_solana_case() -> None:
    evm = "0x" + "aB" * 20  # 40 hex chars, mixed case
    norm, chain = ca.normalize_address(evm)
    assert chain == "evm"
    assert norm == evm.lower()

    norm, chain = ca.normalize_address(_SOL_ADDR)
    assert chain == "solana"
    assert norm == _SOL_ADDR  # case-sensitive, returned verbatim

    assert ca.normalize_address("not-an-address") is None
    assert ca.is_valid_address(_SOL_ADDR)


def test_parse_zerion_maps_positions_and_skips_bad_rows() -> None:
    payload = {
        "data": [
            {
                "attributes": {
                    "quantity": {"float": 1.5},
                    "price": 1500.0,
                    "fungible_info": {"symbol": "eth", "name": "Ethereum"},
                }
            },
            {"attributes": {"quantity": {"float": 9}, "fungible_info": {}}},  # no symbol → skip
            {"attributes": {"fungible_info": {"symbol": "SOL"}}},  # no quantity → skip
        ]
    }
    out = ca._parse_zerion(payload)
    assert [b.symbol for b in out] == ["ETH"]
    assert out[0].quantity == Decimal("1.5")
    assert out[0].price_eur == Decimal("1500.0")


def test_short_address() -> None:
    assert ca.short_address("0xabcdef1234567890abcdef1234567890abcdef12") == "0xabcd…ef12"


def test_parse_balances_skips_bad_rows() -> None:
    payload = {
        "balances": [
            {"symbol": "ETH", "amount": "1.5", "price_eur": "1500"},
            {"symbol": "", "amount": "9"},  # no symbol → skip
            {"symbol": "BAD", "amount": "x"},  # unparseable amount → skip
            {"symbol": "SOL", "amount": "10", "price_eur": "bad"},  # price ignored, kept
        ]
    }
    out = ca._parse_balances(payload)
    assert [b.symbol for b in out] == ["ETH", "SOL"]
    assert out[0].price_eur == Decimal("1500")
    assert out[1].price_eur is None


def test_connector_builds_buys_and_skips_zero() -> None:
    provider = FakeProvider(
        [
            ca.TokenBalance("ETH", Decimal("2"), Decimal("1500")),
            ca.TokenBalance("DUST", Decimal("0")),
        ]
    )
    txns = ca.AddressConnector(address="0x" + "a" * 40, provider=provider).fetch()
    assert len(txns) == 1
    assert txns[0].ticker == "ETH"
    assert txns[0].asset_class == "crypto"
    assert txns[0].kind == "buy"


def test_get_provider_disabled_without_key() -> None:
    # Default settings have no crypto_indexer_api_key → address sync is dormant.
    assert ca.get_provider() is None


def test_sync_creates_then_replaces_holdings(db: Session) -> None:
    portfolio = _seed(db)
    conn = _addr_conn(db, portfolio, "0x" + "a" * 40)

    ca.sync_address(
        db, portfolio, conn, provider=FakeProvider([ca.TokenBalance("ETH", Decimal("2"), Decimal("1500"))])
    )
    eth = next(p for p in portfolio.positions if p.ticker == "ETH")
    assert eth.quantity == Decimal("2.00000000")
    assert conn.status == "active"
    assert conn.last_synced_at is not None

    # Wallet moved to 5 ETH — re-sync replaces rather than stacks.
    ca.sync_address(
        db, portfolio, conn, provider=FakeProvider([ca.TokenBalance("ETH", Decimal("5"), Decimal("1600"))])
    )
    db.refresh(eth)
    assert eth.quantity == Decimal("5.00000000")
    assert db.query(Lot).filter(Lot.connection_id == conn.id).count() == 1


def test_sync_marks_connection_error_on_failure(db: Session) -> None:
    portfolio = _seed(db)
    conn = _addr_conn(db, portfolio, "0x" + "a" * 40)

    with pytest.raises(RuntimeError):
        ca.sync_address(db, portfolio, conn, provider=FakeProvider([], fail=True))

    assert conn.status == "error"
    assert conn.error_detail is not None


def test_parse_zerion_transactions_maps_transfers() -> None:
    payload = {
        "data": [
            {
                "attributes": {
                    "mined_at": "2024-06-01T12:00:00Z",
                    "transfers": [
                        {
                            "direction": "in",
                            "fungible_info": {"symbol": "eth"},
                            "quantity": {"float": 2.0},
                            "price": 1500.0,
                        },
                        {
                            "direction": "out",
                            "fungible_info": {"symbol": "usdc"},
                            "quantity": {"float": 3000.0},
                        },
                    ],
                }
            },
            {
                "attributes": {
                    "mined_at": 1700000000,  # unix epoch form
                    "transfers": [
                        {
                            "direction": "in",
                            "fungible_info": {"symbol": "ETH"},
                            "quantity": {"float": 1.0},
                        },
                        {  # non-in/out direction → skipped
                            "direction": "self",
                            "fungible_info": {"symbol": "ETH"},
                            "quantity": {"float": 9.0},
                        },
                    ],
                }
            },
        ]
    }
    hist = ca._parse_zerion_transactions(payload)
    assert set(hist) == {"ETH", "USDC"}
    assert len(hist["ETH"]) == 2  # the "self" transfer was dropped
    assert hist["ETH"][0].acquire is True
    assert hist["ETH"][0].quantity == Decimal("2.0")
    assert hist["ETH"][0].unit_price_eur == Decimal("1500.0")
    assert hist["USDC"][0].acquire is False


def test_sync_with_tx_provider_dates_lots(db: Session) -> None:
    portfolio = _seed(db)
    conn = _addr_conn(db, portfolio, "0x" + "a" * 40)
    history = {
        "ETH": [
            ca.LedgerEvent(datetime(2023, 1, 1, tzinfo=timezone.utc), True, Decimal("2"), Decimal("1000")),
            ca.LedgerEvent(datetime(2024, 6, 1, tzinfo=timezone.utc), True, Decimal("3"), Decimal("1500")),
        ]
    }

    ca.sync_address(
        db,
        portfolio,
        conn,
        provider=FakeProvider([ca.TokenBalance("ETH", Decimal("5"), Decimal("1600"))]),
        tx_provider=FakeTxProvider(history),
    )

    eth = next(p for p in portfolio.positions if p.ticker == "ETH")
    assert eth.quantity == Decimal("5.00000000")
    lots = db.query(Lot).filter(Lot.connection_id == conn.id).order_by(Lot.purchased_at).all()
    assert [lot.purchased_at.date().isoformat() for lot in lots] == ["2023-01-01", "2024-06-01"]
    assert [lot.quantity for lot in lots] == [Decimal("2"), Decimal("3")]


def test_sync_tx_history_failure_falls_back_to_snapshot(db: Session) -> None:
    portfolio = _seed(db)
    conn = _addr_conn(db, portfolio, "0x" + "a" * 40)

    class BoomTx:
        def fetch_transactions(self, address: str) -> dict:
            raise RuntimeError("history down")

    ca.sync_address(
        db,
        portfolio,
        conn,
        provider=FakeProvider([ca.TokenBalance("ETH", Decimal("4"), Decimal("1600"))]),
        tx_provider=BoomTx(),
    )

    eth = next(p for p in portfolio.positions if p.ticker == "ETH")
    assert eth.quantity == Decimal("4.00000000")  # snapshot fallback still holds
    assert conn.status == "active"  # a tx-history failure is non-fatal


class _Resp:
    def __init__(self, payload: object) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


def test_zerion_balances_follow_pagination(monkeypatch) -> None:
    import httpx

    calls: list[str] = []
    pages = [
        {
            "data": [
                {"attributes": {"quantity": {"float": 2.0}, "price": 1500.0, "fungible_info": {"symbol": "ETH"}}}
            ],
            "links": {"next": "https://api.zerion.io/v1/wallets/x/positions/?page[after]=cur"},
        },
        {
            "data": [
                {"attributes": {"quantity": {"float": 0.5}, "price": 30000.0, "fungible_info": {"symbol": "BTC"}}}
            ],
            "links": {},
        },
    ]

    def fake_get(url, params=None, headers=None, timeout=None):  # noqa: ANN001
        calls.append(url)
        return _Resp(pages[len(calls) - 1])

    monkeypatch.setattr(httpx, "get", fake_get)

    balances = ca.ZerionBalanceProvider("https://api.zerion.io/v1", "key").fetch_balances("0x" + "a" * 40)
    assert len(calls) == 2  # followed links.next to page 2
    assert {b.symbol for b in balances} == {"ETH", "BTC"}  # both pages collected


def test_zerion_transactions_request_is_trash_filtered(monkeypatch) -> None:
    import httpx

    seen: dict = {}

    def fake_get(url, params=None, headers=None, timeout=None):  # noqa: ANN001
        seen["params"] = params
        return _Resp({"data": [], "links": {}})

    monkeypatch.setattr(httpx, "get", fake_get)

    ca.ZerionTransactionProvider("https://api.zerion.io/v1", "key").fetch_transactions("0x" + "a" * 40)
    assert seen["params"].get("filter[trash]") == "only_non_trash"  # matches /positions


def test_parse_zerion_drops_non_finite_quantity() -> None:
    payload = {
        "data": [
            {"attributes": {"quantity": {"float": float("nan")}, "fungible_info": {"symbol": "ETH"}}},
            {"attributes": {"quantity": {"float": 2.0}, "price": 30000.0, "fungible_info": {"symbol": "BTC"}}},
        ]
    }
    out = ca._parse_zerion(payload)
    assert [b.symbol for b in out] == ["BTC"]  # NaN quantity dropped, not crashed on

"""Tests for FIFO lot reconstruction (services/connectors/lot_history).

Pure and deterministic — fixed dates, no DB, no network. Covers the snapshot
fallback, FIFO disposal order, and reconciliation to the authoritative balance
(surplus → now-lot; overshoot → trim oldest).
"""

from datetime import datetime, timezone
from decimal import Decimal

from app.services.connectors.lot_history import (
    HeldLot,
    LedgerEvent,
    balances_to_dated_transactions,
    reconstruct_held_lots,
)
from app.services.connectors.snapshot import TokenBalance


def _d(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


NOW = _d(2026, 6, 30)


def test_no_history_yields_single_now_lot() -> None:
    lots = reconstruct_held_lots(
        [], current_qty=Decimal("3"), now=NOW, fallback_price=Decimal("100")
    )
    assert lots == [HeldLot(NOW, Decimal("3"), Decimal("100"))]


def test_zero_balance_yields_no_lots() -> None:
    assert reconstruct_held_lots([], current_qty=Decimal("0"), now=NOW) == []


def test_acquisitions_preserved_when_total_matches_balance() -> None:
    events = [
        LedgerEvent(_d(2023, 1, 1), True, Decimal("2"), Decimal("1000")),
        LedgerEvent(_d(2024, 6, 1), True, Decimal("3"), Decimal("1500")),
    ]
    lots = reconstruct_held_lots(events, current_qty=Decimal("5"), now=NOW)
    assert [(lot.date, lot.quantity, lot.unit_price_eur) for lot in lots] == [
        (_d(2023, 1, 1), Decimal("2"), Decimal("1000")),
        (_d(2024, 6, 1), Decimal("3"), Decimal("1500")),
    ]


def test_fifo_disposal_consumes_oldest_first() -> None:
    events = [
        LedgerEvent(_d(2023, 1, 1), True, Decimal("2"), Decimal("1000")),
        LedgerEvent(_d(2024, 6, 1), True, Decimal("3"), Decimal("1500")),
        LedgerEvent(_d(2025, 1, 1), False, Decimal("2")),  # sell 2 → drops 2023 lot
    ]
    lots = reconstruct_held_lots(events, current_qty=Decimal("3"), now=NOW)
    assert [(lot.date, lot.quantity) for lot in lots] == [(_d(2024, 6, 1), Decimal("3"))]


def test_fifo_partial_disposal_splits_oldest_lot() -> None:
    events = [
        LedgerEvent(_d(2023, 1, 1), True, Decimal("4"), Decimal("1000")),
        LedgerEvent(_d(2025, 1, 1), False, Decimal("1")),
    ]
    lots = reconstruct_held_lots(events, current_qty=Decimal("3"), now=NOW)
    assert [(lot.date, lot.quantity) for lot in lots] == [(_d(2023, 1, 1), Decimal("3"))]


def test_surplus_balance_becomes_now_lot() -> None:
    # Ledger explains 2; wallet holds 5 (airdrop/staking) → 3 dated now.
    events = [LedgerEvent(_d(2023, 1, 1), True, Decimal("2"), Decimal("1000"))]
    lots = reconstruct_held_lots(
        events, current_qty=Decimal("5"), now=NOW, fallback_price=Decimal("50")
    )
    assert lots[0] == HeldLot(_d(2023, 1, 1), Decimal("2"), Decimal("1000"))
    assert lots[-1] == HeldLot(NOW, Decimal("3"), Decimal("50"))


def test_overshoot_trims_oldest_to_match_balance() -> None:
    # Ledger says 5 held but the balance is 3 (a disposal we didn't see).
    events = [
        LedgerEvent(_d(2023, 1, 1), True, Decimal("2"), Decimal("1000")),
        LedgerEvent(_d(2024, 6, 1), True, Decimal("3"), Decimal("1500")),
    ]
    lots = reconstruct_held_lots(events, current_qty=Decimal("3"), now=NOW)
    assert [(lot.date, lot.quantity) for lot in lots] == [(_d(2024, 6, 1), Decimal("3"))]


def test_large_supply_residual_does_not_spawn_phantom_lot() -> None:
    # Balance 1e9; float-sourced history is off by ~1e-7 (> the old 1e-8 epsilon).
    # The magnitude-relative tolerance absorbs it — no spurious "acquired today" lot.
    events = [LedgerEvent(_d(2021, 1, 1), True, Decimal("999999999.9999999"), Decimal("0.00001"))]
    lots = reconstruct_held_lots(events, current_qty=Decimal("1000000000"), now=NOW)
    assert len(lots) == 1
    assert lots[0].date == _d(2021, 1, 1)  # the real 2021 lot, not a now-dated dust lot


def test_balances_to_dated_transactions_mixes_history_and_snapshot() -> None:
    balances = [
        TokenBalance("ETH", Decimal("5"), Decimal("1600")),
        TokenBalance("SOL", Decimal("10"), Decimal("150")),  # no history → now-lot
        TokenBalance("DUST", Decimal("0")),  # zero → skipped
    ]
    history = {
        "ETH": [
            LedgerEvent(_d(2023, 1, 1), True, Decimal("2"), Decimal("1000")),
            LedgerEvent(_d(2024, 6, 1), True, Decimal("3"), Decimal("1500")),
        ]
    }
    txns = balances_to_dated_transactions(balances, history, now=NOW)

    eth = [t for t in txns if t.ticker == "ETH"]
    sol = [t for t in txns if t.ticker == "SOL"]
    assert {t.date for t in eth} == {_d(2023, 1, 1), _d(2024, 6, 1)}  # two real dates
    assert len(sol) == 1 and sol[0].date == NOW  # snapshot date
    assert all(t.kind == "buy" and t.asset_class == "crypto" for t in txns)
    assert not any(t.ticker == "DUST" for t in txns)

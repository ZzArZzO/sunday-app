"""Tests for the monthly per-user AI budget cap (services/billing/budget)."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models import LlmCallLog, User
from app.services.billing import budget


def _close(a: Decimal, b: str) -> bool:
    # SQLite may return the SUM() as a float; compare with a small tolerance.
    return abs(Decimal(str(a)) - Decimal(b)) < Decimal("0.0001")


def _spend(user_id: int, cost: str, created_at=None) -> LlmCallLog:
    return LlmCallLog(
        feature="chat",
        model="claude-sonnet-4-6",
        user_id=user_id,
        cost_usd=Decimal(cost),
        created_at=created_at,
    )


class TestCap:
    def test_free_and_pro_caps(self):
        free = User(email="f@test.com")
        pro = User(email="p@test.com", subscription_status="active")
        assert budget.monthly_cap_usd(free) == Decimal("0.25")
        assert budget.monthly_cap_usd(pro) == Decimal("5.0")


class TestMonthToDate:
    def test_sums_only_current_month(self, db):
        u = User(email="a@test.com")
        db.add(u)
        db.commit()
        last_month = datetime.now(timezone.utc).replace(day=1) - timedelta(days=2)
        db.add_all(
            [
                _spend(u.id, "0.10"),
                _spend(u.id, "0.05"),
                _spend(u.id, "1.00", created_at=last_month),  # excluded
            ]
        )
        db.commit()
        assert _close(budget.month_to_date_usd(db, u.id), "0.15")

    def test_other_users_not_counted(self, db):
        a = User(email="a@test.com")
        b = User(email="b@test.com")
        db.add_all([a, b])
        db.commit()
        db.add_all([_spend(a.id, "0.10"), _spend(b.id, "9.00")])
        db.commit()
        assert _close(budget.month_to_date_usd(db, a.id), "0.10")


class TestExhaustion:
    def test_free_user_over_cap_is_exhausted(self, db):
        u = User(email="a@test.com")  # free, cap 0.25
        db.add(u)
        db.commit()
        db.add_all([_spend(u.id, "0.20"), _spend(u.id, "0.10")])  # 0.30 > 0.25
        db.commit()
        assert budget.is_exhausted(db, u) is True

    def test_free_user_under_cap_is_not_exhausted(self, db):
        u = User(email="a@test.com")
        db.add(u)
        db.commit()
        db.add(_spend(u.id, "0.10"))
        db.commit()
        assert budget.is_exhausted(db, u) is False
        s = budget.status(db, u)
        assert _close(s["spent_usd"], "0.10") and s["cap_usd"] == Decimal("0.25")

"""Tests for the country selector: supported-countries list + update endpoint.

Calls the route functions directly with the in-memory db fixture (matching the
existing auth tests), so no HTTP layer or Postgres is needed.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.routes.auth import update_country
from app.routes.tax import list_supported_countries
from app.schemas.auth import UpdateCountryRequest
from app.services import tax_summary
from app.services.auth import users as auth_users


def test_lists_all_supported_countries_sorted_by_name() -> None:
    countries = list_supported_countries()
    assert len(countries) == len(tax_summary.COUNTRY_PROFILES)
    names = [c.name for c in countries]
    assert names == sorted(names)
    codes = {c.code for c in countries}
    assert {"DE", "FR", "IE", "LU", "SK"} <= codes


def test_update_country_sets_and_normalises(db: Session) -> None:
    user = auth_users.get_or_create_user(db, "a@b.com")
    res = update_country(UpdateCountryRequest(country="fr"), user, db)
    assert res.country == "FR"
    assert user.country == "FR"


def test_update_country_rejects_unsupported(db: Session) -> None:
    user = auth_users.get_or_create_user(db, "a@b.com")
    with pytest.raises(HTTPException) as exc:
        update_country(UpdateCountryRequest(country="US"), user, db)
    assert exc.value.status_code == 400
    # The user's country is left unchanged.
    assert user.country == "DE"

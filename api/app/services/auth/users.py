"""User provisioning for magic-link sign-in."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Portfolio, User


def normalise_email(email: str) -> str:
    return email.strip().lower()


def is_valid_email(email: str) -> bool:
    e = email.strip()
    return "@" in e and "." in e.split("@")[-1] and len(e) <= 320


def get_or_create_user(db: Session, email: str) -> User:
    """Return the user for this email, creating them (+ an empty portfolio) if new."""
    email = normalise_email(email)
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is not None:
        return user

    user = User(email=email)
    db.add(user)
    db.flush()
    # New users get an empty default portfolio so they can import immediately.
    db.add(Portfolio(user_id=user.id, name="Main"))
    db.flush()
    return user

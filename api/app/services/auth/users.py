"""User provisioning for Supabase-authenticated sign-in."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Portfolio, User


def normalise_email(email: str) -> str:
    return email.strip().lower()


def is_valid_email(email: str) -> bool:
    e = email.strip()
    return "@" in e and "." in e.split("@")[-1] and len(e) <= 320


def get_or_create_user_from_supabase(db: Session, supabase_user_id: str, email: str) -> User:
    """Resolve a verified Supabase JWT's claims to a local `User` row.

    Lookup order: by `supabase_user_id` (the common case for a returning
    user), then by normalised email (bridges a pre-existing row to its
    Supabase identity on first sign-in after the auth migration), else create
    a new user + default portfolio.
    """
    user = db.execute(
        select(User).where(User.supabase_user_id == supabase_user_id)
    ).scalar_one_or_none()
    if user is not None:
        return user

    email = normalise_email(email)
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is not None:
        user.supabase_user_id = supabase_user_id
        db.flush()
        return user

    user = User(supabase_user_id=supabase_user_id, email=email)
    db.add(user)
    db.flush()
    # New users get an empty default portfolio so they can import immediately.
    db.add(Portfolio(user_id=user.id, name="Main"))
    db.flush()
    return user

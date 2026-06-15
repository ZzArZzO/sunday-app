"""Device push tokens (FCM / APNs-via-FCM) registered by the mobile app.

Unlike auth tokens, a push token is a *routing address*, not a secret — it must
be sent verbatim to FCM to deliver a notification, so it's stored raw (not
hashed). One row per device; re-registering the same token bumps `last_seen_at`.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class PushToken(Base):
    __tablename__ = "push_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # FCM registration token (~152 chars) or APNs token; 512 leaves headroom.
    token: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    platform: Mapped[str] = mapped_column(String(16), default="android")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

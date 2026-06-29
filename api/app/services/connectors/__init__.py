"""Import connectors.

Every portfolio import method — CSV, manual entry, on-chain address, exchange
API — is an `ImportSource` that produces `CanonicalTransaction`s. The shared
`apply_transactions` core persists them identically (EU average-cost replay →
Positions + Lots), tagging each lot with its originating Connection.
"""

from app.services.connectors.base import (
    ALLOWED_ASSET_CLASSES,
    KIND_BUY,
    KIND_DIVIDEND,
    KIND_SELL,
    KIND_SPLIT,
    ApplyResult,
    CanonicalTransaction,
    ConnectorNotConfigured,
    HoldingsLimitExceeded,
    ImportSource,
    apply_transactions,
    replace_connection_lots,
)

__all__ = [
    "ALLOWED_ASSET_CLASSES",
    "KIND_BUY",
    "KIND_DIVIDEND",
    "KIND_SELL",
    "KIND_SPLIT",
    "ApplyResult",
    "CanonicalTransaction",
    "ConnectorNotConfigured",
    "HoldingsLimitExceeded",
    "ImportSource",
    "apply_transactions",
    "replace_connection_lots",
]

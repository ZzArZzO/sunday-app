"""Connections — the import sources attached to a portfolio.

GET    /api/connections            — list the user's sources (+ status/last sync)
POST   /api/connections/address    — connect a read-only crypto wallet address (Pro)
POST   /api/connections/{id}/sync  — re-sync a live source (Pro)
DELETE /api/connections/{id}       — disconnect a source and drop its holdings

CSV/manual sources are created by the ingest flow; the live ones (address now,
exchange in a follow-up) are Pro-gated and dormant until their provider is
configured (503), mirroring the billing/LLM/email tiers.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Connection, Portfolio, User
from app.schemas.connection import (
    AddressConnectRequest,
    ConnectionListResponse,
    ConnectionSyncResult,
    ConnectionView,
    ExchangeConnectRequest,
)
from app.services.billing import subscription
from app.services.connectors import crypto_address, exchange
from app.services.connectors.base import (
    ApplyResult,
    HoldingsLimitExceeded,
    replace_connection_lots,
)

router = APIRouter(prefix="/api/connections", tags=["connections"])

PRO_REQUIRED = "Live sync is a Pro feature — upgrade to connect this source."


def _portfolio_for(db: Session, user: User) -> Portfolio:
    portfolio = next(iter(user.portfolios), None)
    if portfolio is None:
        portfolio = Portfolio(user_id=user.id, name="Main")
        db.add(portfolio)
        db.flush()
        user.portfolios.append(portfolio)
    return portfolio


def _get_connection(db: Session, user: User, connection_id: int) -> tuple[Portfolio, Connection]:
    portfolio = _portfolio_for(db, user)
    conn = next((c for c in portfolio.connections if c.id == connection_id), None)
    if conn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    return portfolio, conn


def _sync_view(conn: Connection, result: ApplyResult) -> ConnectionSyncResult:
    return ConnectionSyncResult(
        connection=ConnectionView.model_validate(conn),
        positions_synced=result.positions_created + result.positions_updated,
        warnings=result.warnings,
    )


@router.get("", response_model=ConnectionListResponse)
def list_connections(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConnectionListResponse:
    portfolio = _portfolio_for(db, user)
    return ConnectionListResponse(
        connections=[ConnectionView.model_validate(c) for c in portfolio.connections]
    )


@router.post("/address", response_model=ConnectionSyncResult)
def connect_address(
    body: AddressConnectRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConnectionSyncResult:
    if not subscription.is_pro(user):
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=PRO_REQUIRED)

    provider = crypto_address.get_provider()
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Crypto address sync isn't configured on this server.",
        )

    address = body.address.strip()
    if not crypto_address.is_valid_evm_address(address):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That doesn't look like a public wallet address (0x… expected).",
        )

    portfolio = _portfolio_for(db, user)
    addr = address.lower()
    conn = next(
        (c for c in portfolio.connections if c.kind == "address" and c.config.get("address") == addr),
        None,
    )
    if conn is None:
        conn = Connection(
            portfolio_id=portfolio.id,
            kind="address",
            label=(body.label or crypto_address.short_address(addr))[:120],
            config={"address": addr},
        )
        db.add(conn)
        db.flush()
        portfolio.connections.append(conn)

    try:
        result = crypto_address.sync_address(
            db, portfolio, conn, provider=provider, max_holdings=subscription.holdings_limit(user)
        )
    except HoldingsLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Free plan is limited to {exc.limit} holdings; this would result in {exc.attempted}.",
        ) from exc

    return _sync_view(conn, result)


@router.post("/exchange", response_model=ConnectionSyncResult)
def connect_exchange(
    body: ExchangeConnectRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConnectionSyncResult:
    if not subscription.is_pro(user):
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=PRO_REQUIRED)

    if not exchange.is_supported(body.exchange):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported exchange. Choose one of: {', '.join(sorted(exchange.SUPPORTED_EXCHANGES))}.",
        )

    fetcher = exchange.get_fetcher()
    if fetcher is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Exchange sync isn't configured on this server.",
        )

    name = body.exchange.strip().lower()
    portfolio = _portfolio_for(db, user)
    conn = next(
        (c for c in portfolio.connections if c.kind == "exchange" and c.config.get("exchange") == name),
        None,
    )
    if conn is None:
        conn = Connection(
            portfolio_id=portfolio.id,
            kind="exchange",
            label=(body.label or name.capitalize())[:120],
            config={"exchange": name},
        )
        db.add(conn)
        db.flush()
        portfolio.connections.append(conn)
    # (Re)store credentials encrypted; updating keys is just a re-connect.
    conn.secret_enc = exchange.store_credentials(body.api_key.strip(), body.api_secret.strip())

    try:
        result = exchange.sync_exchange(
            db, portfolio, conn, fetcher=fetcher, max_holdings=subscription.holdings_limit(user)
        )
    except HoldingsLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Free plan is limited to {exc.limit} holdings; this would result in {exc.attempted}.",
        ) from exc

    return _sync_view(conn, result)


@router.post("/{connection_id}/sync", response_model=ConnectionSyncResult)
def sync_connection(
    connection_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConnectionSyncResult:
    portfolio, conn = _get_connection(db, user, connection_id)

    if conn.kind not in {"address", "exchange"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{conn.kind} sources can't be re-synced; re-import instead.",
        )
    if not subscription.is_pro(user):
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=PRO_REQUIRED)

    if conn.kind == "address":
        provider = crypto_address.get_provider()
        if provider is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Crypto address sync isn't configured on this server.",
            )
        try:
            result = crypto_address.sync_address(
                db, portfolio, conn, provider=provider, max_holdings=subscription.holdings_limit(user)
            )
        except HoldingsLimitExceeded as exc:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Free plan is limited to {exc.limit} holdings; this would result in {exc.attempted}.",
            ) from exc
        return _sync_view(conn, result)

    # conn.kind == "exchange"
    fetcher = exchange.get_fetcher()
    if fetcher is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Exchange sync isn't configured on this server.",
        )
    try:
        result = exchange.sync_exchange(
            db, portfolio, conn, fetcher=fetcher, max_holdings=subscription.holdings_limit(user)
        )
    except HoldingsLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Free plan is limited to {exc.limit} holdings; this would result in {exc.attempted}.",
        ) from exc
    return _sync_view(conn, result)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def disconnect(
    connection_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    portfolio, conn = _get_connection(db, user, connection_id)
    # Drop this source's contribution to holdings, then remove the connection.
    replace_connection_lots(db, portfolio, conn, [])
    db.delete(conn)
    db.commit()

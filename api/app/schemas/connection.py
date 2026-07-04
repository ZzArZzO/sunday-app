from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConnectionView(BaseModel):
    id: int
    kind: str  # manual | csv | address | exchange
    label: str
    status: str  # active | error | disconnected
    last_synced_at: datetime | None = None
    error_detail: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ConnectionListResponse(BaseModel):
    connections: list[ConnectionView]


class AddressConnectRequest(BaseModel):
    address: str
    label: str | None = None


class ExchangeConnectRequest(BaseModel):
    exchange: str  # bitvavo | kraken | coinbase | binance
    api_key: str
    api_secret: str
    label: str | None = None


class ConnectionSyncResult(BaseModel):
    connection: ConnectionView
    positions_synced: int
    warnings: list[str]

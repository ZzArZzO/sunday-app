from typing import Literal

from pydantic import BaseModel, Field


class RegisterPushRequest(BaseModel):
    token: str = Field(min_length=1, max_length=512)
    platform: Literal["ios", "android", "web"] = "android"


class RegisterPushResponse(BaseModel):
    ok: bool


class UnregisterPushRequest(BaseModel):
    token: str = Field(min_length=1, max_length=512)


class PushTestResponse(BaseModel):
    sent: int
    dry_run: bool

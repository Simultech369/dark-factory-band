"""HTTP API Server for the Pocketful Stage-1 Clean-Room Delivery."""

from __future__ import annotations

from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from pocketful.payments import PocketfulLedger


class AccountCreateRequest(BaseModel):
    address: str = Field(..., description="Unique account address/handle")
    opening_balance: str | float | int | Decimal = Field("0.00", description="Initial balance")


class TransferRequest(BaseModel):
    sender: str
    recipient: str
    amount: str | float | int | Decimal | None = None
    cents: int | None = None
    memo: str = ""


class SplitRequest(BaseModel):
    sender: str
    recipients: list[str]
    total: str | float | int | Decimal | None = None
    cents: int | None = None
    memo: str = "split"


class ImportStateRequest(BaseModel):
    balances: dict[str, int | str | float | Decimal]
    entries: list[dict[str, Any]] = []


ledger = PocketfulLedger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Seed default sandbox accounts if ledger is empty
    if not ledger.export_state()["balances"]:
        ledger.create_account("alice", "1000.00")
        ledger.create_account("bob", "500.00")
        ledger.create_account("carla", "250.00")
        ledger.create_account("dina", "100.00")
    yield


app = FastAPI(
    title="Pocketful Clean-Room Payment API",
    version="1.0.0",
    description="Stage 1 JSON API conforming to the Dark Factory WeAreDevelopers specification.",
    lifespan=lifespan,
)


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "pocketful",
        "stage": 1,
        "total_circulation_cents": ledger.total_cents(),
    }


@app.post("/accounts", status_code=status.HTTP_201_CREATED)
def create_account(req: AccountCreateRequest) -> dict[str, Any]:
    try:
        ledger.create_account(req.address, req.opening_balance)
        return {
            "address": req.address.strip().lower(),
            "balance_cents": ledger.balance_cents(req.address),
            "status": "created",
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.get("/accounts/{address}/balance", status_code=status.HTTP_200_OK)
def get_balance(address: str) -> dict[str, Any]:
    try:
        cents = ledger.balance_cents(address)
        return {
            "address": address.strip().lower(),
            "balance_cents": cents,
            "balance": f"{cents / 100:.2f}",
        }
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account '{address}' not found",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/transfers", status_code=status.HTTP_200_OK)
def transfer(
    req: TransferRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    try:
        if req.cents is not None:
            entry = ledger.transfer_cents(
                sender=req.sender,
                recipient=req.recipient,
                cents=req.cents,
                memo=req.memo,
                idempotency_key=idempotency_key,
            )
        elif req.amount is not None:
            entry = ledger.transfer(
                sender=req.sender,
                recipient=req.recipient,
                amount=req.amount,
                memo=req.memo,
                idempotency_key=idempotency_key,
            )
        else:
            raise ValueError("either amount or cents must be specified")
        return {
            "sequence": entry.sequence,
            "sender": entry.sender,
            "recipient": entry.recipient,
            "cents": entry.cents,
            "memo": entry.memo,
        }
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown account in transfer: {exc}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/splits", status_code=status.HTTP_200_OK)
def split_payment(
    req: SplitRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    try:
        if req.cents is not None:
            entries = ledger.split_payment_cents(
                sender=req.sender,
                recipients=req.recipients,
                total_cents=req.cents,
                memo=req.memo,
                idempotency_key=idempotency_key,
            )
        elif req.total is not None:
            entries = ledger.split_payment(
                sender=req.sender,
                recipients=req.recipients,
                total=req.total,
                memo=req.memo,
                idempotency_key=idempotency_key,
            )
        else:
            raise ValueError("either total or cents must be specified")
        return {
            "entries": [
                {
                    "sequence": e.sequence,
                    "sender": e.sender,
                    "recipient": e.recipient,
                    "cents": e.cents,
                    "memo": e.memo,
                }
                for e in entries
            ]
        }
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown account in split: {exc}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc



@app.get("/export", status_code=status.HTTP_200_OK)
def export_state() -> dict[str, Any]:
    return ledger.export_state()


@app.post("/import", status_code=status.HTTP_200_OK)
def import_state(req: ImportStateRequest) -> dict[str, Any]:
    try:
        ledger.import_state(req.model_dump())
        return {"status": "imported", "total_cents": ledger.total_cents()}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

"""Thread-safe payment ledger for the Pocketful clean-room demo."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import re
from threading import RLock
from typing import Iterable


CENT = Decimal("0.01")
ADDRESS_RE = re.compile(r"^[a-z][a-z0-9_-]{2,31}$")


@dataclass(frozen=True)
class LedgerEntry:
    sequence: int
    sender: str
    recipient: str
    cents: int
    memo: str = ""


def to_cents(amount: Decimal | str | int | float) -> int:
    """Convert user-facing money into positive integer cents."""
    value = Decimal(str(amount)).quantize(CENT, rounding=ROUND_HALF_UP)
    cents = int(value * 100)
    if cents <= 0:
        raise ValueError("amount must be positive")
    return cents


def _to_non_negative_cents(amount: Decimal | str | int | float) -> int:
    value = Decimal(str(amount)).quantize(CENT, rounding=ROUND_HALF_UP)
    cents = int(value * 100)
    if cents < 0:
        raise ValueError("amount cannot be negative")
    return cents


def _validate_address(address: str) -> str:
    normalized = str(address).strip().lower()
    if not ADDRESS_RE.fullmatch(normalized):
        raise ValueError(f"invalid account address: {address!r}")
    return normalized


class PocketfulLedger:
    """In-memory payment ledger with atomic transfer semantics."""

    def __init__(self) -> None:
        self._balances: dict[str, int] = {}
        self._entries: list[LedgerEntry] = []
        self._idempotency: dict[str, tuple[str, tuple[LedgerEntry, ...]]] = {}
        self._lock = RLock()

    def create_account(
        self,
        address: str,
        opening_balance: Decimal | str | int | float = "0.00",
    ) -> None:
        normalized = _validate_address(address)
        cents = _to_non_negative_cents(opening_balance)
        if cents < 0:
            raise ValueError("opening balance cannot be negative")
        with self._lock:
            if normalized in self._balances:
                raise ValueError("account already exists")
            self._balances[normalized] = cents

    def balance_cents(self, address: str) -> int:
        normalized = _validate_address(address)
        with self._lock:
            return self._balances[normalized]

    def total_cents(self) -> int:
        with self._lock:
            return sum(self._balances.values())

    def entries(self) -> tuple[LedgerEntry, ...]:
        with self._lock:
            return tuple(self._entries)

    def transfer(
        self,
        sender: str,
        recipient: str,
        amount: Decimal | str | int | float,
        memo: str = "",
        idempotency_key: str | None = None,
    ) -> LedgerEntry:
        cents = to_cents(amount)
        sender_id = _validate_address(sender)
        recipient_id = _validate_address(recipient)
        fingerprint = f"transfer:{sender_id}:{recipient_id}:{cents}:{memo}"
        with self._lock:
            cached = self._idempotent_result(idempotency_key, fingerprint)
            if cached is not None:
                return cached[0]
            entry = self._transfer_cents(sender_id, recipient_id, cents, memo)
            self._remember_idempotency(idempotency_key, fingerprint, (entry,))
            return entry

    def split_payment(
        self,
        sender: str,
        recipients: Iterable[str],
        total: Decimal | str | int | float,
        memo: str = "split",
        idempotency_key: str | None = None,
    ) -> tuple[LedgerEntry, ...]:
        sender_id = _validate_address(sender)
        normalized_recipients = [_validate_address(item) for item in recipients]
        if not normalized_recipients:
            raise ValueError("split requires at least one recipient")
        total_cents = to_cents(total)
        base, remainder = divmod(total_cents, len(normalized_recipients))
        amounts = [
            base + (1 if index < remainder else 0)
            for index in range(len(normalized_recipients))
        ]
        fingerprint = (
            f"split:{sender_id}:{','.join(normalized_recipients)}:{total_cents}:{memo}"
        )
        with self._lock:
            cached = self._idempotent_result(idempotency_key, fingerprint)
            if cached is not None:
                return cached
            self._preflight_transfers(
                sender_id,
                tuple(zip(normalized_recipients, amounts, strict=True)),
                total_cents,
            )
            entries = tuple(
                self._apply_transfer_cents(sender_id, recipient, cents, memo)
                for recipient, cents in zip(normalized_recipients, amounts, strict=True)
            )
            self._remember_idempotency(idempotency_key, fingerprint, entries)
            return entries

    def _transfer_cents(
        self,
        sender: str,
        recipient: str,
        cents: int,
        memo: str,
    ) -> LedgerEntry:
        sender_id = _validate_address(sender)
        recipient_id = _validate_address(recipient)
        self._preflight_transfers(sender_id, ((recipient_id, cents),), cents)
        return self._apply_transfer_cents(sender_id, recipient_id, cents, memo)

    def _preflight_transfers(
        self,
        sender_id: str,
        transfers: tuple[tuple[str, int], ...],
        total_cents: int,
    ) -> None:
        if sender_id not in self._balances:
            raise KeyError("unknown account")
        seen_recipients: set[str] = set()
        for recipient_id, cents in transfers:
            if recipient_id == sender_id:
                raise ValueError("sender and recipient must differ")
            if recipient_id in seen_recipients:
                raise ValueError("duplicate split recipient")
            seen_recipients.add(recipient_id)
            if recipient_id not in self._balances:
                raise KeyError("unknown account")
            if cents <= 0:
                raise ValueError("amount must be positive")
        if self._balances[sender_id] < total_cents:
            raise ValueError("insufficient funds")

    def _apply_transfer_cents(
        self,
        sender_id: str,
        recipient_id: str,
        cents: int,
        memo: str,
    ) -> LedgerEntry:
        self._balances[sender_id] -= cents
        self._balances[recipient_id] += cents
        entry = LedgerEntry(
            sequence=len(self._entries) + 1,
            sender=sender_id,
            recipient=recipient_id,
            cents=cents,
            memo=str(memo)[:120],
        )
        self._entries.append(entry)
        return entry

    def _idempotent_result(
        self,
        idempotency_key: str | None,
        fingerprint: str,
    ) -> tuple[LedgerEntry, ...] | None:
        if idempotency_key is None:
            return None
        existing = self._idempotency.get(str(idempotency_key))
        if existing is None:
            return None
        existing_fingerprint, entries = existing
        if existing_fingerprint != fingerprint:
            raise ValueError("idempotency key reused with different operation")
        return entries

    def _remember_idempotency(
        self,
        idempotency_key: str | None,
        fingerprint: str,
        entries: tuple[LedgerEntry, ...],
    ) -> None:
        if idempotency_key is not None:
            self._idempotency[str(idempotency_key)] = (fingerprint, entries)

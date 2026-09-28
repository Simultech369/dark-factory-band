from concurrent.futures import ThreadPoolExecutor

import pytest

from pocketful import PocketfulLedger, to_cents


@pytest.fixture
def ledger_with_accounts() -> PocketfulLedger:
    ledger = PocketfulLedger()
    ledger.create_account("alice", "1000.00")
    ledger.create_account("bob", "0.00")
    ledger.create_account("carla", "0.00")
    ledger.create_account("dina", "0.00")
    return ledger


def test_to_cents_rejects_zero_and_negative_amounts() -> None:
    assert to_cents("1.235") == 124
    with pytest.raises(ValueError):
        to_cents("0")
    with pytest.raises(ValueError):
        to_cents("-0.01")


def test_split_payment_rounds_without_losing_money(
    ledger_with_accounts: PocketfulLedger,
) -> None:
    ledger = ledger_with_accounts
    before = ledger.total_cents()
    entries = ledger.split_payment("alice", ["bob", "carla", "dina"], "10.00")
    assert [entry.cents for entry in entries] == [334, 333, 333]
    assert ledger.balance_cents("alice") == 99000
    assert ledger.balance_cents("bob") == 334
    assert ledger.balance_cents("carla") == 333
    assert ledger.balance_cents("dina") == 333
    assert ledger.total_cents() == before


def test_insufficient_funds_does_not_mutate_balances(
    ledger_with_accounts: PocketfulLedger,
) -> None:
    ledger = ledger_with_accounts
    before_balances = {
        name: ledger.balance_cents(name)
        for name in ("alice", "bob", "carla", "dina")
    }
    with pytest.raises(ValueError):
        ledger.transfer("bob", "alice", "0.01")
    assert {
        name: ledger.balance_cents(name)
        for name in ("alice", "bob", "carla", "dina")
    } == before_balances
    assert ledger.entries() == ()


def test_split_with_missing_recipient_is_atomic(
    ledger_with_accounts: PocketfulLedger,
) -> None:
    ledger = ledger_with_accounts
    before_balances = {
        name: ledger.balance_cents(name)
        for name in ("alice", "bob", "carla", "dina")
    }
    with pytest.raises(KeyError):
        ledger.split_payment("alice", ["bob", "missing"], "2.00")
    assert {
        name: ledger.balance_cents(name)
        for name in ("alice", "bob", "carla", "dina")
    } == before_balances
    assert ledger.entries() == ()


def test_split_with_sender_as_recipient_is_atomic(
    ledger_with_accounts: PocketfulLedger,
) -> None:
    ledger = ledger_with_accounts
    before_balances = {
        name: ledger.balance_cents(name)
        for name in ("alice", "bob", "carla", "dina")
    }
    with pytest.raises(ValueError):
        ledger.split_payment("alice", ["bob", "alice"], "2.00")
    assert {
        name: ledger.balance_cents(name)
        for name in ("alice", "bob", "carla", "dina")
    } == before_balances
    assert ledger.entries() == ()


def test_opening_balance_uses_half_up_rounding() -> None:
    ledger = PocketfulLedger()
    ledger.create_account("alice", "1.005")
    assert ledger.balance_cents("alice") == 101


def test_transfer_idempotency_key_prevents_duplicate_retry(
    ledger_with_accounts: PocketfulLedger,
) -> None:
    ledger = ledger_with_accounts
    first = ledger.transfer("alice", "bob", "1.00", idempotency_key="retry-1")
    second = ledger.transfer("alice", "bob", "1.00", idempotency_key="retry-1")
    assert first == second
    assert ledger.balance_cents("alice") == 99900
    assert ledger.balance_cents("bob") == 100
    assert len(ledger.entries()) == 1
    with pytest.raises(ValueError):
        ledger.transfer("alice", "bob", "2.00", idempotency_key="retry-1")


def test_concurrent_transfers_preserve_money(
    ledger_with_accounts: PocketfulLedger,
) -> None:
    ledger = ledger_with_accounts
    before = ledger.total_cents()

    def send(index: int) -> int:
        recipient = ["bob", "carla", "dina"][index % 3]
        return ledger.transfer("alice", recipient, "0.07", memo="load-test").cents

    with ThreadPoolExecutor(max_workers=12) as pool:
        moved = list(pool.map(send, range(300)))

    assert sum(moved) == 2100
    assert len(ledger.entries()) == 300
    assert ledger.balance_cents("alice") == 97900
    assert ledger.total_cents() == before

import pytest
from fastapi.testclient import TestClient

from server import app, ledger


@pytest.fixture(autouse=True)
def reset_ledger_state():
    """Reset the ledger to clean baseline state before each test."""
    ledger.import_state({
        "balances": {
            "alice": "1000.00",
            "bob": "500.00",
            "carla": "250.00",
            "dina": "100.00",
        },
        "entries": [],
    })


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "pocketful"
    assert data["stage"] == 1
    assert data["total_circulation_cents"] == 185000


def test_create_account(client: TestClient) -> None:
    res = client.post("/accounts", json={"address": "edward", "opening_balance": "50.00"})
    assert res.status_code == 201
    assert res.json() == {"address": "edward", "balance_cents": 5000, "status": "created"}


def test_create_account_duplicate_fails(client: TestClient) -> None:
    res = client.post("/accounts", json={"address": "alice", "opening_balance": "10.00"})
    assert res.status_code == 400


def test_get_balance(client: TestClient) -> None:
    res = client.get("/accounts/alice/balance")
    assert res.status_code == 200
    assert res.json() == {"address": "alice", "balance_cents": 100000, "balance": "1000.00"}


def test_get_balance_unknown_account_returns_404(client: TestClient) -> None:
    res = client.get("/accounts/unknown_user/balance")
    assert res.status_code == 404


def test_transfer_success_and_idempotency(client: TestClient) -> None:
    headers = {"Idempotency-Key": "test-tx-1"}
    payload = {"sender": "alice", "recipient": "bob", "cents": 2500, "memo": "lunch"}

    # First attempt
    res1 = client.post("/transfers", json=payload, headers=headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["cents"] == 2500
    assert data1["sender"] == "alice"
    assert data1["recipient"] == "bob"

    # Verify balances updated
    assert client.get("/accounts/alice/balance").json()["balance_cents"] == 97500
    assert client.get("/accounts/bob/balance").json()["balance_cents"] == 52500

    # Idempotent replay: must return exact same receipt without re-deducting
    res2 = client.post("/transfers", json=payload, headers=headers)
    assert res2.status_code == 200
    assert res2.json() == data1
    assert client.get("/accounts/alice/balance").json()["balance_cents"] == 97500


def test_transfer_insufficient_funds_returns_400(client: TestClient) -> None:
    res = client.post("/transfers", json={"sender": "dina", "recipient": "alice", "cents": 999999})
    assert res.status_code == 400


def test_split_payment_conserves_money(client: TestClient) -> None:
    payload = {
        "sender": "alice",
        "recipients": ["bob", "carla", "dina"],
        "cents": 1000,  # $10.00 split 3 ways -> 334, 333, 333
        "memo": "dinner split",
    }
    res = client.post("/splits", json=payload, headers={"Idempotency-Key": "split-tx-1"})
    assert res.status_code == 200
    entries = res.json()["entries"]
    assert len(entries) == 3
    assert [e["cents"] for e in entries] == [334, 333, 333]

    assert client.get("/accounts/alice/balance").json()["balance_cents"] == 99000
    assert client.get("/accounts/bob/balance").json()["balance_cents"] == 50334
    assert client.get("/accounts/carla/balance").json()["balance_cents"] == 25333
    assert client.get("/accounts/dina/balance").json()["balance_cents"] == 10333


def test_state_export_and_import(client: TestClient) -> None:
    res_exp = client.get("/export")
    assert res_exp.status_code == 200
    exported = res_exp.json()
    assert "balances" in exported
    assert exported["total_cents"] == 185000

    new_state = {
        "balances": {"frank": 10000, "grace": 20000},
        "entries": [],
    }
    res_imp = client.post("/import", json=new_state)
    assert res_imp.status_code == 200
    assert res_imp.json()["total_cents"] == 30000
    assert client.get("/accounts/frank/balance").json()["balance_cents"] == 10000

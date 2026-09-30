# Stage 1: Clean Container & Execution Instructions

This directory contains the materialized payment ledger HTTP JSON API service and verification suite produced by the Dark Factory assembly line.

## 1. Clean Container Start & HTTP Service (Docker)

To verify that the service builds and serves from a clean container:

```bash
# Build the container image
docker build -t dark-factory-stage-1 .

# Run the container serving the HTTP API on port 8000
docker run --rm -p 8000:8000 dark-factory-stage-1
```

**Expected Container Output:**
- `INFO: Started server process`
- `INFO: Waiting for application startup.`
- `INFO: Application startup complete.`
- `INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)`

## 2. HTTP Endpoint Verification

Once the container is serving, test the Stage 1 endpoints:

```bash
# 1. Health check
curl -i http://localhost:8000/health

# 2. Check balance
curl -i http://localhost:8000/accounts/alice/balance

# 3. Idempotent transfer (requires Idempotency-Key header)
curl -i -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: retry-key-101" \
  -d '{"sender": "alice", "recipient": "bob", "cents": 2500, "memo": "lunch"}'

# 4. Multi-party split payment (exact cent rounding, zero loss)
curl -i -X POST http://localhost:8000/splits \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: split-key-202" \
  -d '{"sender": "alice", "recipients": ["bob", "carla", "dina"], "cents": 1000, "memo": "dinner"}'

# 5. State export
curl -i http://localhost:8000/export
```

## 3. Local Environment Execution

To run static quality checks and behavioral test suites locally:

```bash
# Install dependencies
pip install ruff pytest fastapi uvicorn httpx

# Run linter
python -m ruff check .

# Run full test suite (unit + HTTP server integration)
python -m pytest -v
```

## 4. Verified Invariants
- **HTTP Service Gate:** Builds and serves a live HTTP JSON API from a clean container conforming to the official WeAreDevelopers x BAND specification.
- **Thread Safety:** Fine-grained mutex locks around balances prevent race conditions under concurrent transfers.
- **Split Payment Atomicity:** Preflight checks ensure zero balance mutation if any participant has insufficient funds.
- **Exact Cent Rounding:** Rounding avoids cent loss during multi-party splits.
- **Idempotency Protection:** Prevents duplicate transaction application using the `Idempotency-Key` header.
- **State Export/Import:** Full atomic ledger backup and restore.

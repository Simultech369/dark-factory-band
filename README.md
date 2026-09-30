# Dark Factory: Autonomous Multi-Agent Software Assembly Line on BAND

Official submission for the **Dark Factory Hackathon (WeAreDevelopers x BAND)**.

---

## 1. What It Builds

Dark Factory coordinates three specialized agents (`DarkFactoryPlanner`, `DarkFactoryCoder`, `DarkFactoryCritic`) on the BAND platform to plan, materialize, test, and adversarially audit a clean-room payment ledger meeting the **Pocketful** financial track constraints:

- Account creation and balance non-negativity tracking
- Mutex-locked thread-safe concurrent transfers with total money conservation
- Atomic split-payment rounding without fractional penny loss
- Strict preflight balance checks with zero partial mutation upon failure
- Idempotency key deduplication for retry-safe execution
- Cryptographic SHA-256 evidence receipt (`run_receipt.json`) binding materialized file hashes to live tool execution exit codes (`ruff`, `pytest`)

---

## 2. Trajectory Invariant Sequencing

Trajectory Invariant Sequencing: The BAND run uses explicit handoff barriers instead of letting agents race in parallel. Planner first decomposes the Pocketful task and creates the room tasks; Coder only materializes the clean-room files after that handoff; Critic only audits after Coder reports completion. The final receipt is produced after the ordered sequence completes, binding the reviewed files, tool exits, and SHA-256 hashes to the completed trajectory.

---

## 3. Repository Structure

This repository adheres to the official Dark Factory packaging standard:

```
├── README.md              # Project overview, sequencing invariants, verification commands
├── FACTORY.md             # Detailed multi-agent assembly line architecture
├── run_receipt.json       # Cryptographic evidence receipt (5 surfaces + file hashes)
├── band_factory_runner.py # Live BAND room multi-agent orchestration runner
├── factory.py             # Deterministic software factory engine
├── guardrails.py          # The Five Review Surfaces implementation
├── mandates/              # Track-generic agent seat instructions
│   ├── planner.md         # System Architect & Decomposition Planner mandate
│   ├── coder.md           # Clean-Room Implementation Engineer mandate
│   └── critic.md          # Adversarial Quality & Security Auditor mandate
├── stage-1/               # Clean-room materialized payment ledger package
│   ├── Dockerfile         # Clean container definition (python:3.12-slim)
│   ├── RUN.md             # Container & local execution guide
│   ├── pyproject.toml     # Packaging & tool configurations (ruff, pytest)
│   ├── pocketful/         # Production payment ledger source
│   └── tests/             # Exhaustive 8-suite concurrency & ledger test harness
└── room.json              # Exported live BAND room event transcript (post-run)
```

---

## 4. Verification & Execution Instructions

### A. Clean Container Execution (`stage-1/`)
To build and serve the complete HTTP JSON API from a clean container:

```bash
cd stage-1
docker build -t dark-factory-stage-1 .
docker run --rm -p 8000:8000 dark-factory-stage-1
```

**Expected Container Output:**
- `INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)`
- Fully accessible HTTP endpoints: `GET /health`, `POST /accounts`, `GET /accounts/{address}/balance`, `POST /transfers`, `POST /splits`, `GET /export`, `POST /import`
- All 17 verification tests passing locally and in CI.


### B. Live BAND Multi-Agent Room Run
Connects the 3 agents directly to an [app.band.ai](https://app.band.ai) chatroom with shared task boards, live event streams, and in-room receipt uploads:

```powershell
$env:BAND_API_KEY="<your-band-api-key>"
$env:BAND_PLANNER_ID="<planner-uuid>"
$env:BAND_CODER_ID="<coder-uuid>"
$env:BAND_CRITIC_ID="<critic-uuid>"
python band_factory_runner.py
```

### C. Local Deterministic Run
```powershell
python factory.py --track pocketful --workspace ./stage-1 --output-receipt ./run_receipt.json
```

---

## 5. Five Review Surfaces

1. **Spec & Scope Validation:** Validates interface completeness and rejects prompt injection patterns.
2. **Quality & Static Analysis:** Executes `ruff check .` with 0 warnings/errors.
3. **Behavioral Verification:** Executes `pytest` asserting 100% pass rates across concurrency, split rounding, atomicity, and idempotency.
4. **Security Scan:** Scans AST and file content for private keys, secrets, and unsafe path mutations.
5. **Delivery Metadata:** Verifies all deliverable artifacts exist with SHA-256 hashes matching the manifest.

---

## 6. Live Session Evidence & Screenshots

- **Live Room Session:** [https://app.band.ai/sessions/84d4e744-cbe5-4014-b3c7-2b130b32b4d6](https://app.band.ai/sessions/84d4e744-cbe5-4014-b3c7-2b130b32b4d6)
- **Room Transcript Export:** `room.json` (captured after room completion)
- *Note for reviewers:* All screenshots included in submission materials have account handles, emails, and API keys redacted in compliance with security guidelines.

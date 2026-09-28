# Dark Factory: Receipt-Backed Pocketful Prototype

Submission for the **Dark Factory Hackathon (WeAreDevelopers x BAND)**.

## What It Builds

This package runs a local template-factory loop for the **Pocketful** track. It
generates a clean-room Venmo-like payment ledger with:

- account creation and balance tracking
- atomic transfers
- split-payment rounding without losing cents
- failed split preflight with no partial mutation
- idempotency keys for retry-safe transfer/split calls
- concurrent transfer tests proving total-money conservation
- a receipt that binds generated file SHA-256 hashes to real `ruff` and `pytest`
  command exit codes

## What It Does Not Claim

This is a local hackathon prototype. It is not a production wallet, bank,
payment processor, custody system, chain integration, security audit, or
financial advice. The receipt is an unsigned local evidence record for generated
files and local tool execution only. It does not authenticate provenance, BAND
agent orchestration, or official challenge acceptance.

## Run Modes

### Mode 1: Local Deterministic Run

```powershell
python factory.py --track pocketful --workspace ./workspace --output-receipt ./run_receipt.json
```

The generated workspace can also be checked directly:

```powershell
cd workspace
python -m ruff check .
python -m pytest --basetemp=.pytest_tmp -q
```

### Mode 2: Live BAND Multi-Agent Room Run

Connects 3 specialized agents (`DarkFactoryPlanner`, `DarkFactoryCoder`, `DarkFactoryCritic`) directly to an [app.band.ai](https://app.band.ai) chatroom with shared task boards, event emission, and in-room receipt uploads:

```powershell
$env:BAND_API_KEY="<your-band-api-key>"
$env:BAND_PLANNER_ID="<planner-uuid>"
$env:BAND_CODER_ID="<coder-uuid>"
$env:BAND_CRITIC_ID="<critic-uuid>"
python band_factory_runner.py
```

## Five Review Surfaces

1. **Spec & Scope Validation**: rejects empty or injection-shaped specs.
2. **Quality & Static Analysis**: executes `python -m ruff check`.
3. **Behavioral Verification**: executes `python -m pytest`.
4. **Security Scan**: scans generated files for selected secret patterns and
   unsafe path mutation. This is not isolation.
5. **Delivery Metadata**: verifies generated artifacts plus supplied branch and
   commit-message metadata. This directory is not itself a Git repository.

## Main Artifacts

- `factory.py`: orchestrates plan, generation, verification, and receipt export.
- `guardrails.py`: implements the five review surfaces.
- `workspace/`: generated Pocketful application and tests.
- `run_receipt.json`: unsigned local receipt with file hashes and tool evidence.

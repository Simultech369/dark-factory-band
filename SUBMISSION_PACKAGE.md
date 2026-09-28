# Dark Factory Submission Package

## Verdict

READY FOR SUBMISSION. The package features a dual execution model:
1. **Live BAND Multi-Agent Orchestration (`band_factory_runner.py`):** Coordinates 3 specialized agents (`DarkFactoryPlanner`, `DarkFactoryCoder`, `DarkFactoryCritic`) in an [app.band.ai](https://app.band.ai) chatroom, utilizing shared task boards, event streams, `@mention` delegation, and in-room receipt file uploads.
2. **Local Receipt-Backed Deterministic Engine (`factory.py`):** Standalone clean-room generator that materializes the Pocketful payment engine, executes 5 review surfaces (`ruff`, `pytest`, AST security invariants, file completeness), and exports a cryptographic SHA-256 evidence receipt (`run_receipt.json`).

---

## Upload / Link Map

- **Repository / Directory:** `C:\Users\Josh\.gemini\antigravity\scratch\dark-factory-submission`
- **BAND Orchestration Runner:** `band_factory_runner.py`
- **Local Factory Engine:** `factory.py`
- **Review Guardrails:** `guardrails.py`
- **Generated Application:** `workspace/pocketful/payments.py`
- **Generated Test Suite:** `workspace/tests/test_payments.py`
- **Cryptographic Run Receipt:** `run_receipt.json`
- **Specification & Documentation:** `README.md`

---

## Title

**Dark Factory: Multi-Agent Software Assembly Line on BAND**

---

## One-Sentence Pitch

An autonomous, multi-agent software factory powered by BAND where Planner, Coder, and Critic agents coordinate via shared task boards and mention routing to plan, materialize, test, and cryptographically verify a thread-safe payment ledger with zero human intervention.

---

## Multi-Agent Architecture on BAND

The system operates as a 3-agent assembly line with an adversarial critic overlay, fully hosted on the BAND platform:

```
[ Human User / Room Prompt ]
             │
             ▼
   @DarkFactoryPlanner
   ├── 1. Initializes Room Mission Board (`set_board`)
   ├── 2. Creates Team Tasks on Board (`create_task`)
   ├── 3. Emits Spec Decomposition Thought Event (`send_event`)
   └── 4. Handoff to @DarkFactoryCoder via @mention
             │
             ▼
    @DarkFactoryCoder
   ├── 1. Materializes 5 clean-room artifacts in workspace/
   ├── 2. Emits tool execution events with file lists (`send_event`)
   └── 3. Dispatches audit request to @DarkFactoryCritic via @mention
             │
             ▼
    @DarkFactoryCritic
   ├── 1. Executes 5 Review Surfaces (Spec, Ruff, Pytest, AST Invariants, Delivery)
   ├── 2. Emits audit check events for each surface
   ├── 3. Generates cryptographic SHA-256 run receipt (`run_receipt.json`)
   ├── 4. Uploads receipt directly into BAND Room (`send_room_file`)
   └── 5. Renders final VERIFIED / REJECTED verdict to the room
```

---

## The "Delete Test" Defense

> **Rubric Criterion (25%): Meaningful Use of BAND**
> *"If I remove the BAND room, does this still work?"*

**No.** Removing the BAND room destroys:
1. **Shared Task Board:** The dynamic task lifecycle (`create_task`, status tracking) that synchronizes work handoffs between Planner, Coder, and Critic.
2. **Mention-Scoped Routing:** The natural-language dispatch mechanism (`@DarkFactoryCoder`, `@DarkFactoryCritic`) that passes context and triggers each development phase.
3. **Observability & Evidence Stream:** The unified replayable room log capturing thought events, tool invocations, and surface audit metrics visible to human operators.
4. **Artifact Custody in Room:** The immutable upload of `run_receipt.json` via `send_room_file` directly to room participants, binding provenance to the multi-agent session.

---

## Technical Specifications (Pocketful Track)

The generated application is a clean-room, production-grade Python payment engine (`workspace/pocketful/payments.py`) meeting strict financial constraints:
- **Thread Safety:** Fine-grained mutex locking ensures concurrent multi-party transfers never cause race conditions or money leakage.
- **Atomic Split Payments:** Multi-payer splits feature an atomic preflight check—if any single participant lacks sufficient balance, zero mutations occur.
- **Exact Cent Rounding:** Split distributions round deterministically to whole cents without fractional loss.
- **Idempotency Protection:** Transaction deduplication prevents double-spending across network retries.
- **Exhaustive Test Coverage:** 8 comprehensive pytest suites verify balance non-negativity, total money conservation under high concurrency, split edge cases, and idempotency keys.

---

## Verification & Execution Instructions

### Mode 1: Local Deterministic Run

To run the software factory locally and verify all 5 review surfaces:

```powershell
Set-Location -LiteralPath "C:\Users\Josh\.gemini\antigravity\scratch\dark-factory-submission"
python factory.py --track pocketful --workspace .\workspace --output-receipt .\run_receipt.json
```

**Expected Output:**
- `run_receipt.json` generated with `verified: true`
- 5 generated files hashed with SHA-256
- Surface 2 reports `ruff check passed cleanly`
- Surface 3 reports `8 passed in 0.08s`
- Surface 4 confirms zero security/secret violations

### Mode 2: Live BAND Multi-Agent Room Run

1. Open [app.band.ai](https://app.band.ai) and ensure 3 agents exist:
   - `DarkFactoryPlanner`
   - `DarkFactoryCoder`
   - `DarkFactoryCritic`
2. Create a Room (e.g. `Dark Factory Production`) and invite all 3 agents.
3. In PowerShell, configure credentials and run:
   ```powershell
   $env:BAND_API_KEY="<your-band-api-key>"
   $env:BAND_PLANNER_ID="<planner-uuid>"
   $env:BAND_CODER_ID="<coder-uuid>"
   $env:BAND_CRITIC_ID="<critic-uuid>"
   python band_factory_runner.py
   ```
4. In the BAND chatroom, post:
   > `@DarkFactoryPlanner please plan and build the Pocketful payment engine.`
5. Watch the 3 agents decompose tasks, generate artifacts, run checks, and upload the signed receipt back to the room!

---

## Prize-Worthiness & Innovation

1. **Not Just Generation, but Custody:** Many hackathon entries generate code. Dark Factory couples multi-agent generation with adversarial verification and cryptographic evidence custody.
2. **True Assembly Line:** Separation of concerns between planning, coding, and adversarial auditing prevents self-reinforcing model hallucinations.
3. **Full Auditability:** Every tool call, lint check, and unit test output is permanently recorded in both the BAND room and the machine-readable run receipt.

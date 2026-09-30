# Dark Factory Architecture & Factory Specification

## 1. System Overview

**Dark Factory** is an autonomous, multi-agent software assembly line built for the BAND platform. It replaces uncontrolled parallel agent execution with an ordered, barrier-sequenced assembly line where three specialized agents collaborate to plan, implement, and adversarially audit production-grade software:

```
[ Room User / Mission Prompt ]
             │
             ▼
      @PlannerSeat (mandates/planner.md)
      • Decomposes specification into tasks
      • Initializes room mission board (`set_board`)
      • Registers atomic tasks (`create_task`)
      • Emits architecture thought events (`send_event`)
      • Handoff to @CoderSeat via @mention
             │
             ▼
       @CoderSeat (mandates/coder.md)
      • Reads requirements from room board
      • Materializes clean-room files in stage-1/
      • Enforces mutex locking, atomicity, idempotency
      • Emits file materialization events (`send_event`)
      • Handoff to @CriticSeat via @mention
             │
             ▼
      @CriticSeat (mandates/critic.md)
      • Executes 5 Review Surfaces (Spec, Ruff, Pytest, Security, Delivery)
      • Emits audit check stream to room
      • Compiles cryptographic SHA-256 evidence receipt (`run_receipt.json`)
      • Uploads receipt directly to the room (`send_room_file`)
      • Renders final VERIFIED / REJECTED verdict
```

---

## 2. Trajectory Invariant Sequencing

Trajectory Invariant Sequencing: The BAND run uses explicit handoff barriers instead of letting agents race in parallel. Planner first decomposes the Pocketful task and creates the room tasks; Coder only materializes the clean-room files after that handoff; Critic only audits after Coder reports completion. The final receipt is produced after the ordered sequence completes, binding the reviewed files, tool exits, and SHA-256 hashes to the completed trajectory.

---

## 3. The 3 Agent Seats & Generic Mandates

The agents operate under track-agnostic mandates located in `mandates/`:
- `mandates/planner.md`: System Architect & Decomposition Planner.
- `mandates/coder.md`: Clean-Room Implementation Engineer.
- `mandates/critic.md`: Adversarial Quality & Security Auditor.

These mandates define the structural roles and invariants of the assembly line without hardcoding track names, specific endpoints, or challenge-specific error codes.

---

## 4. The Five Review Surfaces

The Critic seat evaluates materialized software against five non-overlapping verification surfaces:
1. **Surface 1: Spec & Scope Validation:** Rejects empty or injection-shaped specs; verifies required interfaces exist.
2. **Surface 2: Quality & Static Analysis:** Executes `python -m ruff check .` enforcing strict linting and PEP-8 conventions.
3. **Surface 3: Behavioral Verification:** Executes `python -m pytest` with 100% assertion passes across concurrency, atomicity, exact cent rounding, and idempotency.
4. **Surface 4: Security Scan:** Scans AST and file content for private keys, secret patterns, and unsafe path mutations.
5. **Surface 5: Delivery Metadata Verification:** Confirms all expected artifacts are materialized on disk without omissions.

---

## 5. Execution Modes

### Mode 1: Clean Container Execution (`stage-1/`)
To satisfy the clean-room container start requirement:
```bash
cd stage-1
docker build -t dark-factory-stage-1 .
docker run --rm dark-factory-stage-1
```

### Mode 2: Live BAND Room Multi-Agent Run
To run the live 3-agent orchestration in an active BAND chatroom:
```powershell
$env:BAND_API_KEY="<your-band-api-key>"
$env:BAND_PLANNER_ID="<planner-uuid>"
$env:BAND_CODER_ID="<coder-uuid>"
$env:BAND_CRITIC_ID="<critic-uuid>"
python band_factory_runner.py
```

### Mode 3: Local Deterministic Run
To run the offline software factory engine:
```powershell
python factory.py --track pocketful --workspace ./stage-1 --output-receipt ./run_receipt.json
```

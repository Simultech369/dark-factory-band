#!/usr/bin/env python3
"""
sanitize_room_json.py - Pre-Commit Sanitizer & Integrity Checker for room.json

Scans room.json (the exported BAND session transcript) to:
1. Detect and scrub any accidentally leaked credentials, tokens, or private keys.
2. Verify structural integrity of the BAND multi-agent transcript.
3. Ensure strict compliance with hackathon submission guidelines.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Sensitive token patterns to detect and scrub
SENSITIVE_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9_-]{20,}", re.IGNORECASE),
    re.compile(r"band-[a-zA-Z0-9_-]{20,}", re.IGNORECASE),
    re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE),
    re.compile(r"(?:api[_-]?key|secret|auth_token)\s*[:=]\s*[\"']?([a-zA-Z0-9_\-\.]{16,})[\"']?", re.IGNORECASE),
    re.compile(r"ghp_[a-zA-Z0-9]{36}", re.IGNORECASE),
    re.compile(r"github_pat_[a-zA-Z0-9_]{50,}", re.IGNORECASE),
]


def scan_and_sanitize(content: str, redact: bool = True) -> tuple[str, list[str]]:
    """Scan string content for sensitive patterns and optionally redact them."""
    findings = []
    sanitized = content

    for pat in SENSITIVE_PATTERNS:
        matches = pat.findall(sanitized)
        for m in matches:
            val = m if isinstance(m, str) else m[0]
            findings.append(val)
            if redact:
                sanitized = sanitized.replace(val, "[REDACTED_CREDENTIAL]")

    return sanitized, findings


def verify_room_structure(data: dict | list) -> tuple[bool, list[str]]:
    """Verify the structural integrity of the room transcript."""
    notes = []
    
    # Handle list of events or dict with events/messages
    events = []
    if isinstance(data, list):
        events = data
    elif isinstance(data, dict):
        events = data.get("messages") or data.get("events") or data.get("data") or [data]
    else:
        return False, ["Transcript root is neither a dict nor a list."]

    notes.append(f"Total transcript events/messages: {len(events)}")

    # Check for seat activity
    raw_str = json.dumps(data).lower()
    has_planner = "planner" in raw_str
    has_coder = "coder" in raw_str
    has_critic = "critic" in raw_str

    if has_planner and has_coder and has_critic:
        notes.append("Found all 3 required seats: Planner, Coder, Critic.")
    else:
        notes.append(f"Missing seat evidence: Planner={has_planner}, Coder={has_coder}, Critic={has_critic}")

    # Check for receipt attachment
    has_receipt = "run_receipt.json" in raw_str or "sha-256" in raw_str
    notes.append(f"Receipt custody evidenced: {has_receipt}")

    is_valid = len(events) > 0 and has_planner and has_coder and has_critic
    return is_valid, notes


def main():
    parser = argparse.ArgumentParser(description="Sanitize and inspect room.json transcript.")
    parser.add_argument("--file", "-f", default="room.json", help="Path to room.json (default: room.json)")
    parser.add_argument("--write", "-w", action="store_true", help="Overwrite file with redacted version if secrets found")
    args = parser.parse_args()

    target_path = Path(args.file)
    if not target_path.exists():
        print(f"[NOTICE] Target transcript file not found: {target_path}")
        print("This is normal before running the live BAND session.")
        return 0

    print(f"[*] Inspecting {target_path} (size: {target_path.stat().st_size} bytes)...")
    try:
        raw_text = target_path.read_text(encoding="utf-8")
        parsed = json.loads(raw_text)
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON: {e}")
        return 1

    sanitized_text, findings = scan_and_sanitize(raw_text, redact=args.write)

    if findings:
        print(f"[WARNING] Detected {len(findings)} potential sensitive tokens!")
        for f in findings[:5]:
            print(f"  - Detected pattern: {f[:4]}...{f[-4:] if len(f) > 8 else ''}")
        if args.write:
            target_path.write_text(sanitized_text, encoding="utf-8")
            print(f"[SUCCESS] Redacted secrets and wrote clean file to {target_path}")
        else:
            print("[ACTION NEEDED] Run with --write to redact before committing to git.")
            return 1
    else:
        print("[PASS] Zero sensitive tokens or leaked credentials detected.")

    is_valid, notes = verify_room_structure(parsed)
    print("\nTranscript Structure Audit:")
    for note in notes:
        print(f"  • {note}")

    print(f"\nFinal Verdict: {'VALID BAND TRANSCRIPT' if is_valid else 'NEEDS RUN / INCOMPLETE'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

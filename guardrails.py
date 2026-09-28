"""Council Review Surfaces and guardrails for Dark Factory.

The guardrails intentionally use local tools and concrete file evidence. A
passing receipt means these checks ran against the generated workspace; it does
not claim production readiness or external audit.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import os
import re
import subprocess
import sys
import time
from typing import Optional


@dataclass(frozen=True)
class ReviewResult:
    surface_name: str
    passed: bool
    details: str
    command: Optional[list[str]] = None
    returncode: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0

    def to_receipt(self) -> dict:
        return asdict(self)


class CouncilGuardrails:
    """Orchestrates local evidence and guardrail validation across 5 surfaces."""

    def __init__(self, repo_dir: str):
        self.repo_dir = os.path.abspath(repo_dir)

    def review_surface_1_spec(self, title: str, description: str) -> ReviewResult:
        """Surface 1: Spec and scope validation."""
        if not title or not description:
            return ReviewResult("Surface 1 (Spec and Scope)", False, "Empty task title or description")

        suspicious_patterns = [
            r"ignore previous instructions",
            r"send .* private key",
            r"curl .* webhook",
            r"rm -rf",
        ]
        for pattern in suspicious_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                return ReviewResult(
                    "Surface 1 (Spec and Scope)",
                    False,
                    f"Suspicious prompt pattern detected: {pattern}",
                )

        scope_terms = ["payment", "wallet", "balance", "transaction"]
        if title.lower() == "pocketful" and not all(term in description.lower() for term in scope_terms):
            return ReviewResult(
                "Surface 1 (Spec and Scope)",
                False,
                "Pocketful spec must mention payment, wallet, balance, and transaction scope.",
            )

        return ReviewResult(
            "Surface 1 (Spec and Scope)",
            True,
            "Task specification parsed, bounded, and validated.",
        )

    def _run_tool(self, command: list[str], timeout: int) -> ReviewResult:
        start = time.perf_counter()
        try:
            res = subprocess.run(
                command,
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            duration_ms = int((time.perf_counter() - start) * 1000)
            passed = res.returncode == 0
            return ReviewResult(
                "",
                passed,
                "tool passed" if passed else "tool failed",
                command=command,
                returncode=res.returncode,
                stdout=res.stdout[-4000:],
                stderr=res.stderr[-4000:],
                duration_ms=duration_ms,
            )
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start) * 1000)
            return ReviewResult(
                "",
                False,
                f"tool execution failed: {exc}",
                command=command,
                duration_ms=duration_ms,
            )

    def review_surface_2_quality(self, target_files: Optional[list[str]] = None) -> ReviewResult:
        """Surface 2: execute ruff against generated Python files."""
        python_files = [
            path for path in (target_files or [])
            if path.endswith(".py") and os.path.exists(os.path.join(self.repo_dir, path))
        ]
        command = [sys.executable, "-m", "ruff", "check", *(python_files or ["."])]
        result = self._run_tool(command, timeout=60)
        return ReviewResult(
            "Surface 2 (Quality and Linting)",
            result.passed,
            "ruff check passed cleanly." if result.passed else "ruff linting failed",
            command=result.command,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_ms=result.duration_ms,
        )

    def review_surface_3_harness(self, test_args: Optional[list[str]] = None) -> ReviewResult:
        """Surface 3: execute pytest against generated behavioral tests."""
        command = [sys.executable, "-m", "pytest", "--basetemp=.pytest_tmp", "-q", *(test_args or [])]
        result = self._run_tool(command, timeout=120)
        details = f"pytest passed: {result.stdout.strip()[:240]}" if result.passed else "pytest failed"
        return ReviewResult(
            "Surface 3 (Behavioral Verification)",
            result.passed,
            details,
            command=result.command,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_ms=result.duration_ms,
        )

    def review_surface_4_security(self, changed_files: list[str]) -> ReviewResult:
        """Surface 4: scan generated files for simple secret and boundary hazards."""
        for rel_path in changed_files:
            full_path = os.path.join(self.repo_dir, rel_path)
            if not os.path.exists(full_path) or not rel_path.endswith((".py", ".toml", ".md")):
                continue
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as handle:
                    content = handle.read()

                if "sys.path" in content:
                    return ReviewResult(
                        "Surface 4 (Security Invariants)",
                        False,
                        f"sys.path modification detected in {rel_path}",
                    )

                secret_patterns = [
                    r"BEGIN PRIVATE KEY",
                    r"gho_[A-Za-z0-9_]{30,}",
                    r"sk-[A-Za-z0-9_-]{20,}",
                    r"eyJ[A-Za-z0-9_\-]{20,}",
                ]
                for pattern in secret_patterns:
                    if re.search(pattern, content):
                        return ReviewResult(
                            "Surface 4 (Security Invariants)",
                            False,
                            f"Potential secret pattern '{pattern}' detected in {rel_path}",
                        )
            except Exception as exc:
                return ReviewResult(
                    "Surface 4 (Security Invariants)",
                    False,
                    f"Failed scanning {rel_path}: {exc}",
                )

        return ReviewResult(
            "Surface 4 (Security Invariants)",
            True,
            "Generated files contain no detected secrets, sys.path mutation, or private keys.",
        )

    def review_surface_5_delivery(self, branch_name: str, commit_msg: str, generated_files: list[str]) -> ReviewResult:
        """Surface 5: verify delivery metadata and generated artifacts exist."""
        if not branch_name.startswith("stagent/"):
            return ReviewResult(
                "Surface 5 (Delivery)",
                False,
                f"Branch name '{branch_name}' must start with 'stagent/'",
            )

        valid_prefixes = ("feat:", "fix:", "test:", "refactor:", "chore:", "docs:")
        if not any(commit_msg.lower().startswith(prefix) for prefix in valid_prefixes):
            return ReviewResult(
                "Surface 5 (Delivery)",
                False,
                f"Commit message must start with a conventional prefix: {valid_prefixes}",
            )

        missing = [
            path for path in generated_files
            if not os.path.exists(os.path.join(self.repo_dir, path))
        ]
        if missing:
            return ReviewResult("Surface 5 (Delivery)", False, f"Missing generated files: {missing}")

        return ReviewResult(
            "Surface 5 (Delivery)",
            True,
            f"Delivery standards validated with {len(generated_files)} generated artifacts present.",
        )

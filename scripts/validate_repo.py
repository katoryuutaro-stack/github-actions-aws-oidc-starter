#!/usr/bin/env python3
"""Fail closed on credential leaks, malformed workflows, and mutable action refs."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

import yaml

SKIP_DIRS = {".git", ".terraform", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}
TEXT_SUFFIXES = {
    ".md", ".txt", ".py", ".tf", ".tfvars", ".json", ".yaml", ".yml", ".sh", ".toml", ".ini"
}
PATTERNS: dict[str, re.Pattern[str]] = {
    "AWS access key ID": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
}
FORBIDDEN_STATIC_NAMES = {"AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"}
APPROVED_ACTIONS = {
    "actions/checkout": "de0fac2e4500dabe0009e67214ff5f5447ce83dd",
    "actions/setup-python": "a309ff8b426b58ec0e2a45f0f869d46889d02405",
    "hashicorp/setup-terraform": "dfe3c3f87815947d99a8997f908cb6525fc44e9e",
    "aws-actions/configure-aws-credentials": "d979d5b3a71173a29b74b5b88418bfda9437d885",
}
APPROVED_TERRAFORM_VERSION = "1.15.5"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


def iter_text_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in {"terraform.tfstate", "terraform.tfvars"} or path.suffix in TEXT_SUFFIXES:
            yield path


def scan_text(path: Path, root: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    errors: list[str] = []
    relative = path.relative_to(root)
    for label, pattern in PATTERNS.items():
        if pattern.search(text):
            errors.append(f"{relative}: possible {label}")
    if path.name.endswith((".yml", ".yaml", ".tf", ".tfvars", ".sh")):
        for name in FORBIDDEN_STATIC_NAMES:
            assignment = re.compile(rf"(?m)^\s*{re.escape(name)}\s*[:=]")
            if assignment.search(text):
                errors.append(f"{relative}: forbidden static credential variable {name}")
    return errors


def validate_action_ref(value: object, location: str) -> list[str]:
    if not isinstance(value, str):
        return [f"{location}: uses must be a string"]
    if value.startswith(("./", "docker://")):
        return []
    if "@" not in value:
        return [f"{location}: external action must include an immutable commit SHA"]
    action, ref = value.rsplit("@", 1)
    if not FULL_SHA.fullmatch(ref):
        return [f"{location}: external action ref must be a full 40-character commit SHA"]
    approved = APPROVED_ACTIONS.get(action)
    if approved is None:
        return [f"{location}: unapproved external action {action}"]
    if ref != approved:
        return [f"{location}: action {action} is not pinned to the approved release commit"]
    return []


def validate_workflow(path: Path, root: Path) -> list[str]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path.relative_to(root)}: invalid YAML: {exc}"]
    if not isinstance(data, dict):
        return [f"{path.relative_to(root)}: workflow must be a mapping"]
    relative = path.relative_to(root)
    errors: list[str] = []
    if "environment" in data:
        errors.append(f"{relative}: environment must be configured at job level")
    jobs = data.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        errors.append(f"{relative}: workflow has no jobs")
        return errors
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            errors.append(f"{relative}: job {job_name!r} must be a mapping")
            continue
        if "runs-on" not in job and "uses" not in job:
            errors.append(f"{relative}: job {job_name!r} has no runs-on or reusable workflow")
        if "steps" not in job and "uses" not in job:
            errors.append(f"{relative}: job {job_name!r} has no steps")
        if "uses" in job:
            errors.extend(validate_action_ref(job["uses"], f"{relative}: job {job_name!r}"))
        steps = job.get("steps", [])
        if not isinstance(steps, list):
            errors.append(f"{relative}: job {job_name!r} steps must be a list")
            continue
        for index, step in enumerate(steps, start=1):
            if not isinstance(step, dict) or "uses" not in step:
                continue
            location = f"{relative}: job {job_name!r} step {index}"
            errors.extend(validate_action_ref(step["uses"], location))
            value = step["uses"]
            if isinstance(value, str) and value.startswith("hashicorp/setup-terraform@"):
                with_data = step.get("with", {})
                version = with_data.get("terraform_version") if isinstance(with_data, dict) else None
                if version != APPROVED_TERRAFORM_VERSION:
                    errors.append(
                        f"{location}: terraform_version must be {APPROVED_TERRAFORM_VERSION}"
                    )
    return errors


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    required = [
        root / "README.md",
        root / "terraform" / "main.tf",
        root / ".github" / "workflows" / "ci.yml",
        root / ".github" / "workflows" / "aws-oidc-check.yml",
        root / ".github" / "workflows" / "oidc-subject-preview.yml",
        root / "scripts" / "resolve_github_identity.py",
        root / "scripts" / "print_oidc_subject.py",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"missing required file: {path.relative_to(root)}")
    for path in iter_text_files(root):
        errors.extend(scan_text(path, root))
    workflows = root / ".github" / "workflows"
    if workflows.exists():
        for path in sorted(workflows.glob("*.y*ml")):
            errors.extend(validate_workflow(path, root))
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    errors = validate(root)
    if errors:
        print("VALIDATION=FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

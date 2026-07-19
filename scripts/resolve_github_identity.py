#!/usr/bin/env python3
"""Resolve GitHub repository IDs and construct legacy/immutable OIDC subjects.

The script uses only the Python standard library. Set GITHUB_TOKEN for private
repositories or to avoid anonymous API rate limits. The token is never printed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

API_VERSION = "2026-03-10"
IMMUTABLE_CUTOFF = datetime(2026, 7, 15, tzinfo=timezone.utc)
VALID_MODES = {"auto", "legacy", "immutable", "dual"}


@dataclass(frozen=True)
class Identity:
    repository: str
    owner_name: str
    owner_id: str
    repository_name: str
    repository_id: str
    subject_mode: str
    subjects: list[str]
    inference: str


def split_repository(repository: str) -> tuple[str, str]:
    parts = repository.strip().split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError("repository must use OWNER/REPOSITORY form")
    return parts[0], parts[1]


def context_suffix(environment: str | None, ref: str | None) -> str:
    if bool(environment) == bool(ref):
        raise ValueError("set exactly one of --environment or --ref")
    if environment:
        return f"environment:{environment}"
    assert ref is not None
    if not (ref.startswith("refs/heads/") or ref.startswith("refs/tags/")):
        raise ValueError("--ref must begin with refs/heads/ or refs/tags/")
    return f"ref:{ref}"


def build_subjects(
    repository: str,
    owner_id: str,
    repository_id: str,
    mode: str,
    suffix: str,
) -> list[str]:
    if mode not in {"legacy", "immutable", "dual"}:
        raise ValueError("mode must be legacy, immutable, or dual")
    owner, repo = split_repository(repository)
    legacy = f"repo:{owner}/{repo}:{suffix}"
    immutable = f"repo:{owner}@{owner_id}/{repo}@{repository_id}:{suffix}"
    if mode == "legacy":
        return [legacy]
    if mode == "immutable":
        return [immutable]
    return [legacy, immutable]


def fetch_json(url: str, token: str | None) -> dict[str, Any]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "aws-oidc-subject-resolver/0.2.1",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    with urlopen(request, timeout=20) as response:  # nosec B310: fixed GitHub API origin
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError(f"unexpected response from {url}")
    return payload


def parse_created_at(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def infer_mode(requested: str, repository_data: dict[str, Any], oidc_data: dict[str, Any] | None) -> tuple[str, str]:
    if requested not in VALID_MODES:
        raise ValueError(f"unsupported mode: {requested}")
    if requested != "auto":
        return requested, "explicit command-line selection"

    if oidc_data is not None and isinstance(oidc_data.get("use_immutable_subject"), bool):
        enabled = bool(oidc_data["use_immutable_subject"])
        return ("immutable" if enabled else "legacy"), "GitHub OIDC repository settings API"

    created_at = parse_created_at(repository_data.get("created_at"))
    if created_at is not None and created_at >= IMMUTABLE_CUTOFF:
        return "immutable", "repository creation date is on/after 2026-07-15"

    return "legacy", (
        "pre-cutoff repository fallback; run the subject-preview workflow after any rename, "
        "transfer, or immutable-subject opt-in"
    )


def resolve(
    repository: str,
    environment: str | None,
    ref: str | None,
    requested_mode: str,
    token: str | None,
) -> Identity:
    owner, repo = split_repository(repository)
    encoded_owner = quote(owner, safe="")
    encoded_repo = quote(repo, safe="")
    repo_url = f"https://api.github.com/repos/{encoded_owner}/{encoded_repo}"
    repository_data = fetch_json(repo_url, token)

    oidc_data: dict[str, Any] | None = None
    oidc_url = f"{repo_url}/actions/oidc/customization/sub"
    try:
        oidc_data = fetch_json(oidc_url, token)
    except HTTPError as exc:
        if exc.code not in {403, 404}:
            raise

    owner_data = repository_data.get("owner") or {}
    owner_id = str(owner_data.get("id", ""))
    repository_id = str(repository_data.get("id", ""))
    if not owner_id.isdigit() or not repository_id.isdigit():
        raise ValueError("GitHub API response did not contain numeric owner/repository IDs")

    mode, inference = infer_mode(requested_mode, repository_data, oidc_data)
    suffix = context_suffix(environment, ref)
    subjects = build_subjects(repository, owner_id, repository_id, mode, suffix)
    return Identity(
        repository=repository,
        owner_name=owner,
        owner_id=owner_id,
        repository_name=repo,
        repository_id=repository_id,
        subject_mode=mode,
        subjects=subjects,
        inference=inference,
    )


def render_tfvars(identity: Identity) -> str:
    lines = [
        f'github_repository          = "{identity.repository}"',
        f'github_subject_mode        = "{identity.subject_mode}"',
        f'github_repository_owner_id = "{identity.owner_id}"',
        f'github_repository_id       = "{identity.repository_id}"',
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True, help="OWNER/REPOSITORY")
    context = parser.add_mutually_exclusive_group(required=True)
    context.add_argument("--environment")
    context.add_argument("--ref")
    parser.add_argument("--mode", choices=sorted(VALID_MODES), default="auto")
    parser.add_argument("--format", choices=["json", "tfvars", "text"], default="tfvars")
    args = parser.parse_args()

    try:
        identity = resolve(
            repository=args.repository,
            environment=args.environment,
            ref=args.ref,
            requested_mode=args.mode,
            token=os.getenv("GITHUB_TOKEN"),
        )
    except (ValueError, HTTPError, URLError, TimeoutError) as exc:
        print(f"RESOLUTION=FAIL: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(asdict(identity), indent=2, sort_keys=True))
    elif args.format == "tfvars":
        print(render_tfvars(identity))
    else:
        print(f"MODE={identity.subject_mode}")
        print(f"INFERENCE={identity.inference}")
        for subject in identity.subjects:
            print(f"SUBJECT={subject}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

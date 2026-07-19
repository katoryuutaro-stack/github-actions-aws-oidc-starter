#!/usr/bin/env python3
"""Request a GitHub Actions OIDC token and print only non-secret claims."""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SAFE_CLAIMS = {
    "aud",
    "sub",
    "repository",
    "repository_id",
    "repository_owner",
    "repository_owner_id",
    "repository_visibility",
    "ref",
    "ref_type",
    "environment",
    "workflow",
    "workflow_ref",
    "job_workflow_ref",
    "runner_environment",
}


def decode_claims(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("OIDC token does not contain three JWT segments")
    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    decoded = base64.urlsafe_b64decode(payload.encode("ascii"))
    value = json.loads(decoded)
    if not isinstance(value, dict):
        raise ValueError("JWT payload is not an object")
    return value


def non_secret_claims(claims: dict[str, Any]) -> dict[str, Any]:
    return {key: claims[key] for key in sorted(SAFE_CLAIMS) if key in claims}


def request_token(audience: str) -> str:
    request_url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL")
    request_token_value = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    if not request_url or not request_token_value:
        raise RuntimeError("GitHub OIDC request variables are missing; grant id-token: write")
    separator = "&" if "?" in request_url else "?"
    url = f"{request_url}{separator}{urlencode({'audience': audience})}"
    request = Request(
        url,
        headers={"Authorization": f"Bearer {request_token_value}"},
    )
    with urlopen(request, timeout=20) as response:  # nosec B310: GitHub-provided URL
        payload = json.load(response)
    token = payload.get("value") if isinstance(payload, dict) else None
    if not isinstance(token, str) or not token:
        raise ValueError("GitHub OIDC endpoint returned no token")
    return token


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audience", default="sts.amazonaws.com")
    parser.add_argument("--summary", default=os.getenv("GITHUB_STEP_SUMMARY"))
    args = parser.parse_args()
    try:
        safe = non_secret_claims(decode_claims(request_token(args.audience)))
    except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"OIDC_PREVIEW=FAIL: {exc}", file=sys.stderr)
        return 2

    print(f"OIDC_SUBJECT={safe['sub']}")
    print(json.dumps(safe, indent=2, sort_keys=True))
    if args.summary:
        with open(args.summary, "a", encoding="utf-8") as handle:
            handle.write("## GitHub OIDC subject preview\n\n")
            handle.write("```json\n")
            handle.write(json.dumps(safe, indent=2, sort_keys=True))
            handle.write("\n```\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

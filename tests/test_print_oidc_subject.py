import base64
import json
from pathlib import Path
import importlib.util
import sys

PATH = Path(__file__).parents[1] / "scripts" / "print_oidc_subject.py"
spec = importlib.util.spec_from_file_location("print_oidc_subject", PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def jwt(payload):
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"header.{encoded}.signature"


def test_decodes_and_filters_non_secret_claims():
    claims = module.decode_claims(jwt({
        "sub": "repo:owner@1/repo@2:ref:refs/heads/main",
        "repository_id": "2",
        "repository_owner_id": "1",
        "secret_like": "must-not-be-returned",
    }))
    safe = module.non_secret_claims(claims)
    assert safe["sub"].startswith("repo:owner@1")
    assert "secret_like" not in safe


def test_rejects_non_jwt():
    try:
        module.decode_claims("not-a-jwt")
    except ValueError as exc:
        assert "three JWT segments" in str(exc)
    else:
        raise AssertionError("expected ValueError")

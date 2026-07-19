from pathlib import Path
import importlib.util
import sys

PATH = Path(__file__).parents[1] / "scripts" / "resolve_github_identity.py"
spec = importlib.util.spec_from_file_location("resolve_github_identity", PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_builds_immutable_environment_subject():
    assert module.build_subjects("octo/repo", "123", "456", "immutable", "environment:production") == [
        "repo:octo@123/repo@456:environment:production"
    ]


def test_dual_mode_is_exact_and_ordered():
    assert module.build_subjects("octo/repo", "123", "456", "dual", "ref:refs/heads/main") == [
        "repo:octo/repo:ref:refs/heads/main",
        "repo:octo@123/repo@456:ref:refs/heads/main",
    ]


def test_new_repository_infers_immutable():
    data = {"created_at": "2026-07-15T00:00:00Z"}
    mode, reason = module.infer_mode("auto", data, None)
    assert mode == "immutable"
    assert "2026-07-15" in reason


def test_api_setting_wins_over_date():
    data = {"created_at": "2020-01-01T00:00:00Z"}
    mode, _ = module.infer_mode("auto", data, {"use_immutable_subject": True})
    assert mode == "immutable"


def test_context_requires_exactly_one_value():
    try:
        module.context_suffix(None, None)
    except ValueError as exc:
        assert "exactly one" in str(exc)
    else:
        raise AssertionError("expected ValueError")

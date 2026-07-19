from pathlib import Path
import importlib.util

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "validate_repo.py"
spec = importlib.util.spec_from_file_location("validate_repo", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def test_current_repository_passes():
    root = Path(__file__).parents[1]
    assert module.validate(root) == []


def test_detects_access_key(tmp_path):
    path = tmp_path / "bad.txt"
    path.write_text("AK" + "IA" + "ABCDEFGHIJKLMNOP", encoding="utf-8")
    errors = module.validate(tmp_path)
    assert any("AWS access key ID" in error for error in errors)


def test_detects_static_credential_assignment(tmp_path):
    path = tmp_path / "bad.yml"
    path.write_text("AWS_SECRET_ACCESS_KEY: unsafe-placeholder\n", encoding="utf-8")
    errors = module.validate(tmp_path)
    assert any("forbidden static credential variable" in error for error in errors)


def test_rejects_workflow_level_environment(tmp_path):
    workflow = tmp_path / "bad.yml"
    workflow.write_text(
        "name: bad\non: workflow_dispatch\nenvironment: production\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: true\n",
        encoding="utf-8",
    )
    errors = module.validate_workflow(workflow, tmp_path)
    assert any("job level" in error for error in errors)


def test_rejects_mutable_action_tag(tmp_path):
    workflow = tmp_path / "bad.yml"
    workflow.write_text(
        "name: bad\non: workflow_dispatch\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v6\n",
        encoding="utf-8",
    )
    errors = module.validate_workflow(workflow, tmp_path)
    assert any("full 40-character commit SHA" in error for error in errors)


def test_rejects_unapproved_action(tmp_path):
    workflow = tmp_path / "bad.yml"
    workflow.write_text(
        "name: bad\non: workflow_dispatch\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: example/action@" + "a" * 40 + "\n",
        encoding="utf-8",
    )
    errors = module.validate_workflow(workflow, tmp_path)
    assert any("unapproved external action" in error for error in errors)

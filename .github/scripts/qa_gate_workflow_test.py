from pathlib import Path
import re


GITHUB_DIR = Path(__file__).resolve().parents[1]
WORKFLOW = GITHUB_DIR / "workflows" / "qa-gate.yml"


def _workflow_text() -> str:
    assert WORKFLOW.exists(), "qa-gate.yml must define the automerge safety gate"
    return WORKFLOW.read_text(encoding="utf-8")


def test_workflow_triggers_on_pull_request_and_manual_dispatch() -> None:
    workflow = _workflow_text()

    assert re.search(r"(?m)^\s+pull_request:\s*$", workflow)
    assert re.search(r"(?m)^\s+workflow_dispatch:\s*$", workflow)


def test_workflow_runs_python_312_and_node_backed_test_suite() -> None:
    workflow = _workflow_text()

    assert "python-version: \"3.12\"" in workflow
    assert "actions/setup-node@" in workflow
    assert re.search(r"node-version:\s*\[18,\s*24\]", workflow)
    assert "node-version: ${{ matrix.node-version }}" in workflow
    assert "python -m venv .venv" in workflow
    assert ".venv/bin/python -m pip install" in workflow
    assert re.search(
        r"\.venv/bin/python -m pytest \.github/scripts/qa_gate_workflow_test\.py tests\b",
        workflow,
    )
    assert "bash tests/test_wrapper.sh" in workflow


def test_workflow_publishes_fail_closed_automerge_gate_context() -> None:
    workflow = _workflow_text()

    assert re.search(r"(?m)^\s+automerge-gate:\s*$", workflow)
    assert re.search(r"(?m)^\s+name:\s+automerge-gate\s*$", workflow)
    assert re.search(r"(?m)^\s+if:\s+\$\{\{\s*always\(\)\s*\}\}\s*$", workflow)
    assert "needs.tests.result" in workflow


def test_workflow_installs_and_runs_packaging_dry_run() -> None:
    workflow = _workflow_text()

    assert "pytest build twine==6.1.0 mcp==1.28.1" in workflow
    assert re.search(r"\.venv/bin/python -m build --outdir dist-ci", workflow)
    assert re.search(r"\.venv/bin/python -m twine check dist-ci/\*", workflow)


def test_workflow_runs_on_main_push_without_cancelling_main_runs() -> None:
    workflow = _workflow_text()

    assert re.search(r"(?m)^\s+push:\n\s+branches: \[main\]", workflow)
    assert "cancel-in-progress: ${{ github.event_name == 'pull_request' }}" in workflow
    # push 事件必須 per-SHA group：同 group 的 pending run 會被新 run 取代（即使
    # cancel-in-progress false），共用 refs/heads/main 會讓中間 commit 的 run 被 cancel
    assert "group: qa-gate-${{ github.event.pull_request.number || github.sha }}" in workflow

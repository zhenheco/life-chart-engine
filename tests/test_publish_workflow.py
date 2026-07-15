import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "publish.yml"


def _workflow_text() -> str:
    assert WORKFLOW.exists(), "publish.yml must define the PyPI release workflow"
    return WORKFLOW.read_text(encoding="utf-8")


def _step_using(workflow: str, action: str) -> str:
    matches = [
        step
        for step in re.split(r"(?m)(?=^      - )", workflow)
        if re.search(rf"(?m)^        uses: {re.escape(action)}@", step)
    ]
    assert len(matches) == 1, f"expected exactly one step using {action}"
    return matches[0]


def test_publish_workflow_runs_only_for_published_releases() -> None:
    workflow = _workflow_text()

    assert re.search(r"(?m)^on:\n  release:\n    types: \[published\]\s*$", workflow)


def test_publish_workflow_separates_build_from_oidc_publish() -> None:
    workflow = _workflow_text()
    jobs = workflow.split("\njobs:\n", maxsplit=1)[1]
    publish = jobs.split("\n  publish:\n", maxsplit=1)[1]

    assert re.findall(r"(?m)^  ([a-z][a-z0-9_-]*):\s*$", jobs) == ["build", "publish"]
    assert re.search(r"(?m)^  publish:\n(?:    .*\n)*?    needs: build\s*$", jobs)
    assert re.search(
        r"(?m)^    permissions:\n      id-token: write\s*$",
        publish,
    )
    assert workflow.count("id-token: write") == 1
    assert "pypa/gh-action-pypi-publish@release/v1" in _step_using(
        publish,
        "pypa/gh-action-pypi-publish",
    )


def test_publish_workflow_checks_and_transfers_distribution_artifact() -> None:
    workflow = _workflow_text()
    build, publish = workflow.split("\n  publish:\n", maxsplit=1)
    upload = _step_using(build, "actions/upload-artifact")
    download = _step_using(publish, "actions/download-artifact")

    assert "python -m build" in build
    assert "python -m twine check dist/*" in build
    assert re.search(r"(?m)^          name: python-package-distributions\s*$", upload)
    assert re.search(r"(?m)^          path: dist/\s*$", upload)
    assert re.search(r"(?m)^          name: python-package-distributions\s*$", download)
    assert re.search(r"(?m)^          path: dist/\s*$", download)


def test_publish_workflow_validates_tag_matches_project_version_before_build() -> None:
    workflow = _workflow_text()
    build = workflow.split("\n  publish:\n", maxsplit=1)[0]
    steps = re.split(r"(?m)(?=^      - )", build)
    validation_steps = [
        step
        for step in steps
        if "GITHUB_REF_NAME" in step and "pyproject.toml" in step
    ]

    assert len(validation_steps) == 1, "expected one tag-vs-project-version step"
    validation_step = validation_steps[0]
    assert "tomllib" in validation_step
    assert "[\"project\"][\"version\"]" in validation_step
    assert build.index(validation_step) < build.index("python -m build")

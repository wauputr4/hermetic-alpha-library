import sys
import tomllib
from pathlib import Path


def _project_metadata():
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    return tomllib.loads(pyproject_path.read_text(encoding="utf-8"))["project"]


def test_pyproject_declares_testable_development_environment():
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    assert pyproject["project"]["requires-python"] == ">=3.11"
    assert pyproject["project"]["license"] == {"text": "MIT"}
    assert "pytest>=8.0" in pyproject["project"]["optional-dependencies"]["dev"]
    assert pyproject["tool"]["pytest"]["ini_options"]["pythonpath"] == ["src"]
    assert pyproject["tool"]["pytest"]["ini_options"]["testpaths"] == ["tests"]


def test_runtime_satisfies_declared_python_floor():
    assert sys.version_info >= (3, 11)


def test_advertised_python_classifiers_match_ci_matrix():
    ci_workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "ci.yml"
    ci_workflow = ci_workflow_path.read_text(encoding="utf-8")
    classifiers = set(_project_metadata()["classifiers"])

    for python_version in ("3.11", "3.12"):
        assert f'"{python_version}"' in ci_workflow
        assert f"Programming Language :: Python :: {python_version}" in classifiers

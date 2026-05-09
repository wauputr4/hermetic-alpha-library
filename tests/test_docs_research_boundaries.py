from pathlib import Path

import pytest


ROOT = Path(__file__).parent.parent


def read_doc(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_readme_includes_research_disclaimer_and_guide_link():
    readme = read_doc("README.md")

    assert "not financial advice" in readme
    assert "standalone" in readme
    assert "trading signal" in readme
    assert "docs/anti-overfitting.md" in readme


@pytest.mark.parametrize(
    "term",
    [
        "baseline",
        "sample size",
        "confidence intervals",
        "data leakage",
        "cherry-picking",
        "out-of-sample",
    ],
)
def test_anti_overfitting_guide_covers_required_research_caution(term):
    guide = read_doc("docs/anti-overfitting.md").lower()

    assert term in guide


@pytest.mark.parametrize(
    "path",
    [
        "docs/README.md",
        "docs/concepts.md",
        "docs/statistical-methods.md",
        "docs/troubleshooting.md",
    ],
)
def test_related_doc_links_to_anti_overfitting_guide(path):
    assert "anti-overfitting" in read_doc(path)

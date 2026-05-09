from pathlib import Path


ROOT = Path(__file__).parent.parent


def read_doc(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_readme_includes_research_disclaimer_and_guide_link():
    readme = read_doc("README.md")

    assert "not financial advice" in readme
    assert "standalone" in readme
    assert "trading signal" in readme
    assert "docs/anti-overfitting.md" in readme


def test_anti_overfitting_guide_covers_required_research_cautions():
    guide = read_doc("docs/anti-overfitting.md").lower()

    required_terms = [
        "baseline",
        "sample size",
        "confidence intervals",
        "data leakage",
        "cherry-picking",
        "out-of-sample",
    ]

    for term in required_terms:
        assert term in guide


def test_related_docs_link_to_anti_overfitting_guide():
    for path in [
        "docs/README.md",
        "docs/concepts.md",
        "docs/statistical-methods.md",
        "docs/troubleshooting.md",
    ]:
        assert "anti-overfitting" in read_doc(path)

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_experiment_scripts_do_not_reference_legacy_results_exports_root():
    checked_suffixes = {".py", ".sh"}
    offenders = []
    for path in (REPO_ROOT / "scripts").rglob("*"):
        if path.suffix not in checked_suffixes:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "results_exports" in text:
            offenders.append(path.relative_to(REPO_ROOT).as_posix())

    assert offenders == []


def test_results_directory_is_the_ignored_experiment_root():
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "results/" in gitignore

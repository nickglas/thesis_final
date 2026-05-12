import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "run_uniform_image_experiments.py"
IMAGE_REF = "thesisrq15acr.azurecr.io/thesis-inference@sha256:" + "a" * 64


def run_uniform_dry_run(*args):
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--image-ref",
            IMAGE_REF,
            "--dry-run",
            *args,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_uniform_wrapper_defaults_rq2_paired_to_five_passes():
    result = run_uniform_dry_run("--only", "rq2_1_paired", "--skip-acr-login")

    assert result.returncode == 0, result.stderr + result.stdout
    assert "--paired-passes 5" in result.stdout
    assert "--results-root" in result.stdout
    assert "results_exports" not in result.stdout


def test_uniform_wrapper_uses_one_rq2_pass_for_smoke_mode():
    result = run_uniform_dry_run("--only", "rq2_1_mtls_split", "--skip-acr-login", "--smoke")

    assert result.returncode == 0, result.stderr + result.stdout
    assert "--split-passes 1" in result.stdout


def test_uniform_wrapper_rejects_legacy_results_exports_root():
    result = run_uniform_dry_run(
        "--only",
        "rq2_1_paired",
        "--skip-acr-login",
        "--results-root",
        "results_exports",
    )

    assert result.returncode != 0
    assert "legacy results_exports directory" in result.stderr

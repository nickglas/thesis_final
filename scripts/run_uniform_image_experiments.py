#!/usr/bin/env python3
"""Run thesis experiments with one thesis-inference image.

The wrapper keeps image provenance uniform by either accepting one immutable
ACR digest reference or building/pushing one image, resolving its digest, and
passing that same pinned reference through to the existing experiment runners.

Examples:
    python scripts/run_uniform_image_experiments.py \
        --build-push-image \
        --acr-name thesisrq15acr \
        --dry-run

    python scripts/run_uniform_image_experiments.py \
        --image-ref thesisrq15acr.azurecr.io/thesis-inference@sha256:<digest> \
        --dry-run
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_IMAGE_TAG = "thesis-inference:latest"
TOOLS_BIN = REPO_ROOT / ".tools" / "bin"
DEFAULT_KIND_VERSION = "v0.31.0"
DEFAULT_RQ2_PASSES = 5
LEGACY_RESULTS_ROOT = "results" + "_exports"

DEFAULT_STAGES = (
    "rq1_1",
    "rq1_2",
    "rq1_3",
    "rq1_4",
    "rq1_4b",
    "rq1_5",
    "rq1_5b",
    "rq2_1_paired",
    "rq2_1_mtls_split",
    "rq2_1_ablation",
    "rq2_2",
)

OPTIONAL_STAGES: tuple[str, ...] = ("rq2_1b_multinode",)

ALL_STAGES = DEFAULT_STAGES + OPTIONAL_STAGES
CONTAINER_STAGES = {
    "rq1_4",
    "rq1_4b",
    "rq1_5",
    "rq1_5b",
    "rq2_1_paired",
    "rq2_1b_multinode",
    "rq2_1_mtls_split",
    "rq2_1_ablation",
    "rq2_2",
}

IMAGE_REF_RE = re.compile(
    r"^(?P<acr>[A-Za-z0-9]+)\.azurecr\.io/thesis-inference@sha256:[0-9a-fA-F]{64}$"
)


@dataclass(frozen=True)
class StagePlan:
    name: str
    commands: list[list[str]]


@dataclass
class StageResult:
    name: str
    status: str
    elapsed_seconds: float
    detail: str = ""
    artifact_dirs: list[str] = field(default_factory=list)


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def utc_run_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S").lower()


def log(message: str) -> None:
    print(f"[{timestamp()}] {message}", flush=True)


def warn(message: str) -> None:
    print(f"[{timestamp()}] WARN: {message}", file=sys.stderr, flush=True)


def drop_sudo_root_to_invoking_user() -> bool:
    """Keep the orchestrator unprivileged even if launched with sudo.

    Azure CLI, Docker, Terraform, and kubeconfig state are user-scoped. Running
    the whole wrapper as root points those tools at root's home/config and can
    make otherwise valid logins look broken. CPU controls now elevate only the
    sysfs/renice operations that need it, so the orchestrator should be the
    original login user.
    """
    if not hasattr(os, "geteuid") or os.geteuid() != 0:
        return True

    if os.environ.get("OPUS_ALLOW_ROOT_ORCHESTRATOR", "").lower() in {"1", "true", "yes"}:
        warn(
            "Running the uniform experiment wrapper as root. This can break "
            "az/docker/terraform credential discovery."
        )
        return True

    sudo_uid = os.environ.get("SUDO_UID")
    sudo_gid = os.environ.get("SUDO_GID")
    if not sudo_uid or not sudo_gid:
        warn(
            "Refusing to run the whole experiment orchestrator as root. Run it "
            "as your normal user; CPU controls use sudo internally. Set "
            "OPUS_ALLOW_ROOT_ORCHESTRATOR=1 to override."
        )
        return False

    try:
        uid = int(sudo_uid)
        gid = int(sudo_gid)
    except ValueError:
        warn("Could not parse SUDO_UID/SUDO_GID; refusing root orchestration.")
        return False

    if uid == 0:
        return True

    try:
        import pwd

        user_info = pwd.getpwuid(uid)
        username = user_info.pw_name
        log(f"Detected sudo launch; dropping orchestrator privileges back to {username} (uid={uid}).")
        if hasattr(os, "initgroups"):
            os.initgroups(username, gid)
        os.setgid(gid)
        os.setuid(uid)
        os.environ["HOME"] = user_info.pw_dir
        os.environ["USER"] = username
        os.environ["LOGNAME"] = username
        xdg_runtime = Path(f"/run/user/{uid}")
        if xdg_runtime.is_dir():
            os.environ["XDG_RUNTIME_DIR"] = str(xdg_runtime)
        else:
            os.environ.pop("XDG_RUNTIME_DIR", None)
        return True
    except Exception as exc:
        warn(f"Could not drop root privileges after sudo launch: {exc}")
        return False


def format_command(command: list[str]) -> str:
    return shlex.join(command)


def relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def maybe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        text = str(value).strip()
        if not text:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def format_metric(value: object, digits: int = 2, suffix: str = "") -> str:
    number = maybe_float(value)
    if number is None:
        return "n/a"
    return f"{number:.{digits}f}{suffix}"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def result_dir_snapshot(results_root: Path) -> set[Path]:
    if not results_root.exists():
        return set()
    return {path.resolve() for path in results_root.iterdir() if path.is_dir()}


def add_tools_to_path() -> None:
    tools_bin = str(TOOLS_BIN)
    path_parts = os.environ.get("PATH", "").split(os.pathsep)
    if tools_bin not in path_parts:
        os.environ["PATH"] = tools_bin + os.pathsep + os.environ.get("PATH", "")


def csv_items(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def validate_image_ref(image_ref: str) -> str:
    match = IMAGE_REF_RE.fullmatch(image_ref.strip())
    if not match:
        raise SystemExit(
            "--image-ref must look like "
            "<acr>.azurecr.io/thesis-inference@sha256:<64-hex-digest>"
        )
    return match.group("acr")


def validate_digest(digest: str) -> str:
    digest = digest.strip().strip('"')
    if not re.fullmatch(r"sha256:[0-9a-fA-F]{64}", digest):
        raise RuntimeError(f"Unexpected ACR digest response: {digest!r}")
    return digest


def kind_asset_name() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        os_name = "linux"
    elif system == "darwin":
        os_name = "darwin"
    elif system == "windows":
        os_name = "windows"
    else:
        raise RuntimeError(f"Unsupported OS for automatic kind install: {platform.system()}")

    if machine in {"x86_64", "amd64"}:
        arch = "amd64"
    elif machine in {"aarch64", "arm64"}:
        arch = "arm64"
    else:
        raise RuntimeError(f"Unsupported CPU architecture for automatic kind install: {platform.machine()}")

    suffix = ".exe" if os_name == "windows" else ""
    return f"kind-{os_name}-{arch}{suffix}"


def kind_binary_path() -> Path:
    suffix = ".exe" if platform.system().lower() == "windows" else ""
    return TOOLS_BIN / f"kind{suffix}"


def resolve_stages(args: argparse.Namespace) -> list[str]:
    if args.only:
        stages = csv_items(args.only)
    else:
        stages = list(DEFAULT_STAGES)
        if args.include_optional:
            stages.extend(OPTIONAL_STAGES)

    skipped = set(csv_items(args.skip))
    unknown = [stage for stage in stages + list(skipped) if stage not in ALL_STAGES]
    if unknown:
        raise SystemExit(
            f"Unknown stage(s): {', '.join(sorted(set(unknown)))}. "
            f"Valid stages: {', '.join(ALL_STAGES)}"
        )

    selected = [stage for stage in stages if stage not in skipped]
    if not selected:
        raise SystemExit("No stages selected.")
    return selected


def python_script(script: str) -> list[str]:
    return [sys.executable, str(REPO_ROOT / script)]


def append_common_results_arg(command: list[str], args: argparse.Namespace) -> list[str]:
    if args.results_root:
        command += ["--results-root", args.results_root]
    return command


def append_rq15_cloud_args(command: list[str], args: argparse.Namespace, acr_name: str, stage: str) -> list[str]:
    command += ["--image-ref", args.image_ref, "--acr-name", acr_name]
    if args.provision_cloud:
        command.append("--provision")
    if args.destroy_cloud_on_success:
        command.append("--delete-resource-group-on-success")
    if args.destroy_cloud_on_failure:
        command.append("--delete-resource-group-on-failure")
    if args.cleanup_on_failure:
        command.append("--cleanup-on-failure")
    if stage == "rq1_5" and args.rq15_nodepool:
        command += ["--nodepool", args.rq15_nodepool]
    command += ["--condition-retries", str(args.rq15_condition_retries)]
    if stage == "rq1_5" and args.rq15_resume_artifact_dir:
        command += ["--resume-artifact-dir", args.rq15_resume_artifact_dir]
    if stage == "rq1_5b" and args.rq15b_resume_artifact_dir:
        command += ["--resume-artifact-dir", args.rq15b_resume_artifact_dir]
    return append_common_results_arg(command, args)


def append_rq2_cloud_args(
    command: list[str],
    args: argparse.Namespace,
    acr_name: str,
    stage: str,
    *,
    supports_cleanup: bool,
    supports_smoke: bool,
) -> list[str]:
    command += ["--image-ref", args.image_ref, "--acr-name", acr_name]
    if args.provision_cloud:
        command.append("--provision")
    if args.destroy_cloud_on_success:
        command.append("--destroy-infrastructure-on-success")
    if args.destroy_cloud_on_failure:
        command.append("--destroy-infrastructure-on-failure")
    if supports_cleanup and args.cleanup_on_failure:
        command.append("--cleanup-on-failure")
    if args.preserve_namespaces:
        command.append("--preserve-namespaces")
    if args.generate_only:
        command.append("--generate-only")
    if supports_smoke and args.smoke:
        command.append("--smoke")
    if args.skip_mesh_enable:
        command.append("--skip-mesh-enable")
    command += rq2_pass_args(args, stage)
    return append_common_results_arg(command, args)


def effective_rq2_passes(args: argparse.Namespace, stage: str) -> int:
    stage_specific = {
        "rq2_1_paired": args.rq2_paired_passes,
        "rq2_1b_multinode": args.rq21b_paired_passes,
        "rq2_1_mtls_split": args.rq2_split_passes,
        "rq2_1_ablation": args.rq2_ablation_passes,
        "rq2_2": args.rq22_paired_passes,
    }[stage]
    if stage_specific is not None:
        return stage_specific
    if args.smoke:
        return 1
    return args.rq2_passes


def rq2_pass_args(args: argparse.Namespace, stage: str) -> list[str]:
    passes = str(effective_rq2_passes(args, stage))
    if stage in {"rq2_1_paired", "rq2_1b_multinode"}:
        return ["--paired-passes", passes]
    if stage == "rq2_1_mtls_split":
        return ["--split-passes", passes]
    if stage == "rq2_1_ablation":
        return ["--ablation-passes", passes]
    if stage == "rq2_2":
        return ["--paired-passes", passes]
    return []


def local_image_prepare_commands(args: argparse.Namespace) -> list[list[str]]:
    return [
        ["docker", "pull", args.image_ref],
        ["docker", "tag", args.image_ref, LOCAL_IMAGE_TAG],
    ]


def build_stage_plan(stage: str, args: argparse.Namespace, acr_name: str) -> StagePlan:
    if stage == "rq1_1":
        return StagePlan(
            stage,
            [
                python_script("run_experiment.py")
                + ["--config", "configs/rq1/1.1/rq1_1_fully_controlled.yaml", "--run-analysis"]
            ],
        )

    if stage == "rq1_2":
        return StagePlan(
            stage,
            [
                python_script("run_experiment.py")
                + ["--config", "configs/rq1/1.2/rq1_2_fully_controlled.yaml", "--run-analysis"]
            ],
        )

    if stage == "rq1_3":
        return StagePlan(
            stage,
            [
                python_script("run_internal_timing.py")
                + ["--config", "configs/internal_timing/timing_full.yaml", "--run-analysis"]
            ],
        )

    if stage == "rq1_4":
        command = (
            python_script("scripts/run_all_rq1.py")
            + ["--only", "rq1_4", "--skip-image-build", "--skip-cloud", "--rq14-rolling"]
        )
        return StagePlan(stage, local_image_prepare_commands(args) + [command])

    if stage == "rq1_4b":
        command = (
            python_script("scripts/run_all_rq1.py")
            + ["--only", "rq1_4b", "--skip-image-build", "--skip-cloud"]
        )
        return StagePlan(stage, local_image_prepare_commands(args) + [command])

    if stage == "rq1_5":
        command = python_script("scripts/run_rq15_fully_controlled.py") + [
            "--config",
            "configs/rq1/1.5/rq1_5_full.yaml",
            "--resource-group",
            args.rq15_resource_group,
            "--cluster-name",
            args.rq15_cluster_name,
        ]
        return StagePlan(stage, [append_rq15_cloud_args(command, args, acr_name, stage)])

    if stage == "rq1_5b":
        command = python_script("scripts/run_rq15_fully_controlled.py") + [
            "--config",
            "configs/rq1/1.5/rq1_5b_multinode.yaml",
            "--resource-group",
            args.rq15b_resource_group,
            "--cluster-name",
            args.rq15b_cluster_name,
            "--nodepool",
            args.rq15b_nodepool,
            "--node-count",
            str(args.rq15b_node_count),
        ]
        return StagePlan(stage, [append_rq15_cloud_args(command, args, acr_name, stage)])

    if stage == "rq2_1_paired":
        command = python_script("scripts/run_rq21_paired_benchmark.py")
        return StagePlan(
            stage,
            [append_rq2_cloud_args(command, args, acr_name, stage, supports_cleanup=True, supports_smoke=True)],
        )

    if stage == "rq2_1b_multinode":
        command = python_script("scripts/run_rq21_paired_benchmark.py") + [
            "--plain-config",
            "configs/rq2/2.1/multinode/rq2_1b_chain2_plain_multinode.yaml",
            "--mtls-config",
            "configs/rq2/2.1/multinode/rq2_1b_chain2_mtls_multinode.yaml",
            "--topology",
            "chain2",
            "--resource-group",
            args.rq21b_resource_group,
            "--cluster-name",
            args.rq21b_cluster_name,
            "--nodepool",
            args.rq21b_nodepool,
            "--node-count",
            str(args.rq21b_node_count),
        ]
        return StagePlan(
            stage,
            [append_rq2_cloud_args(command, args, acr_name, stage, supports_cleanup=True, supports_smoke=True)],
        )

    if stage == "rq2_1_mtls_split":
        command = python_script("scripts/run_rq21_mtls_split.py")
        return StagePlan(
            stage,
            [append_rq2_cloud_args(command, args, acr_name, stage, supports_cleanup=True, supports_smoke=True)],
        )

    if stage == "rq2_1_ablation":
        command = python_script("scripts/run_rq21_ablation.py")
        return StagePlan(
            stage,
            [append_rq2_cloud_args(command, args, acr_name, stage, supports_cleanup=True, supports_smoke=True)],
        )

    if stage == "rq2_2":
        command = python_script("scripts/run_rq22_confidential.py")
        return StagePlan(
            stage,
            [append_rq2_cloud_args(command, args, acr_name, stage, supports_cleanup=False, supports_smoke=False)],
        )

    raise AssertionError(f"unhandled stage: {stage}")


def run_command(command: list[str], *, dry_run: bool) -> None:
    log("$ " + format_command(command))
    if dry_run:
        return
    completed = subprocess.run(command, cwd=str(REPO_ROOT))
    if completed.returncode != 0:
        raise RuntimeError(f"command failed with exit code {completed.returncode}")


def run_capture(command: list[str]) -> str:
    log("$ " + format_command(command))
    completed = subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        if completed.stdout:
            print(completed.stdout, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        raise RuntimeError(f"command failed with exit code {completed.returncode}")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return completed.stdout.strip()


def ensure_kind_for_selected_stages(args: argparse.Namespace, stages: list[str]) -> bool:
    if not {"rq1_4", "rq1_4b"}.intersection(stages):
        return True

    if shutil.which("kind"):
        return True

    local_kind = kind_binary_path()
    if local_kind.exists():
        add_tools_to_path()
        log(f"Using repo-local kind: {local_kind}")
        return True

    if args.no_install_kind:
        warn("kind is required for rq1_4/rq1_4b but was not found on PATH.")
        return False

    asset = kind_asset_name()
    url = f"https://kind.sigs.k8s.io/dl/{args.kind_version}/{asset}"

    if args.dry_run:
        run_command(["mkdir", "-p", str(TOOLS_BIN)], dry_run=True)
        run_command(["curl", "-L", "-o", str(local_kind), url], dry_run=True)
        if platform.system().lower() != "windows":
            run_command(["chmod", "+x", str(local_kind)], dry_run=True)
        add_tools_to_path()
        return True

    TOOLS_BIN.mkdir(parents=True, exist_ok=True)
    run_command(["curl", "-L", "-o", str(local_kind), url], dry_run=False)
    if platform.system().lower() != "windows":
        local_kind.chmod(local_kind.stat().st_mode | 0o755)
    add_tools_to_path()
    log(f"Installed kind {args.kind_version} to {local_kind}")
    return True


def run_stage(plan: StagePlan, *, dry_run: bool, results_root: Path | None = None) -> StageResult:
    started = time.time()
    before = result_dir_snapshot(results_root) if results_root and not dry_run else set()
    try:
        for command in plan.commands:
            run_command(command, dry_run=dry_run)
    except Exception as exc:
        after = result_dir_snapshot(results_root) if results_root and not dry_run else set()
        artifacts = [relative_path(path) for path in sorted(after - before)]
        return StageResult(plan.name, "fail", time.time() - started, str(exc), artifacts)
    after = result_dir_snapshot(results_root) if results_root and not dry_run else set()
    artifacts = [relative_path(path) for path in sorted(after - before)]
    return StageResult(plan.name, "dry-run" if dry_run else "ok", time.time() - started, "", artifacts)


def build_push_and_resolve_image(args: argparse.Namespace, acr_name: str) -> str:
    remote_image = f"{acr_name}.azurecr.io/thesis-inference:{args.image_tag}"
    create_acr_commands = []
    if args.create_acr:
        create_acr_commands = [
            [
                "az",
                "group",
                "create",
                "--name",
                args.acr_resource_group,
                "--location",
                args.acr_location,
            ],
            [
                "az",
                "acr",
                "create",
                "--resource-group",
                args.acr_resource_group,
                "--name",
                acr_name,
                "--sku",
                args.acr_sku,
            ],
        ]

    commands = [
        *create_acr_commands,
        [
            "az",
            "acr",
            "show",
            "--name",
            acr_name,
            "--query",
            "loginServer",
            "--output",
            "tsv",
        ],
        ["az", "acr", "login", "--name", acr_name],
        ["docker", "build", "-t", args.local_image, "."],
        ["docker", "tag", args.local_image, remote_image],
        ["docker", "push", remote_image],
    ]

    for command in commands:
        run_command(command, dry_run=args.dry_run)

    digest_query = [
        "az",
        "acr",
        "repository",
        "show",
        "--name",
        acr_name,
        "--image",
        f"thesis-inference:{args.image_tag}",
        "--query",
        "digest",
        "--output",
        "tsv",
    ]
    if args.dry_run:
        run_command(digest_query, dry_run=True)
        image_ref = f"{acr_name}.azurecr.io/thesis-inference@sha256:{'0' * 64}"
        log(f"Dry-run placeholder pinned image: {image_ref}")
        return image_ref

    digest = validate_digest(run_capture(digest_query))
    image_ref = f"{acr_name}.azurecr.io/thesis-inference@{digest}"
    log(f"Resolved pushed image to pinned reference: {image_ref}")
    return image_ref


def summarize_condition_summary_csv(csv_path: Path) -> dict[str, Any]:
    rows = read_csv_rows(csv_path)
    usable = [row for row in rows if maybe_float(row.get("mean_ms")) is not None]
    if not usable:
        return {}
    best = min(usable, key=lambda row: maybe_float(row.get("mean_ms")) or float("inf"))
    largest_overhead = max(
        usable,
        key=lambda row: maybe_float(row.get("absolute_overhead_ms")) or 0.0,
    )
    baseline_name = str(best.get("baseline_condition") or "")
    baseline = next((row for row in usable if row.get("condition") == baseline_name), None)
    return {
        "summary_type": "condition_summaries",
        "condition_count": len(usable),
        "best_condition": best.get("condition"),
        "best_mean_ms": maybe_float(best.get("mean_ms")),
        "baseline_condition": (baseline or {}).get("condition") or baseline_name or None,
        "baseline_mean_ms": maybe_float((baseline or {}).get("mean_ms")),
        "largest_overhead_condition": largest_overhead.get("condition"),
        "largest_overhead_ms": maybe_float(largest_overhead.get("absolute_overhead_ms")),
        "largest_overhead_pct": maybe_float(largest_overhead.get("pct_overhead_vs_baseline")),
    }


def summarize_internal_timing(artifact_dir: Path) -> dict[str, Any]:
    summary_csv = artifact_dir / "summary.csv"
    if not summary_csv.exists():
        return {}
    rows = read_csv_rows(summary_csv)
    model = next((row for row in rows if row.get("unit_name") == "model"), None)
    level_one = [row for row in rows if row.get("level") == "L1"]
    largest = max(
        level_one,
        key=lambda row: maybe_float(row.get("pct_of_model")) or 0.0,
        default=None,
    )
    overhead = read_json(artifact_dir / "instrumentation_overhead.json") if (artifact_dir / "instrumentation_overhead.json").exists() else {}
    return {
        "summary_type": "internal_timing",
        "model_mean_ms": maybe_float((model or {}).get("mean_ms")),
        "largest_stage": (largest or {}).get("unit_name"),
        "largest_stage_pct": maybe_float((largest or {}).get("pct_of_model")),
        "instrumentation_overhead_ms": maybe_float(overhead.get("overhead_ms")),
        "instrumentation_overhead_pct": maybe_float(overhead.get("overhead_pct")),
    }


def summarize_paired_summary(summary_path: Path) -> dict[str, Any]:
    summary = read_json(summary_path)
    comparison = (summary.get("latency") or {}).get("comparison") or {}
    resources = (summary.get("resources") or {}).get("comparison") or {}
    requirements = summary.get("requirements") or {}
    return {
        "summary_type": "paired",
        "stage": summary.get("stage") or "RQ2.1",
        "topology": summary.get("topology"),
        "placement_mode": summary.get("placement_mode"),
        "mean_latency_overhead_ms": maybe_float(comparison.get("mean_latency_overhead_ms")),
        "mean_latency_overhead_pct": maybe_float(comparison.get("mean_latency_overhead_pct")),
        "p95_latency_overhead_ms": maybe_float(comparison.get("p95_latency_overhead_ms")),
        "sidecar_cpu_mcores_mean_overhead": maybe_float(resources.get("sidecar_cpu_mcores_mean_overhead")),
        "sidecar_memory_mib_mean_overhead": maybe_float(resources.get("sidecar_memory_mib_mean_overhead")),
        "resource_metrics_complete": requirements.get("resource_metrics_complete"),
        "security_validation_complete": requirements.get("security_validation_complete"),
        "blocking_issues": requirements.get("blocking_issues") or [],
    }


def summarize_split_summary(summary_path: Path) -> dict[str, Any]:
    summary = read_json(summary_path)
    by_condition = (summary.get("latency") or {}).get("by_condition") or {}
    split_deltas: dict[str, dict[str, float]] = {}
    for key, row in by_condition.items():
        split = str(row.get("split_key") or "")
        mode = str(row.get("security_mode") or "")
        if split and mode in {"plain", "mtls"}:
            split_deltas.setdefault(split, {})[mode] = maybe_float(row.get("mean_ms")) or 0.0
    deltas = {
        split: values["mtls"] - values["plain"]
        for split, values in split_deltas.items()
        if {"plain", "mtls"}.issubset(values)
    }
    requirements = summary.get("requirements") or {}
    return {
        "summary_type": "split_sensitivity",
        "topology": summary.get("topology"),
        "split_latency_deltas_ms": dict(sorted(deltas.items())),
        "resource_metrics_complete": requirements.get("resource_metrics_complete"),
        "validation_complete": requirements.get("validation_complete"),
        "blocking_issues": requirements.get("blocking_issues") or [],
    }


def summarize_ablation_summary(summary_path: Path) -> dict[str, Any]:
    summary = read_json(summary_path)
    deltas = (summary.get("latency") or {}).get("adjacent_deltas") or {}
    extracted = {
        name: {
            "label": payload.get("label"),
            "mean_latency_delta_ms": maybe_float(payload.get("mean_latency_delta_ms")),
            "mean_latency_delta_pct": maybe_float(payload.get("mean_latency_delta_pct")),
        }
        for name, payload in deltas.items()
        if isinstance(payload, dict)
    }
    requirements = summary.get("requirements") or {}
    return {
        "summary_type": "ablation",
        "topology": summary.get("topology"),
        "adjacent_deltas": extracted,
        "resource_metrics_complete": requirements.get("resource_metrics_complete"),
        "validation_complete": requirements.get("validation_complete"),
        "blocking_issues": requirements.get("blocking_issues") or [],
    }


def summarize_rq22(artifact_dir: Path) -> dict[str, Any]:
    rolling_summary = artifact_dir / "rq22_rolling_summary.json"
    summary = read_json(rolling_summary) if rolling_summary.exists() else {}
    groups: dict[str, list[float]] = {}
    for raw_path in artifact_dir.glob("conditions/*/benchmark/raw_iterations.csv"):
        for row in read_csv_rows(raw_path):
            condition = str(row.get("condition") or "")
            if "confidential" in condition:
                key = "confidential"
            elif "standard" in condition:
                key = "standard"
            else:
                key = condition or "unknown"
            value = maybe_float(row.get("end_to_end_ms"))
            if value is not None:
                groups.setdefault(key, []).append(value)
    means = {key: sum(values) / len(values) for key, values in groups.items() if values}
    delta_ms = None
    delta_pct = None
    if {"standard", "confidential"}.issubset(means):
        delta_ms = means["confidential"] - means["standard"]
        if means["standard"]:
            delta_pct = (delta_ms / means["standard"]) * 100.0
    return {
        "summary_type": "rq22_confidential",
        "status": summary.get("status"),
        "completed_executions": len(summary.get("completed") or []),
        "standard_mean_ms": means.get("standard"),
        "confidential_mean_ms": means.get("confidential"),
        "mean_latency_overhead_ms": delta_ms,
        "mean_latency_overhead_pct": delta_pct,
        "effective_image_ref": summary.get("effective_image_ref"),
    }


def summarize_artifact_dir(artifact_dir: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "artifact_dir": relative_path(artifact_dir),
        "name": artifact_dir.name,
        "summary_type": "unknown",
    }
    try:
        if (artifact_dir / "merged" / "paired_summary.json").exists():
            summary.update(summarize_paired_summary(artifact_dir / "merged" / "paired_summary.json"))
        elif (artifact_dir / "merged" / "split_sensitivity_summary.json").exists():
            summary.update(summarize_split_summary(artifact_dir / "merged" / "split_sensitivity_summary.json"))
        elif (artifact_dir / "merged" / "rq2_1_ablation_summary.json").exists():
            summary.update(summarize_ablation_summary(artifact_dir / "merged" / "rq2_1_ablation_summary.json"))
        elif (artifact_dir / "rq22_rolling_summary.json").exists():
            summary.update(summarize_rq22(artifact_dir))
        elif (artifact_dir / "condition_summaries.csv").exists():
            summary.update(summarize_condition_summary_csv(artifact_dir / "condition_summaries.csv"))
        elif (artifact_dir / "merged_results" / "condition_summaries.csv").exists():
            summary.update(summarize_condition_summary_csv(artifact_dir / "merged_results" / "condition_summaries.csv"))
        elif (artifact_dir / "summary.csv").exists():
            summary.update(summarize_internal_timing(artifact_dir))
    except Exception as exc:
        summary["summary_error"] = str(exc)
    return summary


def stage_headline(artifact_summary: dict[str, Any]) -> str:
    summary_type = artifact_summary.get("summary_type")
    if summary_type == "paired":
        return (
            f"{artifact_summary.get('stage', 'RQ2.1')} "
            f"{artifact_summary.get('topology')}: "
            f"+{format_metric(artifact_summary.get('mean_latency_overhead_ms'))} ms "
            f"({format_metric(artifact_summary.get('mean_latency_overhead_pct'))}%)"
        )
    if summary_type == "split_sensitivity":
        deltas = artifact_summary.get("split_latency_deltas_ms") or {}
        formatted = ", ".join(
            f"{split} +{format_metric(delta)} ms"
            for split, delta in deltas.items()
        )
        return f"mTLS split deltas: {formatted}" if formatted else "mTLS split sensitivity summary"
    if summary_type == "ablation":
        deltas = artifact_summary.get("adjacent_deltas") or {}
        total = deltas.get("c3_minus_c0") or {}
        return (
            "hardened path "
            f"+{format_metric(total.get('mean_latency_delta_ms'))} ms "
            f"({format_metric(total.get('mean_latency_delta_pct'))}%)"
        )
    if summary_type == "rq22_confidential":
        return (
            f"confidential service2 +{format_metric(artifact_summary.get('mean_latency_overhead_ms'))} ms "
            f"({format_metric(artifact_summary.get('mean_latency_overhead_pct'))}%)"
        )
    if summary_type == "condition_summaries":
        return (
            f"best={artifact_summary.get('best_condition')} "
            f"{format_metric(artifact_summary.get('best_mean_ms'))} ms; "
            f"largest overhead={artifact_summary.get('largest_overhead_condition')} "
            f"+{format_metric(artifact_summary.get('largest_overhead_ms'))} ms"
        )
    if summary_type == "internal_timing":
        return (
            f"model {format_metric(artifact_summary.get('model_mean_ms'))} ms; "
            f"largest stage={artifact_summary.get('largest_stage')} "
            f"{format_metric(artifact_summary.get('largest_stage_pct'))}%"
        )
    return "no known summary parser"


def stage_checks(artifact_summary: dict[str, Any]) -> str:
    checks: list[str] = []
    for key, label in (
        ("resource_metrics_complete", "resources"),
        ("security_validation_complete", "security"),
        ("validation_complete", "validation"),
    ):
        if key in artifact_summary:
            checks.append(f"{label}={artifact_summary.get(key)}")
    blockers = artifact_summary.get("blocking_issues")
    if blockers:
        checks.append(f"blockers={len(blockers)}")
    if artifact_summary.get("summary_error"):
        checks.append("summary_error")
    return ", ".join(checks) if checks else ""


def write_uniform_run_report(
    *,
    args: argparse.Namespace,
    stages: list[str],
    results: list[StageResult],
    run_stamp: str,
) -> dict[str, Path]:
    results_root = Path(args.results_root).resolve()
    report_dir = results_root / f"uniform_run_{run_stamp}"
    report_dir.mkdir(parents=True, exist_ok=True)

    stage_payloads: list[dict[str, Any]] = []
    for result in results:
        artifact_summaries = [
            summarize_artifact_dir((REPO_ROOT / artifact).resolve() if not Path(artifact).is_absolute() else Path(artifact))
            for artifact in result.artifact_dirs
        ]
        stage_payloads.append({
            "name": result.name,
            "status": result.status,
            "elapsed_seconds": result.elapsed_seconds,
            "detail": result.detail,
            "artifact_dirs": result.artifact_dirs,
            "artifact_summaries": artifact_summaries,
        })

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "wrapper_run_stamp": run_stamp,
        "image_ref": args.image_ref,
        "acr_name": args.acr_name,
        "selected_stages": stages,
        "include_optional": bool(args.include_optional),
        "destroy_cloud_on_success": bool(args.destroy_cloud_on_success),
        "destroy_cloud_on_failure": bool(args.destroy_cloud_on_failure),
        "results": stage_payloads,
    }

    json_path = report_dir / "uniform_run_summary.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Uniform Thesis Run Summary",
        "",
        f"- Generated: `{payload['generated_at']}`",
        f"- Image: `{args.image_ref}`",
        f"- Stages: `{', '.join(stages)}`",
        f"- Destroy cloud on success: `{args.destroy_cloud_on_success}`",
        f"- Destroy cloud on failure: `{args.destroy_cloud_on_failure}`",
        "",
        "## Stage Overview",
        "",
        "| Stage | Status | Time | Artifacts | Headline | Checks |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for stage in stage_payloads:
        artifacts = "<br>".join(f"`{item}`" for item in stage["artifact_dirs"]) or ""
        if stage["artifact_summaries"]:
            headline = "<br>".join(stage_headline(item) for item in stage["artifact_summaries"])
            checks = "<br>".join(stage_checks(item) for item in stage["artifact_summaries"] if stage_checks(item))
        else:
            headline = stage["detail"] if stage["status"] == "fail" else ""
            checks = ""
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{stage['name']}`",
                    f"`{stage['status']}`",
                    f"{stage['elapsed_seconds']:.1f}s",
                    artifacts,
                    headline.replace("|", "\\|"),
                    checks.replace("|", "\\|"),
                ]
            )
            + " |"
        )

    lines.extend([
        "",
        "## Notes",
        "",
        "- This file is a run index, not a replacement for the per-experiment analysis artifacts.",
        "- Treat any failed stage or listed blocker as requiring manual inspection before thesis use.",
        "- The JSON file beside this report preserves the same information in machine-readable form.",
        "",
    ])

    md_path = report_dir / "uniform_run_summary.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the thesis experiment scripts with one pinned thesis-inference "
            "image, either reused via --image-ref or created via --build-push-image."
        )
    )
    parser.add_argument(
        "--image-ref",
        default=None,
        help="Pinned image reference: <acr>.azurecr.io/thesis-inference@sha256:<digest>",
    )
    parser.add_argument(
        "--acr-name",
        default=None,
        help="ACR name without .azurecr.io. Required for --build-push-image; otherwise defaults to the registry in --image-ref.",
    )
    parser.add_argument(
        "--build-push-image",
        action="store_true",
        help="Build the Docker image, push it to --acr-name, resolve its digest, and use that digest for all stages.",
    )
    parser.add_argument(
        "--create-acr",
        action="store_true",
        help="Create the target ACR before building/pushing. Use when az acr list is empty.",
    )
    parser.add_argument(
        "--acr-resource-group",
        default="rg-thesis-rq15",
        help="Resource group for --create-acr.",
    )
    parser.add_argument(
        "--acr-location",
        default="swedencentral",
        help="Azure region for --create-acr.",
    )
    parser.add_argument(
        "--acr-sku",
        default="Basic",
        help="ACR SKU for --create-acr.",
    )
    parser.add_argument(
        "--image-tag",
        default=f"uniform-{utc_run_stamp()}",
        help="ACR tag to use with --build-push-image.",
    )
    parser.add_argument(
        "--local-image",
        default=LOCAL_IMAGE_TAG,
        help="Local Docker image tag used for the build before pushing.",
    )
    parser.add_argument(
        "--only",
        default=None,
        help=f"Comma-separated stages to run. Valid: {', '.join(ALL_STAGES)}",
    )
    parser.add_argument("--skip", default=None, help="Comma-separated stages to remove from the selected set.")
    parser.add_argument(
        "--include-optional",
        action="store_true",
        help="Include optional sensitivity stages such as rq2_1b_multinode.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")
    parser.add_argument("--continue-on-failure", action="store_true", help="Continue after a stage fails.")
    parser.add_argument(
        "--skip-acr-login",
        action="store_true",
        help="Do not run 'az acr login' before container-based stages.",
    )
    parser.set_defaults(provision_cloud=True)
    parser.add_argument(
        "--provision-cloud",
        dest="provision_cloud",
        action="store_true",
        help="Provision AKS-backed stages through their inner Terraform lifecycle. This is the default.",
    )
    parser.add_argument(
        "--reuse-cloud",
        dest="provision_cloud",
        action="store_false",
        help="Reuse existing AKS clusters instead of provisioning through the inner runners.",
    )
    parser.add_argument(
        "--destroy-cloud-on-success",
        action="store_true",
        help="Pass each runner's infrastructure teardown-on-success flag.",
    )
    parser.add_argument(
        "--destroy-cloud-on-failure",
        action="store_true",
        help="Pass each runner's infrastructure teardown-on-failure flag.",
    )
    parser.add_argument("--cleanup-on-failure", action="store_true", help="Pass namespace cleanup where supported.")
    parser.add_argument("--preserve-namespaces", action="store_true", help="Keep RQ2 namespaces where supported.")
    parser.add_argument("--generate-only", action="store_true", help="Generate RQ2 manifests/configs without live benchmark where supported.")
    parser.add_argument("--smoke", action="store_true", help="Use RQ2 smoke profiles where supported.")
    parser.add_argument("--skip-mesh-enable", action="store_true", help="Pass through to RQ2 mesh-aware runners.")
    parser.add_argument(
        "--rq2-passes",
        type=int,
        default=DEFAULT_RQ2_PASSES,
        help=(
            "Default outer passes for RQ2 stages. The source RQ2 configs use "
            "benchmark.rounds=1 so passes provide the interleaved repetitions "
            f"(default: {DEFAULT_RQ2_PASSES}; smoke mode uses 1 unless a "
            "stage-specific value is set)."
        ),
    )
    parser.add_argument("--rq2-paired-passes", type=int, default=None, help="Override passes for rq2_1_paired.")
    parser.add_argument("--rq21b-paired-passes", type=int, default=None, help="Override passes for rq2_1b_multinode.")
    parser.add_argument("--rq2-split-passes", type=int, default=None, help="Override passes for rq2_1_mtls_split.")
    parser.add_argument("--rq2-ablation-passes", type=int, default=None, help="Override passes for rq2_1_ablation.")
    parser.add_argument("--rq22-paired-passes", type=int, default=None, help="Override passes for rq2_2.")
    parser.add_argument(
        "--results-root",
        default=str(REPO_ROOT / "results"),
        help="Results root passed to runners that support it.",
    )
    parser.add_argument(
        "--rq14-rolling",
        action="store_true",
        help="Backward-compatible no-op; RQ1.4 uses rolling mode by default.",
    )
    parser.add_argument("--rq15-nodepool", default=None, help="Override RQ1.5 nodepool.")
    parser.add_argument("--rq15-resource-group", default="rg-thesis-rq15", help="RQ1.5 resource group.")
    parser.add_argument("--rq15-cluster-name", default="thesis-rq15", help="RQ1.5 AKS cluster name.")
    parser.add_argument(
        "--rq15-resume-artifact-dir",
        default=None,
        help="Existing RQ1.5 export directory whose complete partials should be reused.",
    )
    parser.add_argument("--rq15b-resource-group", default="rg-thesis-rq15b", help="RQ1.5b resource group.")
    parser.add_argument("--rq15b-cluster-name", default="thesis-rq15b", help="RQ1.5b AKS cluster name.")
    parser.add_argument("--rq15b-nodepool", default="rq15bpool", help="RQ1.5b nodepool label.")
    parser.add_argument("--rq15b-node-count", type=int, default=6, help="RQ1.5b node count.")
    parser.add_argument(
        "--rq15b-resume-artifact-dir",
        default=None,
        help="Existing RQ1.5b export directory whose complete partials should be reused.",
    )
    parser.add_argument("--rq21b-resource-group", default="rg-thesis-rq21b", help="RQ2.1b resource group.")
    parser.add_argument("--rq21b-cluster-name", default="thesis-rq21b", help="RQ2.1b AKS cluster name.")
    parser.add_argument("--rq21b-nodepool", default="rq21bpool", help="RQ2.1b benchmark nodepool label.")
    parser.add_argument("--rq21b-node-count", type=int, default=3, help="RQ2.1b benchmark node count.")
    parser.add_argument(
        "--rq15-condition-retries",
        type=int,
        default=1,
        help="Retries per RQ1.5/RQ1.5b rolling condition when artifacts are incomplete.",
    )
    parser.add_argument(
        "--kind-version",
        default=DEFAULT_KIND_VERSION,
        help="kind release to install locally when rq1_4/rq1_4b need kind and it is missing.",
    )
    parser.add_argument(
        "--no-install-kind",
        action="store_true",
        help="Fail instead of downloading a repo-local kind binary when kind is missing.",
    )
    args = parser.parse_args()
    if args.rq15_condition_retries < 0:
        parser.error("--rq15-condition-retries must be >= 0")
    pass_args = {
        "--rq2-passes": args.rq2_passes,
        "--rq2-paired-passes": args.rq2_paired_passes,
        "--rq21b-paired-passes": args.rq21b_paired_passes,
        "--rq2-split-passes": args.rq2_split_passes,
        "--rq2-ablation-passes": args.rq2_ablation_passes,
        "--rq22-paired-passes": args.rq22_paired_passes,
    }
    for flag, value in pass_args.items():
        if value is not None and value < 1:
            parser.error(f"{flag} must be >= 1")
    if Path(args.results_root).name == LEGACY_RESULTS_ROOT:
        parser.error(f"--results-root must use results, not the legacy {LEGACY_RESULTS_ROOT} directory")
    return args


def main() -> int:
    args = parse_args()
    if not drop_sudo_root_to_invoking_user():
        return 1

    run_stamp = utc_run_stamp()
    stages = resolve_stages(args)
    log(f"Stages: {', '.join(stages)}")
    if args.dry_run:
        log("Dry run: no commands will be executed.")

    if not ensure_kind_for_selected_stages(args, stages):
        return 1

    if args.build_push_image and args.image_ref:
        raise SystemExit("--build-push-image cannot be combined with --image-ref")
    if args.build_push_image:
        if not args.acr_name:
            raise SystemExit("--acr-name is required with --build-push-image")
        acr_name = args.acr_name
        log(f"Image destination tag: {acr_name}.azurecr.io/thesis-inference:{args.image_tag}")
        try:
            args.image_ref = build_push_and_resolve_image(args, acr_name)
        except Exception as exc:
            warn(f"Image build/push failed: {exc}")
            return 1
    else:
        if not args.image_ref:
            raise SystemExit("Provide either --image-ref or --build-push-image --acr-name")
        image_acr_name = validate_image_ref(args.image_ref)
        acr_name = args.acr_name or image_acr_name
        if acr_name != image_acr_name:
            raise SystemExit(
                f"--acr-name ({acr_name}) must match the registry in --image-ref ({image_acr_name}) "
                "so every stage uses the same image source."
            )

    log(f"Uniform image: {args.image_ref}")
    plans = [build_stage_plan(stage, args, acr_name) for stage in stages]
    results_root = Path(args.results_root).resolve()

    results: list[StageResult] = []
    if CONTAINER_STAGES.intersection(stages) and not args.skip_acr_login and not args.build_push_image:
        login_plan = StagePlan("acr_login", [["az", "acr", "login", "--name", acr_name]])
        login_result = run_stage(login_plan, dry_run=args.dry_run, results_root=results_root)
        results.append(login_result)
        if login_result.status == "fail" and not args.continue_on_failure:
            plans = []

    for plan in plans:
        log("=" * 72)
        log(f"Stage: {plan.name}")
        log("=" * 72)
        result = run_stage(plan, dry_run=args.dry_run, results_root=results_root)
        results.append(result)
        if result.status == "fail":
            warn(f"Stage {result.name} failed: {result.detail}")
            if not args.continue_on_failure:
                break

    log("=" * 72)
    log("Summary")
    log("=" * 72)
    exit_code = 0
    for result in results:
        if result.status == "fail":
            exit_code = 1
        suffix = f" - {result.detail}" if result.detail else ""
        log(f"{result.name}: {result.status} ({result.elapsed_seconds:.1f}s){suffix}")
    if not args.dry_run:
        try:
            report_paths = write_uniform_run_report(
                args=args,
                stages=stages,
                results=results,
                run_stamp=run_stamp,
            )
            log(f"Uniform run report: {report_paths['markdown']}")
        except Exception as exc:
            warn(f"Failed to write uniform run report: {exc}")
            if exit_code == 0:
                exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

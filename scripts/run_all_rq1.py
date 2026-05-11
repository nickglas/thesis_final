"""End-to-end orchestrator for the full RQ1 experiment family.

Runs RQ1.1 → RQ1.5 (and optionally the RQ1.4b / RQ1.5b multi-node sensitivity
stages) sequentially, sharing one Docker image and tearing down per-stage
infrastructure on success OR failure. The wrapper is fail-fast: it aborts on
the first stage that fails, after ensuring that stage's teardown has run.

Usage:
    python scripts/run_all_rq1.py --acr-name <acr>           # all stages
    python scripts/run_all_rq1.py --skip-cloud --acr-name <acr>  # local + kind only
    python scripts/run_all_rq1.py --only rq1_5,rq1_5b --acr-name <acr>

Stages (default order):
    rq1_1   — local CPU split benchmark
    rq1_2   — local CPU split benchmark
    rq1_3   — local internal timing profile
    rq1_4   — kind single-node Kubernetes chain
    rq1_4b  — kind multi-node Kubernetes chain (sensitivity)
    rq1_5   — AKS single-node (thesis-facing primary)
    rq1_5b  — AKS multi-node (sensitivity)

Per-stage teardown:
    Local stages have no teardown.
    kind stages: ``kind delete cluster`` always runs.
    AKS stages: the existing run_rq15_fully_controlled.py orchestrator handles
    teardown via ``--delete-resource-group-on-success`` and
    ``--delete-resource-group-on-failure``, which this wrapper passes through.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CONFIGS = {
    "rq1_1": REPO_ROOT / "configs" / "rq1" / "1.1" / "rq1_1_fully_controlled.yaml",
    "rq1_2": REPO_ROOT / "configs" / "rq1" / "1.2" / "rq1_2_fully_controlled.yaml",
    "rq1_3": REPO_ROOT / "configs" / "internal_timing" / "timing_full.yaml",
    "rq1_4": REPO_ROOT / "configs" / "rq1" / "1.4" / "rq1_4_fully_controlled.yaml",
    "rq1_4b": REPO_ROOT / "configs" / "rq1" / "1.4" / "rq1_4b_multinode.yaml",
    "rq1_5": REPO_ROOT / "configs" / "rq1" / "1.5" / "rq1_5_full.yaml",
    "rq1_5b": REPO_ROOT / "configs" / "rq1" / "1.5" / "rq1_5b_multinode.yaml",
}

KIND_CONFIGS = {
    "rq1_4": REPO_ROOT / "k8s" / "kind" / "kind-single-node.yaml",
    "rq1_4b": REPO_ROOT / "k8s" / "kind" / "kind-multi-node.yaml",
}

KIND_CLUSTER_NAMES = {
    "rq1_4": "thesis-rq14",
    "rq1_4b": "thesis-rq14b",
}

KIND_NAMESPACES = {
    "rq1_4": "rq14",
    "rq1_4b": "rq14b",
}

DEFAULT_ORDER = ["rq1_1", "rq1_2", "rq1_3", "rq1_4", "rq1_4b", "rq1_5", "rq1_5b"]


def log(message: str) -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}", flush=True)


def warn(message: str) -> None:
    print(
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] WARN: {message}",
        file=sys.stderr,
        flush=True,
    )


def ensure_command(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"Required command not found on PATH: {name}")


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> int:
    log("$ " + " ".join(cmd))
    completed = subprocess.run(cmd, cwd=str(cwd) if cwd else None)
    if check and completed.returncode != 0:
        raise StageFailure(f"Command failed with exit code {completed.returncode}: {' '.join(cmd)}")
    return completed.returncode


class StageFailure(RuntimeError):
    pass


@dataclass
class StageResult:
    name: str
    status: str
    detail: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full RQ1 experiment family end-to-end")
    parser.add_argument(
        "--acr-name",
        default=None,
        help="Azure Container Registry name (no .azurecr.io suffix). Required for AKS stages.",
    )
    parser.add_argument(
        "--only",
        default=None,
        help="Comma-separated subset of stages to run (e.g. 'rq1_4,rq1_5').",
    )
    parser.add_argument("--skip-local", action="store_true", help="Skip rq1_1, rq1_2, rq1_3")
    parser.add_argument("--skip-kind", action="store_true", help="Skip rq1_4 and rq1_4b")
    parser.add_argument("--skip-cloud", action="store_true", help="Skip rq1_5 and rq1_5b")
    parser.add_argument("--skip-multinode", action="store_true", help="Skip rq1_4b and rq1_5b sensitivity stages")
    parser.add_argument("--skip-image-build", action="store_true", help="Reuse an already-built thesis-inference:latest image")
    parser.add_argument(
        "--continue-on-failure",
        action="store_true",
        help="Don't abort the wrapper after the first stage failure. Each stage still tears down its own infra.",
    )
    return parser.parse_args()


def resolve_stage_list(args: argparse.Namespace) -> list[str]:
    if args.only:
        names = [name.strip() for name in args.only.split(",") if name.strip()]
        unknown = [name for name in names if name not in CONFIGS]
        if unknown:
            raise SystemExit(f"Unknown stage(s): {', '.join(unknown)}. Valid: {', '.join(CONFIGS)}")
        return names

    stages = list(DEFAULT_ORDER)
    if args.skip_local:
        stages = [name for name in stages if name not in {"rq1_1", "rq1_2", "rq1_3"}]
    if args.skip_kind:
        stages = [name for name in stages if name not in {"rq1_4", "rq1_4b"}]
    if args.skip_cloud:
        stages = [name for name in stages if name not in {"rq1_5", "rq1_5b"}]
    if args.skip_multinode:
        stages = [name for name in stages if name not in {"rq1_4b", "rq1_5b"}]
    return stages


def build_image_once(skip_build: bool) -> None:
    if skip_build:
        log("Skipping docker build (--skip-image-build).")
        return
    ensure_command("docker")
    log("Building shared thesis-inference:latest image once.")
    run(["docker", "build", "-t", "thesis-inference:latest", "."], cwd=REPO_ROOT)


# ---------------------------------------------------------------------------
# Local stages
# ---------------------------------------------------------------------------


def run_local_split(stage_name: str) -> None:
    config = CONFIGS[stage_name]
    log(f"Running {stage_name} via run_experiment.py.")
    run(
        [
            sys.executable,
            str(REPO_ROOT / "run_experiment.py"),
            "--config",
            str(config),
            "--run-analysis",
        ]
    )


def run_internal_timing(stage_name: str) -> None:
    config = CONFIGS[stage_name]
    log(f"Running {stage_name} via run_internal_timing.py.")
    run(
        [
            sys.executable,
            str(REPO_ROOT / "run_internal_timing.py"),
            "--config",
            str(config),
            "--run-analysis",
        ]
    )


# ---------------------------------------------------------------------------
# kind stages (single-node and multi-node)
# ---------------------------------------------------------------------------


def kind_cluster_exists(cluster_name: str) -> bool:
    result = subprocess.run(
        ["kind", "get", "clusters"], capture_output=True, text=True, check=False
    )
    return cluster_name in {line.strip() for line in (result.stdout or "").splitlines()}


def kind_delete_cluster(cluster_name: str) -> None:
    if not kind_cluster_exists(cluster_name):
        return
    log(f"Deleting kind cluster {cluster_name}.")
    subprocess.run(["kind", "delete", "cluster", "--name", cluster_name], check=False)


def run_kind_stage(stage_name: str) -> None:
    ensure_command("kind")
    ensure_command("kubectl")
    cluster_name = KIND_CLUSTER_NAMES[stage_name]
    namespace = KIND_NAMESPACES[stage_name]
    cluster_config = KIND_CONFIGS[stage_name]
    experiment_config = CONFIGS[stage_name]

    if kind_cluster_exists(cluster_name):
        warn(f"kind cluster {cluster_name} already exists; deleting before recreating.")
        kind_delete_cluster(cluster_name)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    host_results_dir = REPO_ROOT / "results_exports" / f"{stage_name}_{timestamp}"
    host_results_dir.mkdir(parents=True, exist_ok=True)

    try:
        log(f"Creating kind cluster {cluster_name} from {cluster_config.relative_to(REPO_ROOT)}.")
        run(["kind", "create", "cluster", "--name", cluster_name, "--config", str(cluster_config)])

        log("Loading thesis-inference:latest into kind nodes.")
        run(["kind", "load", "docker-image", "thesis-inference:latest", "--name", cluster_name])

        # Generate manifests. For multinode use the AKS generator (it knows
        # multi_node_anti_affinity); the empty --nodepool suppresses the
        # AKS-only agentpool nodeSelector.
        if stage_name == "rq1_4b":
            output_dir = REPO_ROOT / "k8s" / "aks" / "generated"
            log("Generating multi-node manifests via the AKS generator (anti-affinity aware).")
            run(
                [
                    sys.executable,
                    str(REPO_ROOT / "k8s" / "aks" / "generate_aks_manifests.py"),
                    "--config",
                    str(experiment_config),
                    "--nodepool",
                    "",
                    "--output-dir",
                    str(output_dir),
                ]
            )
        else:
            output_dir = REPO_ROOT / "k8s" / "base" / "generated"
            log("Generating single-node manifests via the local generator.")
            run(
                [
                    sys.executable,
                    str(REPO_ROOT / "k8s" / "generate_manifests.py"),
                    "--config",
                    str(experiment_config),
                    "--all",
                ]
            )

        log("Applying generated manifests.")
        run(["kubectl", "apply", "-f", str(output_dir)])

        if stage_name == "rq1_4":
            # The local generator does not emit a client pod manifest; use the
            # checked-in client manifest (which already pins namespace=rq14).
            run(["kubectl", "apply", "-f", str(REPO_ROOT / "k8s" / "base" / "client-pod.yaml")])

        log(f"Waiting for benchmark-client to be Ready in namespace {namespace}.")
        run(
            [
                "kubectl",
                "wait",
                "--for=condition=Ready",
                "pod/benchmark-client",
                "-n",
                namespace,
                "--timeout=180s",
            ]
        )

        log(f"Running benchmark inside the cluster for {stage_name}.")
        run(
            [
                "kubectl",
                "exec",
                "-n",
                namespace,
                "benchmark-client",
                "--",
                "python",
                "run_k8s_experiment.py",
                "--config",
                str(experiment_config.relative_to(REPO_ROOT)),
                "--run-analysis",
            ]
        )

        log(f"Copying results out of the client pod to {host_results_dir}.")
        run(
            [
                "kubectl",
                "cp",
                f"{namespace}/benchmark-client:/app/results/",
                str(host_results_dir),
            ]
        )
    finally:
        kind_delete_cluster(cluster_name)


# ---------------------------------------------------------------------------
# AKS stages
# ---------------------------------------------------------------------------


def run_aks_stage(stage_name: str, acr_name: str) -> None:
    if not acr_name:
        raise StageFailure(f"{stage_name} requires --acr-name")
    config = CONFIGS[stage_name]
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "run_rq15_fully_controlled.py"),
        "--config",
        str(config),
        "--provision",
        "--push",
        "--acr-name",
        acr_name,
        "--delete-resource-group-on-success",
        "--delete-resource-group-on-failure",
    ]

    if stage_name == "rq1_5b":
        cmd += [
            "--resource-group",
            "rg-thesis-rq15b",
            "--cluster-name",
            "thesis-rq15b",
            "--nodepool",
            "rq15bpool",
            "--node-count",
            "6",
        ]
    log(f"Running {stage_name} via run_rq15_fully_controlled.py.")
    run(cmd)


# ---------------------------------------------------------------------------
# Stage dispatch
# ---------------------------------------------------------------------------


STAGE_RUNNERS = {
    "rq1_1": lambda args: run_local_split("rq1_1"),
    "rq1_2": lambda args: run_local_split("rq1_2"),
    "rq1_3": lambda args: run_internal_timing("rq1_3"),
    "rq1_4": lambda args: run_kind_stage("rq1_4"),
    "rq1_4b": lambda args: run_kind_stage("rq1_4b"),
    "rq1_5": lambda args: run_aks_stage("rq1_5", args.acr_name),
    "rq1_5b": lambda args: run_aks_stage("rq1_5b", args.acr_name),
}


def main() -> int:
    args = parse_args()
    stages = resolve_stage_list(args)
    if not stages:
        log("No stages selected; nothing to do.")
        return 0

    needs_image = any(name in {"rq1_4", "rq1_4b", "rq1_5", "rq1_5b"} for name in stages)
    if needs_image:
        build_image_once(args.skip_image_build)

    needs_acr = any(name in {"rq1_5", "rq1_5b"} for name in stages)
    if needs_acr and not args.acr_name:
        raise SystemExit("--acr-name is required when running AKS stages (rq1_5 / rq1_5b)")

    log(f"Stage plan: {stages}")
    results: list[StageResult] = []
    overall_status = 0

    for stage_name in stages:
        log("=" * 60)
        log(f"Stage: {stage_name}")
        log("=" * 60)
        started_at = time.time()
        try:
            STAGE_RUNNERS[stage_name](args)
        except StageFailure as exc:
            elapsed = time.time() - started_at
            warn(f"Stage {stage_name} FAILED after {elapsed:.1f}s: {exc}")
            results.append(StageResult(stage_name, "fail", str(exc)))
            overall_status = 1
            if not args.continue_on_failure:
                break
        except KeyboardInterrupt:
            warn(f"Stage {stage_name} interrupted by user.")
            results.append(StageResult(stage_name, "interrupted"))
            overall_status = 130
            break
        except Exception as exc:
            elapsed = time.time() - started_at
            warn(f"Stage {stage_name} FAILED after {elapsed:.1f}s with unexpected error: {exc}")
            results.append(StageResult(stage_name, "fail", repr(exc)))
            overall_status = 1
            if not args.continue_on_failure:
                break
        else:
            elapsed = time.time() - started_at
            log(f"Stage {stage_name} OK after {elapsed:.1f}s.")
            results.append(StageResult(stage_name, "ok"))

    log("=" * 60)
    log("Summary")
    log("=" * 60)
    for result in results:
        suffix = f" — {result.detail}" if result.detail else ""
        log(f"  {result.name}: {result.status}{suffix}")
    return overall_status


if __name__ == "__main__":
    raise SystemExit(main())

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
import csv
import json
import os
import re
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


def run_capture(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> str:
    log("$ " + " ".join(cmd))
    completed = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    if check and completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        suffix = f": {detail}" if detail else ""
        raise StageFailure(
            f"Command failed with exit code {completed.returncode}: {' '.join(cmd)}{suffix}"
        )
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return (completed.stdout or "").strip()


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
        "--image-ref",
        default=None,
        help="Pinned image reference to pass through to RQ1.4 rolling orchestration.",
    )
    parser.add_argument(
        "--rq14-rolling",
        action="store_true",
        help="Run RQ1.4 one condition at a time to fit local kind capacity.",
    )
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


def condition_client_manifest(output_dir: Path, condition_name: str) -> Path:
    sanitized = re.sub(r"[^a-z0-9-]", "-", condition_name.lower().replace("_", "-"))
    sanitized = re.sub(r"-+", "-", sanitized).strip("-")
    condition_path = output_dir / f"99_benchmark_client_{sanitized}.yaml"
    if condition_path.exists():
        return condition_path
    return output_dir / "99_benchmark_client.yaml"


def wait_for_condition_ready(namespace: str, condition_name: str, expected_count: int, timeout_seconds: int) -> None:
    deadline = time.time() + timeout_seconds + 60
    deployment_names: list[str] = []
    while True:
        output = run_capture(
            [
                "kubectl",
                "get",
                "deployments",
                "-n",
                namespace,
                "-l",
                f"condition={condition_name}",
                "-o",
                "jsonpath={range .items[*]}{.metadata.name}{\"\\n\"}{end}",
            ],
            check=False,
        )
        deployment_names = [line.strip() for line in output.splitlines() if line.strip()]
        if len(deployment_names) == expected_count:
            break
        if time.time() >= deadline:
            raise StageFailure(
                f"Timed out waiting for {expected_count} deployment object(s) for {condition_name}"
            )
        time.sleep(2)

    for deployment_name in deployment_names:
        log(f"Waiting for deployment {deployment_name} rollout.")
        run(
            [
                "kubectl",
                "rollout",
                "status",
                f"deployment/{deployment_name}",
                "-n",
                namespace,
                f"--timeout={timeout_seconds}s",
            ]
        )

    log(f"Waiting for {condition_name} pod(s) to become Ready.")
    run(
        [
            "kubectl",
            "wait",
            "--for=condition=Ready",
            "pod",
            "-n",
            namespace,
            "-l",
            f"condition={condition_name}",
            f"--timeout={timeout_seconds}s",
        ]
    )


def wait_for_condition_removed(namespace: str, condition_name: str, timeout_seconds: int) -> None:
    deadline = time.time() + timeout_seconds
    while True:
        deployments = run_capture(
            [
                "kubectl",
                "get",
                "deployments",
                "-n",
                namespace,
                "-l",
                f"condition={condition_name}",
                "-o",
                "name",
            ],
            check=False,
        )
        service_pods = run_capture(
            [
                "kubectl",
                "get",
                "pods",
                "-n",
                namespace,
                "-l",
                f"condition={condition_name},workload-role=service",
                "-o",
                "name",
            ],
            check=False,
        )
        if not deployments.strip() and not service_pods.strip():
            return
        if time.time() >= deadline:
            raise StageFailure(f"Timed out waiting for {condition_name} resources to terminate")
        time.sleep(2)


def wait_for_pod_removed(namespace: str, pod_name: str, timeout_seconds: int) -> None:
    deadline = time.time() + timeout_seconds
    while True:
        result = subprocess.run(
            ["kubectl", "get", "pod", pod_name, "-n", namespace],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return
        if time.time() >= deadline:
            raise StageFailure(f"Timed out waiting for pod {pod_name} to terminate")
        time.sleep(2)


def copy_pod_results(namespace: str, source_path: str, destination_path: Path) -> None:
    if destination_path.exists():
        shutil.rmtree(destination_path)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    run(["kubectl", "cp", f"{namespace}/benchmark-client:{source_path}", str(destination_path)])


def merge_rolling_kind_results(partial_root: Path, merged_dir: Path, config_path: Path, conditions: list[str]) -> None:
    log(f"Merging rolling per-condition artifacts into {merged_dir}.")
    merged_dir.mkdir(parents=True, exist_ok=True)

    fieldnames: list[str] | None = None
    rows: list[dict[str, str]] = []
    local_validation: dict = {}
    grpc_validation: dict = {}
    warmup_calibration: dict = {}
    deployment_metadata: dict = {}
    environment: dict | None = None

    for condition in conditions:
        condition_dir = partial_root / condition
        if not condition_dir.is_dir():
            raise StageFailure(f"missing partial results directory: {condition_dir}")

        with (condition_dir / "raw_iterations.csv").open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if fieldnames is None:
                fieldnames = list(reader.fieldnames or [])
            elif list(reader.fieldnames or []) != fieldnames:
                raise StageFailure(f"raw_iterations.csv header mismatch for {condition}")
            rows.extend(list(reader))

        with (condition_dir / "parity_validation.json").open("r", encoding="utf-8") as handle:
            parity = json.load(handle)
        local_validation.update(parity.get("local_validation", {}))
        grpc_validation.update(parity.get("grpc_validation", {}))

        with (condition_dir / "warmup_calibration.json").open("r", encoding="utf-8") as handle:
            warmup_calibration.update(json.load(handle))

        with (condition_dir / "deployment_metadata.json").open("r", encoding="utf-8") as handle:
            deployment_metadata.update(json.load(handle))

        if environment is None:
            with (condition_dir / "environment.json").open("r", encoding="utf-8") as handle:
                environment = json.load(handle)

    if not rows or fieldnames is None:
        raise StageFailure("rolling merge failed: no raw iterations were collected")

    with (merged_dir / "raw_iterations.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    shutil.copy2(config_path, merged_dir / "config.yaml")
    environment = environment or {}
    environment["rolling_orchestration"] = {
        "enabled": True,
        "conditions": conditions,
        "partial_results_root": str(partial_root.resolve()),
    }

    for file_name, payload in {
        "environment.json": environment,
        "parity_validation.json": {
            "local_validation": local_validation,
            "grpc_validation": grpc_validation,
        },
        "warmup_calibration.json": warmup_calibration,
        "deployment_metadata.json": deployment_metadata,
    }.items():
        with (merged_dir / file_name).open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)


def run_kind_rolling_generated_stage(
    stage_name: str,
    namespace: str,
    experiment_config: Path,
    output_dir: Path,
    host_results_dir: Path,
) -> None:
    from src.benchmark.config import load_config

    config = load_config(str(experiment_config))
    conditions = list(config.conditions)
    if not conditions:
        raise StageFailure(f"{stage_name} config has no conditions")

    partial_root = host_results_dir / "partial_results"
    merged_dir = host_results_dir / "merged_results"
    pod_partial_root = f"/tmp/{stage_name}_rolling_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    timeout_seconds = int(float(config.kubernetes.readiness_timeout if config.kubernetes else 120.0))

    run(["kubectl", "delete", "pod", "benchmark-client", "-n", namespace, "--ignore-not-found=true"], check=False)

    for condition in conditions:
        condition_name = condition.name
        manifest_path = output_dir / f"{condition_name}.yaml"
        client_path = condition_client_manifest(output_dir, condition_name)
        pod_output_dir = f"{pod_partial_root}/{condition_name}"
        host_condition_dir = partial_root / condition_name

        log(f"Applying {condition_name}.")
        run(["kubectl", "apply", "-f", str(manifest_path)])
        expected_count = len(condition.chain_split_points or []) + 1
        wait_for_condition_ready(namespace, condition_name, expected_count, timeout_seconds)

        log(f"Applying client manifest for {condition_name}.")
        run(["kubectl", "apply", "-f", str(client_path)])
        log("Waiting for benchmark-client to be Ready.")
        run(
            [
                "kubectl",
                "wait",
                "--for=condition=Ready",
                "pod/benchmark-client",
                "-n",
                namespace,
                f"--timeout={timeout_seconds}s",
            ]
        )

        log(f"Running rolling benchmark for {condition_name}.")
        run(["kubectl", "exec", "-n", namespace, "benchmark-client", "--", "rm", "-rf", pod_output_dir], check=False)
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
                "--condition",
                condition_name,
                "--output-dir",
                pod_output_dir,
            ]
        )

        log(f"Copying rolling results for {condition_name} to {host_condition_dir}.")
        copy_pod_results(namespace, pod_output_dir, host_condition_dir)

        log(f"Deleting {condition_name} resources before the next rolling step.")
        run(["kubectl", "delete", "-f", str(manifest_path), "--ignore-not-found=true"], check=False)
        wait_for_condition_removed(namespace, condition_name, timeout_seconds + 60)
        run(["kubectl", "delete", "pod", "benchmark-client", "-n", namespace, "--ignore-not-found=true"], check=False)
        wait_for_pod_removed(namespace, "benchmark-client", timeout_seconds + 60)

    merge_rolling_kind_results(
        partial_root,
        merged_dir,
        experiment_config,
        [condition.name for condition in conditions],
    )
    log("Running host-side analysis on merged rolling results.")
    run([sys.executable, str(REPO_ROOT / "run_analysis.py"), str(merged_dir)])


def run_kind_stage(stage_name: str, args: argparse.Namespace) -> None:
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
    host_results_dir = REPO_ROOT / "results" / f"{stage_name}_{timestamp}"
    host_results_dir.mkdir(parents=True, exist_ok=True)

    try:
        log(f"Creating kind cluster {cluster_name} from {cluster_config.relative_to(REPO_ROOT)}.")
        run(["kind", "create", "cluster", "--name", cluster_name, "--config", str(cluster_config)])

        if stage_name == "rq1_4" and args.rq14_rolling:
            ensure_command("bash")
            log("Delegating RQ1.4 to the rolling fully controlled orchestrator.")
            command = [
                "bash",
                str(REPO_ROOT / "scripts" / "run_rq14_fully_controlled.sh"),
                "--rolling",
                "--cleanup-on-failure",
            ]
            if args.image_ref:
                command += ["--image-ref", args.image_ref]
            elif args.skip_image_build:
                command.append("--skip-image-build")
            run(command)
            return

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
                    "none",
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

        namespace_manifests = sorted(output_dir.glob("*namespace*.yaml"))
        if namespace_manifests:
            log("Applying namespace manifest(s) before workloads.")
            for namespace_manifest in namespace_manifests:
                run(["kubectl", "apply", "-f", str(namespace_manifest)])
            run(["kubectl", "get", "namespace", namespace])

        if stage_name == "rq1_4b":
            log("Running rq1_4b in rolling mode because multi-node placement is condition-specific.")
            run_kind_rolling_generated_stage(
                stage_name,
                namespace,
                experiment_config,
                output_dir,
                host_results_dir,
            )
            return

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
    "rq1_4": lambda args: run_kind_stage("rq1_4", args),
    "rq1_4b": lambda args: run_kind_stage("rq1_4b", args),
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

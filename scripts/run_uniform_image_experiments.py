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
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_IMAGE_TAG = "thesis-inference:latest"

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

OPTIONAL_STAGES: tuple[str, ...] = ()

ALL_STAGES = DEFAULT_STAGES + OPTIONAL_STAGES
CONTAINER_STAGES = {"rq1_4", "rq1_4b", "rq1_5", "rq1_5b", "rq2_1_paired", "rq2_1_mtls_split", "rq2_1_ablation", "rq2_2"}

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


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def utc_run_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S").lower()


def log(message: str) -> None:
    print(f"[{timestamp()}] {message}", flush=True)


def warn(message: str) -> None:
    print(f"[{timestamp()}] WARN: {message}", file=sys.stderr, flush=True)


def format_command(command: list[str]) -> str:
    return shlex.join(command)


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


def append_rq15_cloud_args(command: list[str], args: argparse.Namespace, acr_name: str) -> list[str]:
    command += ["--image-ref", args.image_ref, "--acr-name", acr_name]
    if args.provision_cloud:
        command.append("--provision")
    if args.destroy_cloud_on_success:
        command.append("--delete-resource-group-on-success")
    if args.destroy_cloud_on_failure:
        command.append("--delete-resource-group-on-failure")
    if args.cleanup_on_failure:
        command.append("--cleanup-on-failure")
    if args.rq15_nodepool:
        command += ["--nodepool", args.rq15_nodepool]
    return append_common_results_arg(command, args)


def append_rq2_cloud_args(
    command: list[str],
    args: argparse.Namespace,
    acr_name: str,
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
    return append_common_results_arg(command, args)


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
        command = ["bash", "scripts/run_rq14_fully_controlled.sh", "--image-ref", args.image_ref]
        if args.rq14_rolling:
            command.append("--rolling")
        if args.cleanup_on_failure:
            command.append("--cleanup-on-failure")
        return StagePlan(stage, [command])

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
        ]
        return StagePlan(stage, [append_rq15_cloud_args(command, args, acr_name)])

    if stage == "rq1_5b":
        command = python_script("scripts/run_rq15_fully_controlled.py") + [
            "--config",
            "configs/rq1/1.5/rq1_5b_multinode.yaml",
            "--resource-group",
            "rg-thesis-rq15b",
            "--cluster-name",
            "thesis-rq15b",
            "--nodepool",
            args.rq15b_nodepool,
            "--node-count",
            str(args.rq15b_node_count),
        ]
        return StagePlan(stage, [append_rq15_cloud_args(command, args, acr_name)])

    if stage == "rq2_1_paired":
        command = python_script("scripts/run_rq21_paired_benchmark.py")
        return StagePlan(
            stage,
            [append_rq2_cloud_args(command, args, acr_name, supports_cleanup=True, supports_smoke=True)],
        )

    if stage == "rq2_1_mtls_split":
        command = python_script("scripts/run_rq21_mtls_split.py")
        return StagePlan(
            stage,
            [append_rq2_cloud_args(command, args, acr_name, supports_cleanup=True, supports_smoke=True)],
        )

    if stage == "rq2_1_ablation":
        command = python_script("scripts/run_rq21_ablation.py")
        return StagePlan(
            stage,
            [append_rq2_cloud_args(command, args, acr_name, supports_cleanup=True, supports_smoke=True)],
        )

    if stage == "rq2_2":
        command = python_script("scripts/run_rq22_confidential.py")
        return StagePlan(
            stage,
            [append_rq2_cloud_args(command, args, acr_name, supports_cleanup=False, supports_smoke=False)],
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


def run_stage(plan: StagePlan, *, dry_run: bool) -> StageResult:
    started = time.time()
    try:
        for command in plan.commands:
            run_command(command, dry_run=dry_run)
    except Exception as exc:
        return StageResult(plan.name, "fail", time.time() - started, str(exc))
    return StageResult(plan.name, "dry-run" if dry_run else "ok", time.time() - started)


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
        help="Backward-compatible no-op; all thesis stages run by default.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")
    parser.add_argument("--continue-on-failure", action="store_true", help="Continue after a stage fails.")
    parser.add_argument(
        "--skip-acr-login",
        action="store_true",
        help="Do not run 'az acr login' before container-based stages.",
    )
    parser.add_argument(
        "--provision-cloud",
        action="store_true",
        help="Pass the cloud provisioning flag to AKS-backed stages.",
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
    parser.add_argument("--results-root", default=None, help="Results root passed to runners that support it.")
    parser.add_argument("--rq14-rolling", action="store_true", help="Run RQ1.4 one condition at a time.")
    parser.add_argument("--rq15-nodepool", default=None, help="Override RQ1.5 nodepool.")
    parser.add_argument("--rq15b-nodepool", default="rq15bpool", help="RQ1.5b nodepool label.")
    parser.add_argument("--rq15b-node-count", type=int, default=6, help="RQ1.5b node count.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stages = resolve_stages(args)
    log(f"Stages: {', '.join(stages)}")
    if args.dry_run:
        log("Dry run: no commands will be executed.")

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

    results: list[StageResult] = []
    if CONTAINER_STAGES.intersection(stages) and not args.skip_acr_login and not args.build_push_image:
        login_plan = StagePlan("acr_login", [["az", "acr", "login", "--name", acr_name]])
        login_result = run_stage(login_plan, dry_run=args.dry_run)
        results.append(login_result)
        if login_result.status == "fail" and not args.continue_on_failure:
            plans = []

    for plan in plans:
        log("=" * 72)
        log(f"Stage: {plan.name}")
        log("=" * 72)
        result = run_stage(plan, dry_run=args.dry_run)
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
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

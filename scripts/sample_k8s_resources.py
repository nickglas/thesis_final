from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


class SamplerError(RuntimeError):
    pass


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_kubectl() -> None:
    if shutil.which("kubectl") is None:
        raise SamplerError("kubectl was not found on PATH")


def run_kubectl_top(namespace: str | None, all_namespaces: bool) -> str:
    args = ["kubectl", "top", "pod", "--containers", "--no-headers"]
    if all_namespaces:
        args.append("--all-namespaces")
    elif namespace:
        args.extend(["-n", namespace])
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise SamplerError(
            "Unable to collect container resource metrics with kubectl top. "
            "Confirm metrics-server is installed and ready. "
            f"kubectl output: {detail or result.returncode}"
        )
    return result.stdout


def parse_top_output(text: str, namespace: str | None, all_namespaces: bool) -> list[dict[str, str]]:
    rows = []
    captured_at = utc_timestamp()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if all_namespaces:
            if len(parts) < 5:
                continue
            row_namespace, pod_name, container_name, cpu, memory = parts[:5]
        else:
            if len(parts) < 4:
                continue
            pod_name, container_name, cpu, memory = parts[:4]
            row_namespace = namespace or "default"
        rows.append({
            "timestamp": captured_at,
            "namespace": row_namespace,
            "pod_name": pod_name,
            "container_name": container_name,
            "container_role": "istio-proxy" if container_name == "istio-proxy" else "app",
            "cpu_usage": cpu,
            "memory_usage": memory,
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "timestamp",
        "namespace",
        "pod_name",
        "container_name",
        "container_role",
        "cpu_usage",
        "memory_usage",
    ]
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


def emit_rows(rows: list[dict[str, str]], output_format: str, output_path: str | None) -> None:
    if output_path:
        write_csv(Path(output_path), rows)
        return
    if output_format == "json":
        print(json.dumps(rows, indent=2))
        return
    writer = csv.DictWriter(
        sys.stdout,
        fieldnames=[
            "timestamp",
            "namespace",
            "pod_name",
            "container_name",
            "container_role",
            "cpu_usage",
            "memory_usage",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sample Kubernetes container CPU/memory usage via kubectl top pod --containers"
    )
    parser.add_argument("-n", "--namespace", default=None, help="Namespace to sample")
    parser.add_argument(
        "--all-namespaces",
        action="store_true",
        help="Sample pods across all namespaces",
    )
    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=0,
        help="Repeat interval. Use 0 for a single sample.",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=1,
        help="Number of samples to collect. Use a positive integer.",
    )
    parser.add_argument(
        "--output-format",
        choices=["csv", "json"],
        default="csv",
        help="Stdout format when --output is not provided.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="CSV file path to append samples to.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.samples < 1:
        print("--samples must be at least 1", file=sys.stderr)
        return 2
    if args.all_namespaces and args.namespace:
        print("Use either --namespace or --all-namespaces, not both", file=sys.stderr)
        return 2

    try:
        ensure_kubectl()
        collected: list[dict[str, str]] = []
        for sample_index in range(args.samples):
            text = run_kubectl_top(args.namespace, args.all_namespaces)
            rows = parse_top_output(text, args.namespace, args.all_namespaces)
            if args.output:
                emit_rows(rows, args.output_format, args.output)
            else:
                collected.extend(rows)
            if sample_index < args.samples - 1:
                time.sleep(args.interval_seconds)
        if not args.output:
            emit_rows(collected, args.output_format, None)
    except SamplerError as exc:
        print(f"Resource sampling unavailable: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

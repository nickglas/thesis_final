"""Kubernetes benchmark runner for RQ1.4 chain experiments.

Assumes services are already deployed to the cluster and reachable via
standard Kubernetes DNS. The runner performs:

  For each round r in 1..R:
      Generate condition-order permutation
      For each condition c:
          Resolve all service addresses for the condition
          Wait for gRPC readiness on each client-visible service
          (strict mTLS/AuthZ conditions may intentionally block direct probes
          to protected downstream services)
          Run live chain parity validation (round 1 only)
          Run warmup with calibration check
          Run M measured iterations (recorded)
          Cooldown pause

Service deployment/teardown is handled externally (by the experiment
entrypoint or operator scripts), not by this runner.
"""

import os
import json
import time
import random
import logging
import subprocess
from typing import Optional

import grpc
import torch
import yaml
import numpy as np
from datetime import datetime

from src.benchmark.config import (
    ExperimentConfig,
    K8sConfig,
    format_k8s_service_name,
)
from src.benchmark.cpu_stabilisation import apply_cpu_stabilisation
from src.benchmark.deployment_metadata import build_environment_deployment_section
from src.benchmark.logging import ArtifactLogger
from src.benchmark.warmup import run_warmup_calibrated
from src.client.chain_client import ChainClient
from src.grpc_target import resolve_target_address
from src.models.resnet_splits import get_full_model, get_chain_segments

logger = logging.getLogger(__name__)

# Maximum hop columns in the CSV (chain_5svc = 5 services)
MAX_HOPS = 5
RUNTIME_METADATA_PATH = "/tmp/k8s_runtime_metadata.json"


def _read_json_file(path: str) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return None


def _read_yaml_file(path: str) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle)
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def _container_resource_snapshot(container: dict) -> dict:
    resources = container.get("resources", {})
    return {
        "requests": resources.get("requests", {}) or {},
        "limits": resources.get("limits", {}) or {},
    }


def _service_record_from_runtime(record: dict, default_address: str) -> dict:
    return {
        "service_name": record.get("service_name", "unknown"),
        "address": record.get("address") or default_address,
        "segment_index": str(record.get("segment_index", "unknown")),
        "pod_name": record.get("pod_name") or "unknown",
        "node_name": record.get("node_name") or "unknown",
        "pod_ip": record.get("pod_ip") or "unknown",
        "image": record.get("image") or "unknown",
        "image_id": record.get("image_id") or "unknown",
        "image_pull_policy": record.get("image_pull_policy") or "unknown",
        "qos_class": record.get("qos_class") or "unknown",
        "resources": record.get("resources") or {"requests": {}, "limits": {}},
        "service_account_name": record.get("service_account_name") or "unknown",
        "containers": record.get("containers") or [],
        "sidecar_present": bool(record.get("sidecar_present", False)),
        "sidecars": record.get("sidecars") or [],
        "sidecar_image_ids": record.get("sidecar_image_ids") or [],
        "labels": record.get("labels") or {},
        "annotations": record.get("annotations") or {},
    }


def _resolve_cluster_identity(runtime_meta: Optional[dict]) -> dict:
    cluster_context = os.environ.get("KUBE_CLUSTER_CONTEXT", "").strip()
    cluster_info = os.environ.get("KUBE_CLUSTER_INFO", "").strip()

    if runtime_meta:
        cluster_context = runtime_meta.get("cluster_context") or cluster_context
        cluster_info = runtime_meta.get("cluster_info") or cluster_info

    if not cluster_context:
        try:
            cluster_context = subprocess.check_output(
                ["kubectl", "config", "current-context"],
                stderr=subprocess.DEVNULL, timeout=5,
            ).decode().strip()
        except Exception:
            cluster_context = "unknown"

    if not cluster_info:
        k8s_host = os.environ.get("KUBERNETES_SERVICE_HOST", "")
        k8s_port = os.environ.get("KUBERNETES_SERVICE_PORT", "")
        if k8s_host:
            cluster_info = (
                f"https://{k8s_host}:{k8s_port}" if k8s_port else f"https://{k8s_host}"
            )
        else:
            try:
                info = subprocess.check_output(
                    ["kubectl", "cluster-info"],
                    stderr=subprocess.DEVNULL, timeout=5,
                ).decode().strip()
                cluster_info = info.split("\n")[0] if info else "unknown"
            except Exception:
                cluster_info = "unknown"

    return {
        "cluster_context": cluster_context,
        "cluster_info": cluster_info,
    }


def _resolve_client_metadata(k8s_cfg: K8sConfig, runtime_meta: Optional[dict]) -> dict:
    client_meta = {
        "pod_name": os.environ.get("MY_POD_NAME", "").strip() or "unknown",
        "node_name": os.environ.get("MY_NODE_NAME", "").strip() or "unknown",
        "pod_ip": os.environ.get("MY_POD_IP", "").strip() or "unknown",
        "image": k8s_cfg.image,
        "image_id": "unknown",
        "image_pull_policy": k8s_cfg.image_pull_policy,
        "qos_class": "unknown",
        "resources": {
            "requests": {
                "cpu": k8s_cfg.client_resources.cpu_request,
                "memory": k8s_cfg.client_resources.memory_request,
            },
            "limits": {
                "cpu": k8s_cfg.client_resources.cpu_limit,
                "memory": k8s_cfg.client_resources.memory_limit,
            },
        },
    }

    if runtime_meta and isinstance(runtime_meta.get("client"), dict):
        observed = runtime_meta["client"]
        client_meta.update({
            "pod_name": observed.get("pod_name") or client_meta["pod_name"],
            "node_name": observed.get("node_name") or client_meta["node_name"],
            "pod_ip": observed.get("pod_ip") or client_meta["pod_ip"],
            "image": observed.get("image") or client_meta["image"],
            "image_id": observed.get("image_id") or client_meta["image_id"],
            "image_pull_policy": observed.get("image_pull_policy") or client_meta["image_pull_policy"],
            "qos_class": observed.get("qos_class") or client_meta["qos_class"],
            "resources": observed.get("resources") or client_meta["resources"],
            "service_account_name": observed.get("service_account_name") or "unknown",
            "containers": observed.get("containers") or [],
            "sidecar_present": bool(observed.get("sidecar_present", False)),
            "sidecars": observed.get("sidecars") or [],
            "sidecar_image_ids": observed.get("sidecar_image_ids") or [],
            "labels": observed.get("labels") or {},
            "annotations": observed.get("annotations") or {},
        })

    return client_meta


def _flatten_chain_metrics(metrics: dict) -> dict:
    """Flatten chain client metrics into the RQ1.4 CSV schema.

    Converts the nested hop_timings list into flat hop_N_* columns,
    zero-filling unused hop slots up to MAX_HOPS.
    """
    flat = {
        "end_to_end_ms": metrics["end_to_end_ms"],
        "total_compute_ms": metrics["total_compute_ms"],
        "non_compute_overhead_ms": metrics["non_compute_overhead_ms"],
        "total_activation_bytes": metrics["total_activation_bytes"],
        "num_hops": metrics["num_hops"],
    }

    for i in range(1, MAX_HOPS + 1):
        hop = None
        for h in metrics["hop_timings"]:
            if h["hop_index"] == i:
                hop = h
                break
        flat[f"hop_{i}_compute_ms"] = hop["compute_ms"] if hop else 0.0
        flat[f"hop_{i}_deserialize_ms"] = hop["deserialize_ms"] if hop else 0.0
        flat[f"hop_{i}_serialize_ms"] = hop["serialize_ms"] if hop else 0.0
        flat[f"hop_{i}_forward_ms"] = hop["forward_ms"] if hop else 0.0
        flat[f"hop_{i}_activation_bytes"] = hop["activation_bytes"] if hop else 0

    return flat


def resolve_all_service_addresses(cond, k8s_cfg: K8sConfig) -> list:
    """Resolve DNS addresses for every service in a chain condition.

    Returns a list of (service_name, address) tuples ordered by segment index.
    For monolithic_k8s_1svc: 1 service.  For chain_Nsvc: N services.
    """
    split_points = cond.chain_split_points or []
    n_services = len(split_points) + 1

    addresses = []
    for idx in range(1, n_services + 1):
        svc_name = format_k8s_service_name(
            k8s_cfg.service_name_template,
            cond.name,
            idx,
        )
        address = (
            f"{svc_name}.{k8s_cfg.namespace}"
            f".svc.cluster.local:{k8s_cfg.grpc_port}"
        )
        addresses.append((svc_name, address))
    return addresses


def wait_for_all_services(addresses: list, timeout: float = 60.0):
    """Block until every service in the chain is gRPC-ready.

    Parameters
    ----------
    addresses : list of (service_name, address) tuples
    timeout : float
        Per-service timeout in seconds.

    Raises RuntimeError if any service fails to become ready.
    """
    for svc_name, address in addresses:
        logger.info(f"      Waiting for {svc_name} at {address}...")
        resolved_address = resolve_target_address(address)
        if resolved_address != address:
            logger.info(f"      {svc_name} resolved to {resolved_address}")
        channel = grpc.insecure_channel(resolved_address)
        try:
            grpc.channel_ready_future(channel).result(timeout=timeout)
            logger.info(f"      {svc_name} READY")
        except grpc.FutureTimeoutError:
            raise RuntimeError(
                f"gRPC service {svc_name} not ready after {timeout}s "
                f"at {address}"
            )
        finally:
            channel.close()


def collect_k8s_metadata(cond, k8s_cfg: K8sConfig,
                         service_addresses: list) -> dict:
    """Collect Kubernetes deployment metadata for a condition.

    Gathers pod names, node placement, and cluster context where available.
    Failures are non-fatal — returns best-effort metadata.

    Priority for each field:
      1. Injected JSON file written by the host script before this run
         (``/tmp/rq14_pod_metadata_{cond.name}.json``)
      2. Environment variables injected via the Downward API / pod spec
      3. kubectl subprocess call (works only if kubectl is installed in
         the container image — typically not the case)
    """
    meta = {
        "namespace": k8s_cfg.namespace,
        "condition": cond.name,
        "num_services": len(service_addresses),
        "split_points": cond.chain_split_points or [],
        "services": [],
        "declared_kubernetes_config": {
            "image": k8s_cfg.image,
            "image_pull_policy": k8s_cfg.image_pull_policy,
            "service_resources": {
                "requests": {
                    "cpu": k8s_cfg.resources.cpu_request,
                    "memory": k8s_cfg.resources.memory_request,
                },
                "limits": {
                    "cpu": k8s_cfg.resources.cpu_limit,
                    "memory": k8s_cfg.resources.memory_limit,
                },
            },
            "client_resources": {
                "requests": {
                    "cpu": k8s_cfg.client_resources.cpu_request,
                    "memory": k8s_cfg.client_resources.memory_request,
                },
                "limits": {
                    "cpu": k8s_cfg.client_resources.cpu_limit,
                    "memory": k8s_cfg.client_resources.memory_limit,
                },
            },
        },
    }

    runtime_meta = _read_json_file(RUNTIME_METADATA_PATH)
    meta.update(_resolve_cluster_identity(runtime_meta))
    meta["cluster_deployment"] = (
        runtime_meta.get("cluster_deployment") if runtime_meta else {}
    ) or {}
    meta["namespaces"] = (
        runtime_meta.get("namespaces") if runtime_meta else {}
    ) or {}
    meta["mesh"] = (
        runtime_meta.get("mesh") if runtime_meta else {}
    ) or {}
    meta["client"] = _resolve_client_metadata(k8s_cfg, runtime_meta)

    # --- Load service pod details from the injected metadata file ---
    # The host script (run_rq14_fully_controlled.sh) writes this file into
    # the pod before the benchmark starts.  Each entry maps segment_index
    # to its pod/node identity.
    injected_meta_path = f"/tmp/rq14_pod_metadata_{cond.name}.json"
    injected_pods: dict = {}  # segment_index (str) -> record dict
    try:
        with open(injected_meta_path, "r", encoding="utf-8") as fh:
            pod_records = json.load(fh)
        for record in pod_records:
            seg = str(record.get("segment_index", ""))
            if seg:
                injected_pods[seg] = record
    except Exception:
        pass  # file absent or malformed — will fall back to kubectl

    runtime_services = {}
    if runtime_meta:
        for record in runtime_meta.get("conditions", {}).get(cond.name, []):
            seg = str(record.get("segment_index", ""))
            if seg:
                runtime_services[seg] = record

    # --- Per-service pod details ---
    # Pod labels use the raw condition name (label values allow underscores).
    condition_label = cond.name
    for svc_name, address in service_addresses:
        try:
            seg_idx = svc_name.rsplit("-", 1)[-1]
        except Exception:
            seg_idx = ""

        svc_meta = {
            "service_name": svc_name,
            "address": address,
            "segment_index": seg_idx or "unknown",
            "pod_name": "unknown",
            "node_name": "unknown",
            "pod_ip": "unknown",
            "image": k8s_cfg.image,
            "image_id": "unknown",
            "image_pull_policy": k8s_cfg.image_pull_policy,
            "qos_class": "unknown",
            "resources": {
                "requests": {
                    "cpu": k8s_cfg.resources.cpu_request,
                    "memory": k8s_cfg.resources.memory_request,
                },
                "limits": {
                    "cpu": k8s_cfg.resources.cpu_limit,
                    "memory": k8s_cfg.resources.memory_limit,
                },
            },
        }

        # 1. Preferred: unified runtime metadata injected by the host script.
        if seg_idx and seg_idx in runtime_services:
            svc_meta.update(_service_record_from_runtime(runtime_services[seg_idx], address))
        # 2. Legacy per-condition metadata injection.
        elif seg_idx and seg_idx in injected_pods:
            record = injected_pods[seg_idx]
            svc_meta["pod_name"] = record.get("pod_name") or "unknown"
            svc_meta["node_name"] = record.get("node_name") or "unknown"
            svc_meta["pod_ip"] = record.get("pod_ip") or "unknown"
        elif seg_idx:
            # 3. Fallback: kubectl (uses raw label values; works when kubectl is present in the image)
            try:
                raw = subprocess.check_output(
                    [
                        "kubectl", "get", "pods",
                        "-n", k8s_cfg.namespace,
                        "-l", f"condition={condition_label},segment-index={seg_idx}",
                        "-o", "json",
                    ],
                    stderr=subprocess.DEVNULL, timeout=10,
                ).decode().strip()
                payload = json.loads(raw)
                items = payload.get("items", [])
                if items:
                    item = items[0]
                    svc_meta["pod_name"] = item.get("metadata", {}).get("name", "unknown")
                    svc_meta["node_name"] = item.get("spec", {}).get("nodeName", "unknown")
                    svc_meta["pod_ip"] = item.get("status", {}).get("podIP", "unknown")
                    container = (item.get("spec", {}).get("containers") or [{}])[0]
                    status = (item.get("status", {}).get("containerStatuses") or [{}])[0]
                    svc_meta["image"] = container.get("image", svc_meta["image"])
                    svc_meta["image_id"] = status.get("imageID", svc_meta["image_id"])
                    svc_meta["image_pull_policy"] = container.get("imagePullPolicy", svc_meta["image_pull_policy"])
                    svc_meta["qos_class"] = item.get("status", {}).get("qosClass", svc_meta["qos_class"])
                    svc_meta["resources"] = _container_resource_snapshot(container)
            except Exception:
                pass

        meta["services"].append(svc_meta)

    observed_images = sorted({svc.get("image", "unknown") for svc in meta["services"]})
    observed_policies = sorted({svc.get("image_pull_policy", "unknown") for svc in meta["services"]})
    service_resource_signatures = sorted({
        json.dumps(svc.get("resources", {}), sort_keys=True)
        for svc in meta["services"]
    })
    meta["observed_deployment_profile"] = {
        "service_images": observed_images,
        "service_image_pull_policies": observed_policies,
        "service_resources_uniform": len(service_resource_signatures) == 1,
        "service_resources": json.loads(service_resource_signatures[0]) if service_resource_signatures else {},
        "client": meta["client"],
    }

    meta["collected_at"] = datetime.now().isoformat()
    return meta


class K8sBenchmarkRunner:
    """Benchmark runner for RQ1.4 chain experiments on Kubernetes.

    Parameters
    ----------
    config : ExperimentConfig
        Full experiment configuration (must include kubernetes section).
    config_path : str
        Path to the YAML config file (copied to output).
    output_dir : str, optional
        Override output directory. Auto-generated if None.
    """

    def __init__(self, config: ExperimentConfig, config_path: str,
                 output_dir: str = None):
        self.config = config
        self.config_path = config_path
        self.raw_config = _read_yaml_file(config_path) or {}

        if config.kubernetes is None:
            raise ValueError(
                "K8sBenchmarkRunner requires a 'kubernetes' section in config"
            )
        self.k8s_cfg = config.kubernetes

        if output_dir is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = config.experiment_name.split()[0].lower().replace(".", "_")
            output_dir = os.path.join("results", f"{prefix}_{ts}")
        self.output_dir = output_dir
        self.artifact_logger = ArtifactLogger(output_dir)

        # Fixed deterministic input tensor
        torch.manual_seed(config.seed)
        self.input_tensor = torch.randn(*config.input_shape)

        self.all_rows = []
        self.parity_local_results = {}
        self._parity_grpc_results = {}
        self._warmup_calibrations = {}
        self._deployment_metadata = {}

    def run(self):
        """Execute the full benchmark and save raw artifacts."""
        logger.info("=" * 60)
        logger.info("%s K8s Benchmark — Starting", self.config.experiment_name)
        logger.info("=" * 60)

        # Apply CPU-behaviour stabilisation before any measurement
        self.stabilisation_meta = apply_cpu_stabilisation(
            self.config.cpu_stabilisation,
        )

        self.artifact_logger.save_config_copy(self.config_path)
        self.artifact_logger.save_resolved_config(self.config, self.config_path)
        self.artifact_logger.save_environment(self.stabilisation_meta)

        cfg = self.config
        completed = False

        try:
            for round_num in range(1, cfg.rounds + 1):
                rng = random.Random(cfg.seed + round_num)
                order = list(range(len(cfg.conditions)))
                rng.shuffle(order)

                names = [cfg.conditions[i].name for i in order]
                logger.info(f"Round {round_num}/{cfg.rounds} — order: {names}")

                for idx in order:
                    cond = cfg.conditions[idx]
                    logger.info(f"  Condition: {cond.name}")
                    self._run_chain_condition(round_num, cond)

                    logger.info(f"  Cooldown: {cfg.cooldown_seconds}s")
                    time.sleep(cfg.cooldown_seconds)

            completed = True
        finally:
            self._persist_artifacts()
            if completed:
                logger.info(
                    f"Benchmark complete. {len(self.all_rows)} iterations recorded."
                )
            else:
                logger.warning(
                    "Benchmark interrupted after %s iterations. Partial artifacts saved.",
                    len(self.all_rows),
                )
            logger.info(f"Results directory: {self.output_dir}")

    def _persist_artifacts(self):
        self.artifact_logger.save_raw_iterations(self.all_rows)
        self.artifact_logger.save_json("parity_validation.json", {
            "local_validation": self.parity_local_results,
            "grpc_validation": self._parity_grpc_results,
        })
        self.artifact_logger.save_json(
            "warmup_calibration.json", self._warmup_calibrations
        )
        self.artifact_logger.save_json(
            "deployment_metadata.json", self._deployment_metadata
        )
        deployment_section = build_environment_deployment_section(
            self._deployment_metadata
        )
        if deployment_section:
            self.artifact_logger.update_environment({"deployment": deployment_section})

    def _run_chain_condition(self, round_num: int, cond):
        """Run one chain condition (including monolithic_k8s_1svc)."""
        cfg = self.config
        k8s = self.k8s_cfg

        # Resolve ALL service addresses for the chain
        service_addresses = resolve_all_service_addresses(cond, k8s)
        first_svc_name, first_address = service_addresses[0]

        logger.info(
            f"    Chain: {len(service_addresses)} services, "
            f"first={first_svc_name}"
        )
        for svc_name, addr in service_addresses:
            logger.info(f"      {svc_name} -> {addr}")

        readiness_addresses = self._client_visible_readiness_addresses(
            cond, service_addresses
        )
        if len(readiness_addresses) == len(service_addresses):
            logger.info("    Checking full-chain readiness...")
        else:
            skipped = [svc_name for svc_name, _ in service_addresses[len(readiness_addresses):]]
            logger.info(
                "    Checking client-visible readiness only; downstream direct "
                "readiness probes are intentionally blocked by RQ2.1 mTLS/authz: %s",
                skipped,
            )
        wait_for_all_services(readiness_addresses, timeout=k8s.readiness_timeout)
        logger.info("    Client-visible services ready")

        # Collect deployment metadata (once per condition, round 1)
        if round_num == 1:
            meta = collect_k8s_metadata(cond, k8s, service_addresses)
            self._deployment_metadata[cond.name] = meta
            logger.info(f"    Deployment metadata captured")

        client = ChainClient(first_address, k8s.max_message_bytes)
        try:
            # Live chain parity validation (round 1 only)
            if round_num == 1:
                self._validate_chain_parity(client, cond)

            # Warmup
            cal_key = f"{cond.name}_round{round_num}"
            cal = run_warmup_calibrated(
                infer_fn=client.warmup_infer,
                input_tensor=self.input_tensor,
                n=cfg.warmup_iterations,
                window=cfg.warmup_calibration_window,
                cv_threshold=cfg.warmup_calibration_cv_threshold,
                max_extra_iterations=cfg.warmup_calibration_max_extra_iterations,
            )
            self._warmup_calibrations[cal_key] = cal
            logger.info(
                f"    Warmup: {cal['total_iterations']} iterations, "
                f"stabilised_once={cal['stabilised_once']}, "
                f"first_stabilised_at={cal['first_stabilised_at_iteration']}, "
                f"final_window_stabilised={cal['final_window_stabilised']}"
            )

            # Measured iterations
            logger.info(f"    Measuring: {cfg.measured_iterations} iterations")
            for i in range(cfg.measured_iterations):
                metrics = client.infer(self.input_tensor)
                flat = _flatten_chain_metrics(metrics)
                row = {
                    "round": round_num,
                    "condition": cond.name,
                    "iteration": i + 1,
                    **flat,
                }
                self.all_rows.append(row)
                self.artifact_logger.append_raw_iterations([row])
        finally:
            client.close()

    def _client_visible_readiness_addresses(self, cond, service_addresses: list) -> list:
        """Return service addresses the benchmark client is allowed to probe.

        RQ2.1 mTLS/AuthZ configurations intentionally deny direct client
        access to protected downstream services. The benchmark still calls
        service1 and exercises the full service1->... chain; only the readiness
        gate is narrowed so the runner does not fail on the intended denial path.
        """
        raw_k8s = self.raw_config.get("kubernetes") or {}
        if not isinstance(raw_k8s, dict):
            return service_addresses

        mesh = raw_k8s.get("mesh") or {}
        mesh_enabled = bool(mesh.get("enabled", False))
        if not mesh_enabled or cond.type != "chain":
            return service_addresses

        blocked_segments = []
        peer = mesh.get("peer_authentication") or {}
        for workload in peer.get("strict_workloads") or []:
            if not isinstance(workload, dict):
                continue
            mode = str(workload.get("mode") or "STRICT").upper()
            if mode != "STRICT":
                continue
            try:
                blocked_segments.append(int(workload.get("segment_index") or 0))
            except (TypeError, ValueError):
                continue

        authz = mesh.get("authorization_policy") or {}
        if isinstance(authz, dict) and bool(authz.get("enabled", False)):
            policies = authz.get("policies")
            policy_items = policies if isinstance(policies, list) and policies else [authz]
            for policy in policy_items:
                if not isinstance(policy, dict):
                    continue
                try:
                    blocked_segments.append(int(policy.get("downstream_segment_index") or 2))
                except (TypeError, ValueError):
                    blocked_segments.append(2)

        blocked_downstream_segments = [
            segment for segment in blocked_segments
            if segment > 1 and segment <= len(service_addresses)
        ]
        if not blocked_downstream_segments:
            return service_addresses
        first_blocked_segment = min(blocked_downstream_segments)
        return service_addresses[: max(1, first_blocked_segment - 1)]

    def _validate_chain_parity(self, client: ChainClient, cond):
        """Live chain parity validation: send test inputs through the deployed
        chain and compare output to local monolithic model. Fail-closed."""
        cfg = self.config
        logger.info(
            f"    Chain parity validation: atol={cfg.parity_atol}, "
            f"inputs={cfg.parity_num_inputs}"
        )

        rng = np.random.RandomState(cfg.seed)
        model = get_full_model()

        all_match = True
        max_diff = 0.0

        for _ in range(cfg.parity_num_inputs):
            inp = torch.from_numpy(
                rng.randn(1, 3, 224, 224).astype(np.float32)
            )
            with torch.no_grad():
                mono_out = model(inp)

            chain_out = _infer_and_get_tensor(client, inp)
            diff = (mono_out - chain_out).abs().max().item()
            max_diff = max(max_diff, diff)
            if diff > cfg.parity_atol:
                all_match = False

        result = {
            "match": all_match,
            "max_abs_diff": max_diff,
            "atol": cfg.parity_atol,
            "num_inputs": cfg.parity_num_inputs,
            "method": "live_chain_grpc",
        }
        self._parity_grpc_results[cond.name] = result

        status = "PASS" if all_match else "FAIL"
        logger.info(f"    Chain parity: {status} (max_abs_diff={max_diff:.2e})")

        if not all_match:
            raise RuntimeError(
                f"Chain parity validation FAILED for {cond.name}. "
                f"max_abs_diff={max_diff:.2e} > atol={cfg.parity_atol}. "
                f"Benchmark aborted."
            )


def _infer_and_get_tensor(client: ChainClient,
                          input_tensor: torch.Tensor) -> torch.Tensor:
    """Run chain inference and return the output tensor."""
    response = client.infer_response(input_tensor)
    out_arr = np.frombuffer(response.tensor_data, dtype=np.float32).copy()
    return torch.from_numpy(out_arr.reshape(list(response.shape)))

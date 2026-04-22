#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd -P)"

CONFIG_REL="configs/rq1/1.5/rq1_5_full.yaml"
CONFIG_PATH="${REPO_ROOT}/${CONFIG_REL}"
CLIENT_POD_NAME="benchmark-client"
GENERATED_DIR="${REPO_ROOT}/k8s/aks/generated"

RUN_TS="$(date -u +%Y%m%d_%H%M%S)"
HOST_EXPORT_DIR="${REPO_ROOT}/results_exports/rq1_5_fully_controlled_${RUN_TS}"
DIAGNOSTICS_DIR="${HOST_EXPORT_DIR}/diagnostics"
HOST_PARTIAL_RESULTS_DIR="${HOST_EXPORT_DIR}/partial_results"
HOST_BENCHMARK_LOG_DIR="${HOST_EXPORT_DIR}/condition_logs"
MERGED_RESULTS_DIR="${HOST_EXPORT_DIR}/merged_results"
POD_PARTIAL_RESULTS_ROOT="/tmp/rq15_rolling_${RUN_TS}"

PYTHON_BIN=""
KUBE_CONTEXT=""
KUBE_CLUSTER_INFO=""
NAMESPACE=""
READINESS_TIMEOUT=""
READINESS_TIMEOUT_SECONDS=""
FINAL_RESULTS_DIR=""

NODEPOOL="rq15pool"
CLEANUP_ON_FAILURE=0
RESOURCES_DEPLOYED=0

CONDITION_MANIFESTS=()

readonly REQUIRED_FILES=(
  "run_k8s_experiment.py"
  "run_analysis.py"
  "scripts/inject_k8s_runtime_metadata.py"
  "scripts/preflight_rq15_full.py"
  "k8s/aks/generate_aks_manifests.py"
  "${CONFIG_REL}"
)

usage() {
  cat <<EOF
Usage: bash scripts/run_rq15_fully_controlled.sh [options]

Runs the thesis-facing RQ1.5 AKS benchmark in rolling mode:
deploy one condition, benchmark it, tear it down, then continue.

Options:
  --cleanup-on-failure  Tear down the rq15 namespace if the run fails.
  --nodepool NAME       AKS nodepool label to preflight against (default: rq15pool).
  -h, --help            Show this help text.
EOF
}

timestamp() {
  date '+%Y-%m-%d %H:%M:%S'
}

log() {
  printf '[%s] %s\n' "$(timestamp)" "$*"
}

warn() {
  printf '[%s] WARN: %s\n' "$(timestamp)" "$*" >&2
}

error() {
  printf '[%s] ERROR: %s\n' "$(timestamp)" "$*" >&2
}

die() {
  error "$*"
  exit 1
}

on_exit() {
  local exit_code=$?

  if (( exit_code != 0 )); then
    if (( RESOURCES_DEPLOYED )); then
      gather_diagnostics || true
      if (( CLEANUP_ON_FAILURE )); then
        log "Cleanup-on-failure enabled; tearing down namespace ${NAMESPACE}."
        cleanup_cluster || true
      else
        warn "Preserving namespace ${NAMESPACE} for inspection."
      fi
    fi
    warn "Run failed. Host artifacts directory: ${HOST_EXPORT_DIR}"
  fi
}

trap on_exit EXIT

parse_args() {
  while (( $# > 0 )); do
    case "$1" in
      --cleanup-on-failure)
        CLEANUP_ON_FAILURE=1
        ;;
      --nodepool)
        shift
        [[ $# -gt 0 ]] || die "--nodepool requires a value"
        NODEPOOL="$1"
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        die "Unknown argument: $1"
        ;;
    esac
    shift
  done
}

ensure_command() {
  local command_name="$1"
  command -v "${command_name}" >/dev/null 2>&1 || die "Required command not found: ${command_name}"
}

python_has_modules() {
  local python_cmd="$1"
  shift

  "${python_cmd}" - "$@" <<'PY' >/dev/null 2>&1
import importlib
import sys

for module_name in sys.argv[1:]:
    importlib.import_module(module_name)
PY
}

find_python() {
  local candidate
  local candidates=()

  if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python" ]]; then
    candidates+=("${VIRTUAL_ENV}/bin/python")
  fi

  if [[ -x "${REPO_ROOT}/.venv/bin/python" ]]; then
    candidates+=("${REPO_ROOT}/.venv/bin/python")
  fi

  for candidate in python3 python; do
    if command -v "${candidate}" >/dev/null 2>&1; then
      candidates+=("${candidate}")
    fi
  done

  for candidate in "${candidates[@]}"; do
    if python_has_modules "${candidate}" yaml; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done

  return 1
}

python_yaml_get() {
  local config_file="$1"
  local dotted_path="$2"
  "${PYTHON_BIN}" - "${config_file}" "${dotted_path}" <<'PY'
import sys
import yaml

config_path, dotted_path = sys.argv[1:]

with open(config_path, "r", encoding="utf-8") as handle:
    data = yaml.safe_load(handle)

value = data
for part in dotted_path.split("."):
    if isinstance(value, list):
        value = value[int(part)]
    else:
        value = value[part]

if isinstance(value, bool):
    print("true" if value else "false")
else:
    print(value)
PY
}

python_config_get() {
  local dotted_path="$1"
  python_yaml_get "${CONFIG_PATH}" "${dotted_path}"
}

verify_required_files() {
  local relative_path
  for relative_path in "${REQUIRED_FILES[@]}"; do
    [[ -f "${REPO_ROOT}/${relative_path}" ]] || die "Required file is missing: ${relative_path}"
  done
}

verify_python_support() {
  "${PYTHON_BIN}" "${REPO_ROOT}/k8s/aks/generate_aks_manifests.py" --help >/dev/null
  python_has_modules "${PYTHON_BIN}" yaml scipy matplotlib || die "Rolling mode requires a Python interpreter with yaml, scipy, and matplotlib available for host-side artifact merging and analysis. Activate the repo .venv or install requirements.txt."
}

load_condition_manifests() {
  mapfile -t CONDITION_MANIFESTS < <("${PYTHON_BIN}" - "${CONFIG_PATH}" <<'PY'
import sys
import yaml

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    data = yaml.safe_load(handle)

for condition in data["conditions"]:
    print(condition["name"])
PY
)

  (( ${#CONDITION_MANIFESTS[@]} > 0 )) || die "No conditions were found in ${CONFIG_REL}"
}

validate_fully_controlled_config() {
  "${PYTHON_BIN}" - "${CONFIG_PATH}" <<'PY'
import re
import sys
import yaml

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    raw = yaml.safe_load(handle)

k8s = raw.get("kubernetes") or {}
service = k8s.get("resources") or {}
client = k8s.get("client_resources") or service
threading = (raw.get("cpu_stabilisation") or {}).get("threading") or {}
errors = []

image = str(k8s.get("image", ""))
if "@sha256:" not in image:
    errors.append("kubernetes.image must be a pinned digest reference for the thesis-facing run")

if str(k8s.get("image_pull_policy", "")) != "Always":
    errors.append("kubernetes.image_pull_policy must be Always for the thesis-facing run")

for label, resources in (("service", service), ("client", client)):
    if str(resources.get("cpu_request")) != str(resources.get("cpu_limit")):
        errors.append(f"{label} cpu_request must equal cpu_limit for fully controlled QoS")
    if str(resources.get("memory_request")) != str(resources.get("memory_limit")):
        errors.append(f"{label} memory_request must equal memory_limit for fully controlled QoS")

if not re.fullmatch(r"[0-9]+", str(service.get("cpu_request", ""))):
    errors.append("service cpu_request must be an integer core value for the thesis-facing run")

expected_threads = {
    "pytorch_intra_op": 1,
    "pytorch_inter_op": 1,
    "omp_num_threads": 1,
    "mkl_num_threads": 1,
    "openblas_num_threads": 1,
}
for key, expected in expected_threads.items():
    actual = threading.get(key)
    if actual != expected:
        errors.append(f"cpu_stabilisation.threading.{key} expected {expected}, found {actual}")

if errors:
    for err in errors:
        print(err, file=sys.stderr)
    sys.exit(1)
PY
}

condition_expected_pods() {
  local condition_name="$1"
  if [[ "${condition_name}" == "monolithic_k8s_1svc" ]]; then
    printf '1\n'
    return 0
  fi

  if [[ "${condition_name}" =~ ^chain_([0-9]+)svc$ ]]; then
    printf '%s\n' "${BASH_REMATCH[1]}"
    return 0
  fi

  die "Cannot infer expected pod count for condition ${condition_name}"
}

preflight() {
  ensure_command kubectl
  ensure_command tar

  PYTHON_BIN="$(find_python)" || die "Python is required but neither python3 nor python is available"
  verify_required_files
  verify_python_support
  validate_fully_controlled_config
  load_condition_manifests

  KUBE_CONTEXT="$(kubectl config current-context 2>/dev/null)" || die "Unable to read the current kubectl context"
  KUBE_CLUSTER_INFO="$(kubectl cluster-info 2>/dev/null | head -n 1)" || die "Current kubectl context is not reachable"

  NAMESPACE="$(python_config_get 'kubernetes.namespace')"
  READINESS_TIMEOUT="$(python_config_get 'kubernetes.readiness_timeout')"
  READINESS_TIMEOUT_SECONDS="${READINESS_TIMEOUT%.*}"

  log "Repository root: ${REPO_ROOT}"
  log "Using Python: ${PYTHON_BIN}"
  log "Kubernetes context: ${KUBE_CONTEXT}"
  log "Cluster endpoint: ${KUBE_CLUSTER_INFO}"
  log "Thesis config: ${CONFIG_REL}"
  log "Orchestration mode: rolling one-condition deployment"
  log "Conditions: ${CONDITION_MANIFESTS[*]}"

  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/preflight_rq15_full.py" \
    --config "${CONFIG_PATH}" \
    --mode rolling \
    --namespace "${NAMESPACE}" \
    --nodepool "${NODEPOOL}"
}

prepare_artifact_dirs() {
  mkdir -p "${HOST_EXPORT_DIR}" "${DIAGNOSTICS_DIR}" \
    "${HOST_PARTIAL_RESULTS_DIR}" "${HOST_BENCHMARK_LOG_DIR}"
}

generate_manifests() {
  log "Generating AKS manifests from ${CONFIG_REL}."
  "${PYTHON_BIN}" "${REPO_ROOT}/k8s/aks/generate_aks_manifests.py" --config "${CONFIG_PATH}"
}

validate_generated_manifests() {
  log "Validating generated AKS manifests against the thesis-facing config."
  "${PYTHON_BIN}" - "${CONFIG_PATH}" "${GENERATED_DIR}" "${CONDITION_MANIFESTS[@]}" <<'PY'
import os
import sys
import yaml

config_path, generated_dir, *conditions = sys.argv[1:]

with open(config_path, "r", encoding="utf-8") as handle:
    raw = yaml.safe_load(handle)

threading = raw["cpu_stabilisation"]["threading"]
k8s = raw["kubernetes"]
resources = k8s["resources"]
client_resources = k8s["client_resources"]
expected_env = {
    "PYTORCH_INTRA_OP_THREADS": str(threading["pytorch_intra_op"]),
    "PYTORCH_INTER_OP_THREADS": str(threading["pytorch_inter_op"]),
    "OMP_NUM_THREADS": str(threading["omp_num_threads"]),
    "MKL_NUM_THREADS": str(threading["mkl_num_threads"]),
    "OPENBLAS_NUM_THREADS": str(threading["openblas_num_threads"]),
}

condition_to_services = {
    cond["name"]: len(cond.get("chain_split_points") or []) + 1
    for cond in raw["conditions"]
}

errors = []
required_files = ["00_namespace.yaml", "99_benchmark_client.yaml"] + [f"{name}.yaml" for name in conditions]
for file_name in required_files:
    path = os.path.join(generated_dir, file_name)
    if not os.path.exists(path):
        errors.append(f"missing generated manifest: {file_name}")

for condition in conditions:
    path = os.path.join(generated_dir, f"{condition}.yaml")
    if not os.path.exists(path):
        continue
    with open(path, "r", encoding="utf-8") as handle:
        docs = [doc for doc in yaml.safe_load_all(handle) if doc]
    deployments = [doc for doc in docs if doc.get("kind") == "Deployment"]
    expected_deployments = condition_to_services[condition]
    if len(deployments) != expected_deployments:
        errors.append(
            f"{condition}: expected {expected_deployments} Deployment docs, found {len(deployments)}"
        )
        continue
    for doc in deployments:
        name = doc.get("metadata", {}).get("name", "<unknown>")
        container = doc["spec"]["template"]["spec"]["containers"][0]
        env = {item["name"]: str(item.get("value", "")) for item in container.get("env", [])}
        requests = container.get("resources", {}).get("requests", {})
        limits = container.get("resources", {}).get("limits", {})
        if str(container.get("image")) != str(k8s["image"]):
            errors.append(f"{name}: expected image {k8s['image']}, found {container.get('image')}")
        if str(container.get("imagePullPolicy")) != str(k8s["image_pull_policy"]):
            errors.append(
                f"{name}: expected imagePullPolicy={k8s['image_pull_policy']}, found {container.get('imagePullPolicy')}"
            )
        for key, expected in expected_env.items():
            if env.get(key) != expected:
                errors.append(f"{name}: expected {key}={expected}, found {env.get(key)}")
        if str(requests.get("cpu")) != str(resources["cpu_request"]):
            errors.append(f"{name}: expected requests.cpu={resources['cpu_request']}, found {requests.get('cpu')}")
        if str(limits.get("cpu")) != str(resources["cpu_limit"]):
            errors.append(f"{name}: expected limits.cpu={resources['cpu_limit']}, found {limits.get('cpu')}")
        if str(requests.get("memory")) != str(resources["memory_request"]):
            errors.append(
                f"{name}: expected requests.memory={resources['memory_request']}, found {requests.get('memory')}"
            )
        if str(limits.get("memory")) != str(resources["memory_limit"]):
            errors.append(
                f"{name}: expected limits.memory={resources['memory_limit']}, found {limits.get('memory')}"
            )

client_path = os.path.join(generated_dir, "99_benchmark_client.yaml")
if os.path.exists(client_path):
    with open(client_path, "r", encoding="utf-8") as handle:
        client_doc = yaml.safe_load(handle)
    container = client_doc["spec"]["containers"][0]
    env = {item["name"]: str(item.get("value", "")) for item in container.get("env", [])}
    requests = container.get("resources", {}).get("requests", {})
    limits = container.get("resources", {}).get("limits", {})
    if str(container.get("image")) != str(k8s["image"]):
        errors.append(f"benchmark-client: expected image {k8s['image']}, found {container.get('image')}")
    if str(container.get("imagePullPolicy")) != str(k8s["image_pull_policy"]):
        errors.append(
            f"benchmark-client: expected imagePullPolicy={k8s['image_pull_policy']}, found {container.get('imagePullPolicy')}"
        )
    for key, expected in expected_env.items():
        if env.get(key) != expected:
            errors.append(f"benchmark-client: expected {key}={expected}, found {env.get(key)}")
    if str(requests.get("cpu")) != str(client_resources["cpu_request"]):
        errors.append(
            f"benchmark-client: expected requests.cpu={client_resources['cpu_request']}, found {requests.get('cpu')}"
        )
    if str(limits.get("cpu")) != str(client_resources["cpu_limit"]):
        errors.append(
            f"benchmark-client: expected limits.cpu={client_resources['cpu_limit']}, found {limits.get('cpu')}"
        )
    if str(requests.get("memory")) != str(client_resources["memory_request"]):
        errors.append(
            f"benchmark-client: expected requests.memory={client_resources['memory_request']}, found {requests.get('memory')}"
        )
    if str(limits.get("memory")) != str(client_resources["memory_limit"]):
        errors.append(
            f"benchmark-client: expected limits.memory={client_resources['memory_limit']}, found {limits.get('memory')}"
        )

if errors:
    for error in errors:
        print(error, file=sys.stderr)
    sys.exit(1)
PY
}

wait_for_namespace_deletion() {
  local deadline=$((SECONDS + 180))
  while kubectl get namespace "${NAMESPACE}" >/dev/null 2>&1; do
    if (( SECONDS >= deadline )); then
      die "Timed out waiting for namespace ${NAMESPACE} to terminate"
    fi
    sleep 2
  done
}

cleanup_existing_namespace() {
  if kubectl get namespace "${NAMESPACE}" >/dev/null 2>&1; then
    log "Deleting existing namespace ${NAMESPACE} to guarantee a clean rerun."
    kubectl delete namespace "${NAMESPACE}" --wait=false
    wait_for_namespace_deletion
  fi
}

deploy_rolling_base_resources() {
  cleanup_existing_namespace

  log "Applying namespace manifest."
  kubectl apply -f "${GENERATED_DIR}/00_namespace.yaml"
  RESOURCES_DEPLOYED=1

  log "Applying benchmark client pod manifest."
  kubectl apply -f "${GENERATED_DIR}/99_benchmark_client.yaml"
}

deploy_condition_resources() {
  local condition_name="$1"
  local manifest_path="${GENERATED_DIR}/${condition_name}.yaml"

  log "Applying ${condition_name}."
  kubectl apply -f "${manifest_path}"
}

describe_selected_pods() {
  local selector="$1"
  local pod_names pod_name

  pod_names="$(kubectl get pods -n "${NAMESPACE}" -l "${selector}" -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' 2>/dev/null || true)"
  if [[ -z "${pod_names}" ]]; then
    return 0
  fi

  while IFS= read -r pod_name; do
    [[ -n "${pod_name}" ]] || continue
    kubectl describe pod -n "${NAMESPACE}" "${pod_name}" | tee "${DIAGNOSTICS_DIR}/${pod_name}.describe.txt"
  done <<< "${pod_names}"
}

readiness_failure_diagnostics() {
  local reason="$1"
  local selector="${2:-}"
  local all_pods pod_name

  warn "${reason}"
  kubectl get pods -n "${NAMESPACE}" -o wide | tee "${DIAGNOSTICS_DIR}/readiness_pods.txt"
  if [[ -n "${selector}" ]]; then
    describe_selected_pods "${selector}"
  else
    all_pods="$(kubectl get pods -n "${NAMESPACE}" -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' 2>/dev/null || true)"
    while IFS= read -r pod_name; do
      [[ -n "${pod_name}" ]] || continue
      kubectl describe pod -n "${NAMESPACE}" "${pod_name}" | tee "${DIAGNOSTICS_DIR}/${pod_name}.describe.txt"
    done <<< "${all_pods}"
  fi
}

wait_for_condition_ready() {
  local condition_name="$1"
  local expected_count="$2"
  local deployments deadline deployment_names deployment_name

  deadline=$((SECONDS + READINESS_TIMEOUT_SECONDS + 60))
  while true; do
    deployment_names="$(kubectl get deployments -n "${NAMESPACE}" -l "condition=${condition_name}" -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' 2>/dev/null || true)"
    deployments=0
    if [[ -n "${deployment_names}" ]]; then
      while IFS= read -r deployment_name; do
        [[ -n "${deployment_name}" ]] || continue
        deployments=$((deployments + 1))
      done <<< "${deployment_names}"
    fi

    if (( deployments == expected_count )); then
      break
    fi

    if (( SECONDS >= deadline )); then
      readiness_failure_diagnostics "Timed out waiting for ${expected_count} deployment objects for ${condition_name}." "condition=${condition_name}"
      return 1
    fi
    sleep 2
  done

  while IFS= read -r deployment_name; do
    [[ -n "${deployment_name}" ]] || continue
    log "Waiting for deployment ${deployment_name} rollout."
    kubectl rollout status "deployment/${deployment_name}" -n "${NAMESPACE}" --timeout="${READINESS_TIMEOUT_SECONDS}s" || {
      readiness_failure_diagnostics "Deployment ${deployment_name} failed to become available." "condition=${condition_name}"
      return 1
    }
  done <<< "${deployment_names}"

  log "Waiting for condition ${condition_name} pods to become Ready."
  kubectl wait --for=condition=Ready pod -n "${NAMESPACE}" -l "condition=${condition_name}" --timeout="${READINESS_TIMEOUT_SECONDS}s" >/dev/null || {
    readiness_failure_diagnostics "Pods for ${condition_name} did not become Ready in time." "condition=${condition_name}"
    return 1
  }
}

wait_for_pod_exists() {
  local pod_name="$1"
  local deadline=$((SECONDS + 60))

  until kubectl get pod -n "${NAMESPACE}" "${pod_name}" >/dev/null 2>&1; do
    if (( SECONDS >= deadline )); then
      readiness_failure_diagnostics "Timed out waiting for pod ${pod_name} to appear." "role=client"
      return 1
    fi
    sleep 2
  done
}

wait_for_client_ready() {
  wait_for_pod_exists "${CLIENT_POD_NAME}"
  log "Waiting for client pod ${CLIENT_POD_NAME} to become Ready."
  kubectl wait --for=condition=Ready "pod/${CLIENT_POD_NAME}" -n "${NAMESPACE}" --timeout="${READINESS_TIMEOUT_SECONDS}s" >/dev/null || {
    readiness_failure_diagnostics "Client pod ${CLIENT_POD_NAME} did not become Ready in time." "role=client"
    return 1
  }
}

condition_resources_remaining() {
  local condition_name="$1"
  local deployment_name pod_name

  deployment_name="$(kubectl get deployments -n "${NAMESPACE}" -l "condition=${condition_name}" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
  pod_name="$(kubectl get pods -n "${NAMESPACE}" -l "condition=${condition_name}" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
  [[ -n "${deployment_name}" || -n "${pod_name}" ]]
}

wait_for_condition_removal() {
  local condition_name="$1"
  local deadline=$((SECONDS + READINESS_TIMEOUT_SECONDS + 60))

  while condition_resources_remaining "${condition_name}"; do
    if (( SECONDS >= deadline )); then
      readiness_failure_diagnostics "Timed out waiting for ${condition_name} resources to terminate." "condition=${condition_name}"
      return 1
    fi
    sleep 2
  done
}

delete_condition_resources() {
  local condition_name="$1"
  local manifest_path="${GENERATED_DIR}/${condition_name}.yaml"

  log "Deleting ${condition_name} resources before the next rolling step."
  kubectl delete -f "${manifest_path}" --ignore-not-found=true >/dev/null || true
  wait_for_condition_removal "${condition_name}"
}

copy_results_with_fallback() {
  local source_path="$1"
  local destination_path="$2"
  local destination_parent

  destination_parent="$(dirname "${destination_path}")"
  mkdir -p "${destination_parent}"
  rm -rf "${destination_path}"

  if kubectl cp "${NAMESPACE}/${CLIENT_POD_NAME}:${source_path}" "${destination_path}"; then
    return 0
  fi

  warn "kubectl cp failed for ${source_path}; attempting a Python tar-stream fallback."
  local archive_path="${destination_parent}/$(basename "${source_path}").tar"

  kubectl exec -i -n "${NAMESPACE}" "${CLIENT_POD_NAME}" -- python - "${source_path}" <<'PY' > "${archive_path}"
import os
import sys
import tarfile

source_path = os.path.abspath(sys.argv[1])
if not os.path.exists(source_path):
    raise SystemExit(f"missing path: {source_path}")

with tarfile.open(fileobj=sys.stdout.buffer, mode="w") as archive:
    archive.add(source_path, arcname=os.path.basename(source_path))
PY

  tar -xf "${archive_path}" -C "${destination_parent}"
  rm -f "${archive_path}"
}

inject_runtime_metadata() {
  local condition_name="$1"

  log "Injecting live runtime metadata for ${condition_name}."
  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/inject_k8s_runtime_metadata.py" \
    --config "${CONFIG_PATH}" \
    --namespace "${NAMESPACE}" \
    --client-pod "${CLIENT_POD_NAME}"
}

run_condition_benchmark() {
  local condition_name="$1"
  local benchmark_exit_code
  local condition_log_path="${HOST_BENCHMARK_LOG_DIR}/${condition_name}.log"
  local pod_output_dir="${POD_PARTIAL_RESULTS_ROOT}/${condition_name}"
  local host_condition_results_dir="${HOST_PARTIAL_RESULTS_DIR}/${condition_name}"

  inject_runtime_metadata "${condition_name}"

  log "Running the in-cluster rolling benchmark for ${condition_name}."
  kubectl exec -n "${NAMESPACE}" "${CLIENT_POD_NAME}" -- rm -rf "${pod_output_dir}" >/dev/null 2>&1 || true

  set +e
  kubectl exec -n "${NAMESPACE}" "${CLIENT_POD_NAME}" -- \
    python run_k8s_experiment.py --config "${CONFIG_REL}" --condition "${condition_name}" --output-dir "${pod_output_dir}" 2>&1 | tee "${condition_log_path}"
  benchmark_exit_code=${PIPESTATUS[0]}
  set -e

  (( benchmark_exit_code == 0 )) || die "Benchmark command failed for ${condition_name} with exit code ${benchmark_exit_code}"

  log "Copying rolling results for ${condition_name} from pod path ${pod_output_dir}."
  kubectl exec -n "${NAMESPACE}" "${CLIENT_POD_NAME}" -- test -d "${pod_output_dir}" || die "Results directory does not exist in the client pod: ${pod_output_dir}"
  copy_results_with_fallback "${pod_output_dir}" "${host_condition_results_dir}"
  kubectl exec -n "${NAMESPACE}" "${CLIENT_POD_NAME}" -- rm -rf "${pod_output_dir}" >/dev/null 2>&1 || true
}

merge_rolling_results() {
  log "Merging rolling per-condition artifacts into ${MERGED_RESULTS_DIR}."
  "${PYTHON_BIN}" - "${HOST_PARTIAL_RESULTS_DIR}" "${MERGED_RESULTS_DIR}" "${CONFIG_PATH}" "${CONDITION_MANIFESTS[@]}" <<'PY'
import csv
import json
import os
import shutil
import sys
from dataclasses import asdict

from src.benchmark.config import load_config

partial_root, merged_dir, config_path, *conditions = sys.argv[1:]

os.makedirs(merged_dir, exist_ok=True)

fieldnames = None
rows = []
local_validation = {}
grpc_validation = {}
warmup_calibration = {}
deployment_metadata = {}
environment = None

for condition in conditions:
    condition_dir = os.path.join(partial_root, condition)
    if not os.path.isdir(condition_dir):
        raise SystemExit(f"missing partial results directory: {condition_dir}")

    raw_path = os.path.join(condition_dir, "raw_iterations.csv")
    parity_path = os.path.join(condition_dir, "parity_validation.json")
    warmup_path = os.path.join(condition_dir, "warmup_calibration.json")
    deployment_path = os.path.join(condition_dir, "deployment_metadata.json")
    environment_path = os.path.join(condition_dir, "environment.json")

    with open(raw_path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if fieldnames is None:
            fieldnames = reader.fieldnames
        elif reader.fieldnames != fieldnames:
            raise SystemExit(
                f"raw_iterations.csv header mismatch for {condition}: {reader.fieldnames} != {fieldnames}"
            )
        rows.extend(list(reader))

    with open(parity_path, "r", encoding="utf-8") as handle:
        parity = json.load(handle)
    local_validation.update(parity.get("local_validation", {}))
    grpc_validation.update(parity.get("grpc_validation", {}))

    with open(warmup_path, "r", encoding="utf-8") as handle:
        warmup_calibration.update(json.load(handle))

    with open(deployment_path, "r", encoding="utf-8") as handle:
        deployment_metadata.update(json.load(handle))

    if environment is None:
        with open(environment_path, "r", encoding="utf-8") as handle:
            environment = json.load(handle)

if not rows or fieldnames is None:
    raise SystemExit("rolling merge failed: no raw iterations were collected")

raw_output_path = os.path.join(merged_dir, "raw_iterations.csv")
with open(raw_output_path, "w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

shutil.copy2(config_path, os.path.join(merged_dir, "config.yaml"))

resolved_config = asdict(load_config(config_path))
with open(os.path.join(merged_dir, "resolved_config.json"), "w", encoding="utf-8") as handle:
    json.dump(
        {
            "source_config_path": os.path.abspath(config_path),
            "resolved_config": resolved_config,
        },
        handle,
        indent=2,
    )

if environment is None:
    environment = {}
environment["rolling_orchestration"] = {
    "enabled": True,
    "conditions": conditions,
    "partial_results_root": os.path.abspath(partial_root),
    "teardown_between_conditions": True,
}

with open(os.path.join(merged_dir, "environment.json"), "w", encoding="utf-8") as handle:
    json.dump(environment, handle, indent=2)

with open(os.path.join(merged_dir, "parity_validation.json"), "w", encoding="utf-8") as handle:
    json.dump(
        {
            "local_validation": local_validation,
            "grpc_validation": grpc_validation,
        },
        handle,
        indent=2,
    )

with open(os.path.join(merged_dir, "warmup_calibration.json"), "w", encoding="utf-8") as handle:
    json.dump(warmup_calibration, handle, indent=2)

with open(os.path.join(merged_dir, "deployment_metadata.json"), "w", encoding="utf-8") as handle:
    json.dump(deployment_metadata, handle, indent=2)
PY
  FINAL_RESULTS_DIR="${MERGED_RESULTS_DIR}"
}

run_host_analysis() {
  log "Running host-side analysis on merged rolling results."
  "${PYTHON_BIN}" "${REPO_ROOT}/run_analysis.py" "${FINAL_RESULTS_DIR}"
}

run_rolling_benchmark() {
  local condition_name expected_count

  deploy_rolling_base_resources
  wait_for_client_ready

  for condition_name in "${CONDITION_MANIFESTS[@]}"; do
    deploy_condition_resources "${condition_name}"
    expected_count="$(condition_expected_pods "${condition_name}")"
    wait_for_condition_ready "${condition_name}" "${expected_count}"
    run_condition_benchmark "${condition_name}"
    delete_condition_resources "${condition_name}"
  done

  merge_rolling_results
  run_host_analysis
}

gather_diagnostics() {
  if ! kubectl get namespace "${NAMESPACE}" >/dev/null 2>&1; then
    warn "Namespace ${NAMESPACE} no longer exists; skipping cluster diagnostics."
    return 0
  fi

  log "Gathering Kubernetes diagnostics under ${DIAGNOSTICS_DIR}."
  mkdir -p "${DIAGNOSTICS_DIR}"

  kubectl get pods -n "${NAMESPACE}" -o wide | tee "${DIAGNOSTICS_DIR}/kubectl_get_pods.txt"
  kubectl get svc -n "${NAMESPACE}" | tee "${DIAGNOSTICS_DIR}/kubectl_get_svc.txt"

  local pod_names pod_name
  pod_names="$(kubectl get pods -n "${NAMESPACE}" -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' 2>/dev/null || true)"
  while IFS= read -r pod_name; do
    [[ -n "${pod_name}" ]] || continue
    kubectl describe pod -n "${NAMESPACE}" "${pod_name}" > "${DIAGNOSTICS_DIR}/${pod_name}.describe.txt" || true
    kubectl logs -n "${NAMESPACE}" "${pod_name}" --tail=200 > "${DIAGNOSTICS_DIR}/${pod_name}.log.txt" 2>&1 || true
  done <<< "${pod_names}"
}

cleanup_cluster() {
  local manifest_name manifest_path

  log "Cleaning up benchmark resources in reverse deployment order."
  kubectl delete pod -n "${NAMESPACE}" "${CLIENT_POD_NAME}" --ignore-not-found=true || true
  for (( idx=${#CONDITION_MANIFESTS[@]} - 1; idx>=0; idx-- )); do
    manifest_name="${CONDITION_MANIFESTS[idx]}"
    manifest_path="${GENERATED_DIR}/${manifest_name}.yaml"
    kubectl delete -f "${manifest_path}" --ignore-not-found=true || true
  done
  kubectl delete namespace "${NAMESPACE}" --ignore-not-found=true --wait=false || true
  wait_for_namespace_deletion
  RESOURCES_DEPLOYED=0
}

main() {
  parse_args "$@"
  cd "${REPO_ROOT}"

  preflight
  prepare_artifact_dirs
  generate_manifests
  validate_generated_manifests
  run_rolling_benchmark
  cleanup_cluster

  log "RQ1.5 rolling fully controlled run finished successfully. Final results directory: ${FINAL_RESULTS_DIR}"
}

main "$@"
#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd -P)"

CONFIG_REL="configs/rq1/1.4/rq1_4_fully_controlled.yaml"
CONFIG_PATH="${REPO_ROOT}/${CONFIG_REL}"
IMAGE_TAG="thesis-inference:latest"
IMAGE_REF=""
CLIENT_POD_NAME="benchmark-client"
GENERATED_DIR="${REPO_ROOT}/k8s/base/generated"

readonly REFERENCE_FULLY_CONTROLLED_CONFIGS=(
  "configs/rq1/1.1/rq1_1_fully_controlled.yaml"
  "configs/rq1/1.2/rq1_2_fully_controlled.yaml"
)

RUN_TS="$(date -u +%Y%m%d_%H%M%S)"
HOST_EXPORT_DIR="${REPO_ROOT}/results_exports/rq1_4_fully_controlled_${RUN_TS}"
DIAGNOSTICS_DIR="${HOST_EXPORT_DIR}/diagnostics"
BENCHMARK_LOG_PATH="${HOST_EXPORT_DIR}/benchmark.log"
CLIENT_MANIFEST_PATH="${HOST_EXPORT_DIR}/benchmark-client.generated.yaml"
HOST_PARTIAL_RESULTS_DIR="${HOST_EXPORT_DIR}/partial_results"
HOST_BENCHMARK_LOG_DIR="${HOST_EXPORT_DIR}/condition_logs"
MERGED_RESULTS_DIR="${HOST_EXPORT_DIR}/merged_results"
POD_PARTIAL_RESULTS_ROOT="/tmp/rq14_rolling_${RUN_TS}"

PYTHON_BIN=""
KUBE_CONTEXT=""
KUBE_CLUSTER_INFO=""
NAMESPACE=""
READINESS_TIMEOUT=""
READINESS_TIMEOUT_SECONDS=""
POD_RESULTS_DIR=""

CLEANUP_ON_FAILURE=0
PRUNE_IMAGE=0
ROLLING_MODE=0
SKIP_IMAGE_BUILD=0
RESOURCES_DEPLOYED=0
FINAL_RESULTS_DIR=""
HOST_CPU_GOVERNOR_SET=0
HOST_CPU_TURBO_DISABLED=0

readonly REQUIRED_FILES=(
  "Dockerfile"
  "run_k8s_experiment.py"
  "k8s/generate_manifests.py"
  "${CONFIG_REL}"
  "${REFERENCE_FULLY_CONTROLLED_CONFIGS[0]}"
  "${REFERENCE_FULLY_CONTROLLED_CONFIGS[1]}"
  "k8s/base/client-pod.yaml"
)

readonly CONDITION_MANIFESTS=(
  "monolithic_k8s_1svc"
  "chain_2svc"
  "chain_3svc"
  "chain_4svc"
  "chain_5svc"
)

usage() {
  cat <<EOF
Usage: bash scripts/run_rq14_fully_controlled.sh [options]

Runs the RQ1.4 fully controlled local Kubernetes benchmark end to end.

Options:
  --cleanup-on-failure  Tear down rq14 resources if the run fails.
  --image-ref REF       Pull an existing pinned image and retag it as ${IMAGE_TAG}.
  --prune-image         Remove ${IMAGE_TAG} after a successful run.
  --rolling             Deploy and benchmark one condition at a time.
  --skip-image-build    Reuse an existing local ${IMAGE_TAG}.
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

  restore_host_cpu_controls || true

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
      --image-ref)
        shift
        [[ $# -gt 0 ]] || die "--image-ref requires a value"
        IMAGE_REF="$1"
        ;;
      --prune-image)
        PRUNE_IMAGE=1
        ;;
      --rolling)
        ROLLING_MODE=1
        ;;
      --skip-image-build)
        SKIP_IMAGE_BUILD=1
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
  "${PYTHON_BIN}" "${REPO_ROOT}/k8s/generate_manifests.py" --help >/dev/null

  if (( ROLLING_MODE )); then
    python_has_modules "${PYTHON_BIN}" yaml scipy matplotlib || die "Rolling mode requires a Python interpreter with yaml, scipy, and matplotlib available for host-side artifact merging and analysis. Activate the repo .venv or install requirements.txt."
  fi
}

validate_fully_controlled_config() {
  local required_pair key expected actual config_rel
  local shared_keys=(
    "model.name"
    "model.pretrained"
    "model.device"
    "model.input_shape.0"
    "model.input_shape.1"
    "model.input_shape.2"
    "model.input_shape.3"
    "model.precision"
    "benchmark.rounds"
    "benchmark.warmup_iterations"
    "benchmark.measured_iterations"
    "benchmark.cooldown_seconds"
    "benchmark.seed"
    "parity.atol"
    "parity.num_inputs"
    "warmup_calibration.window"
    "warmup_calibration.cv_threshold"
    "warmup_calibration.max_extra_iterations"
    "cpu_stabilisation.threading.pytorch_intra_op"
    "cpu_stabilisation.threading.pytorch_inter_op"
    "cpu_stabilisation.threading.omp_num_threads"
    "cpu_stabilisation.threading.mkl_num_threads"
    "cpu_stabilisation.threading.openblas_num_threads"
    "cpu_stabilisation.affinity.enabled"
    "cpu_stabilisation.affinity.num_cores"
    "cpu_stabilisation.affinity.avoid_smt"
    "cpu_stabilisation.affinity.explicit_cpus"
    "cpu_stabilisation.priority.enabled"
    "cpu_stabilisation.priority.nice_value"
    "cpu_stabilisation.governor.set_governor"
    "cpu_stabilisation.governor.requested_mode"
    "cpu_stabilisation.turbo.disable_turbo"
  )
  local required_pairs=(
    "kubernetes.namespace=rq14"
    "kubernetes.grpc_port=50051"
    "kubernetes.max_message_bytes=16777216"
    "kubernetes.image=${IMAGE_TAG}"
    "kubernetes.image_pull_policy=IfNotPresent"
    "kubernetes.resources.cpu_request=1"
    "kubernetes.resources.cpu_limit=1"
    "kubernetes.client_resources.cpu_request=1"
    "kubernetes.client_resources.cpu_limit=1"
  )

  expected="${REPO_ROOT}/${REFERENCE_FULLY_CONTROLLED_CONFIGS[0]}"
  for key in "${shared_keys[@]}"; do
    actual="$(python_yaml_get "${expected}" "${key}")"
    for config_rel in "${REFERENCE_FULLY_CONTROLLED_CONFIGS[@]}" "${CONFIG_REL}"; do
      local compared_file="${REPO_ROOT}/${config_rel}"
      local compared_value
      compared_value="$(python_yaml_get "${compared_file}" "${key}")"
      [[ "${compared_value}" == "${actual}" ]] || die "Fully controlled config drift detected: ${config_rel} has ${key}='${compared_value}', expected '${actual}' to match ${REFERENCE_FULLY_CONTROLLED_CONFIGS[0]}"
    done
  done

  for required_pair in "${required_pairs[@]}"; do
    key="${required_pair%%=*}"
    expected="${required_pair#*=}"
    actual="$(python_config_get "${key}")"
    [[ "${actual}" == "${expected}" ]] || die "Fully controlled invariant failed: ${key} expected '${expected}', found '${actual}'"
  done
}

wait_for_kube_system_label_ready() {
  local label_selector="$1"
  local component_name="$2"
  local pod_count

  pod_count="$(kubectl get pods -n kube-system -l "${label_selector}" --no-headers 2>/dev/null | wc -l | tr -d '[:space:]')"
  if [[ -z "${pod_count}" || "${pod_count}" == "0" ]]; then
    warn "No kube-system pods matched '${label_selector}' while checking ${component_name}. Continuing because this cluster may use a non-standard add-on layout."
    return 0
  fi

  log "Checking kube-system readiness for ${component_name} (${label_selector})."
  kubectl wait --for=condition=Ready pod -n kube-system -l "${label_selector}" --timeout=60s >/dev/null || {
    kubectl get pods -n kube-system -l "${label_selector}" -o wide || true
    die "kube-system component '${component_name}' is not Ready. Local cluster DNS or service routing is unhealthy; fix the cluster before running RQ1.4."
  }
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
  ensure_command docker
  ensure_command kubectl
  ensure_command tar

  PYTHON_BIN="$(find_python)" || die "Python is required but neither python3 nor python is available"
  verify_required_files
  verify_python_support
  validate_fully_controlled_config

  KUBE_CONTEXT="$(kubectl config current-context 2>/dev/null)" || die "Unable to read the current kubectl context"
  KUBE_CLUSTER_INFO="$(kubectl cluster-info 2>/dev/null | head -n 1)" || die "Current kubectl context is not reachable"

  NAMESPACE="$(python_config_get 'kubernetes.namespace')"
  READINESS_TIMEOUT="$(python_config_get 'kubernetes.readiness_timeout')"
  READINESS_TIMEOUT_SECONDS="${READINESS_TIMEOUT%.*}"

  log "Repository root: ${REPO_ROOT}"
  log "Using Python: ${PYTHON_BIN}"
  log "Kubernetes context: ${KUBE_CONTEXT}"
  log "Cluster endpoint: ${KUBE_CLUSTER_INFO}"
  log "Fully controlled config: ${CONFIG_REL}"
  if (( ROLLING_MODE )); then
    log "Orchestration mode: rolling one-condition deployment"
  else
    log "Orchestration mode: full simultaneous deployment"
  fi

  wait_for_kube_system_label_ready "k8s-app=kube-dns" "CoreDNS"
  wait_for_kube_system_label_ready "k8s-app=kube-proxy" "kube-proxy"

  warn "This automation guarantees single-threaded pods and 1-CPU Guaranteed QoS from the repo config. Fixed-core exclusivity, CPU governor control, and turbo disable remain node-level or best-effort in Kubernetes and are not fully enforceable from this script alone."
}

prepare_artifact_dirs() {
  mkdir -p "${HOST_EXPORT_DIR}" "${DIAGNOSTICS_DIR}"
}

capacity_preflight() {
  if (( ROLLING_MODE )); then
    log "Checking whether the active cluster can fit the rolling one-condition deployment set."
  else
    log "Checking whether the active cluster can fit the full fully controlled deployment set."
  fi
  "${PYTHON_BIN}" - "${CONFIG_PATH}" "${NAMESPACE}" "${ROLLING_MODE}" <<'PY'
import json
import subprocess
import sys

import yaml

config_path, benchmark_namespace, rolling_mode = sys.argv[1:]
rolling_mode = rolling_mode == "1"


def parse_cpu_to_millicores(value):
    text = str(value).strip()
    if text.endswith("m"):
        return int(text[:-1])
    return int(float(text) * 1000)


def kubectl_json(*args):
    output = subprocess.check_output(["kubectl", *args], text=True)
    return json.loads(output)


with open(config_path, "r", encoding="utf-8") as handle:
    config = yaml.safe_load(handle)

allocatable_mcpu = 0
for node in kubectl_json("get", "nodes", "-o", "json")["items"]:
    allocatable_mcpu += parse_cpu_to_millicores(node["status"]["allocatable"]["cpu"])

current_requested_mcpu = 0
for pod in kubectl_json("get", "pods", "-A", "-o", "json")["items"]:
    metadata = pod.get("metadata", {})
    namespace = metadata.get("namespace", "")
    if namespace == benchmark_namespace:
        continue

    phase = pod.get("status", {}).get("phase")
    if phase in {"Succeeded", "Failed"}:
        continue

    for container in pod.get("spec", {}).get("containers", []):
        requests = container.get("resources", {}).get("requests", {})
        cpu_request = requests.get("cpu")
        if cpu_request is None:
            continue
        current_requested_mcpu += parse_cpu_to_millicores(cpu_request)

kubernetes = config["kubernetes"]
service_cpu_request_mcpu = parse_cpu_to_millicores(kubernetes["resources"]["cpu_request"])
client_resources = kubernetes.get("client_resources", kubernetes["resources"])
client_cpu_request_mcpu = parse_cpu_to_millicores(client_resources["cpu_request"])
condition_service_counts = [
    (len(condition.get("chain_split_points") or []) + 1)
    for condition in config["conditions"]
]

if rolling_mode:
    benchmark_requested_mcpu = client_cpu_request_mcpu
    benchmark_requested_mcpu += max(condition_service_counts, default=0) * service_cpu_request_mcpu
else:
    benchmark_requested_mcpu = client_cpu_request_mcpu
    for service_count in condition_service_counts:
        benchmark_requested_mcpu += service_count * service_cpu_request_mcpu

required_total_mcpu = current_requested_mcpu + benchmark_requested_mcpu

if required_total_mcpu > allocatable_mcpu:
    current_cores = current_requested_mcpu / 1000.0
    benchmark_cores = benchmark_requested_mcpu / 1000.0
    allocatable_cores = allocatable_mcpu / 1000.0
    deficit_cores = (required_total_mcpu - allocatable_mcpu) / 1000.0
    mode_text = "rolling one-condition" if rolling_mode else "simultaneous fully controlled"
    raise SystemExit(
        "Cluster capacity preflight failed. "
        f"Allocatable CPU={allocatable_cores:.3f} cores, "
        f"current non-{benchmark_namespace} requested CPU={current_cores:.3f} cores, "
        f"benchmark requested CPU={benchmark_cores:.3f} cores. "
        f"The {mode_text} deployment would exceed cluster capacity by {deficit_cores:.3f} cores. "
        "Increase local cluster CPU allocation or reduce background cluster load."
    )

mode_label = "rolling" if rolling_mode else "simultaneous"
print(
    f"Cluster capacity OK for {mode_label} mode: "
    f"allocatable={allocatable_mcpu / 1000.0:.3f} cores, "
    f"current requested={current_requested_mcpu / 1000.0:.3f} cores, "
    f"benchmark requested={benchmark_requested_mcpu / 1000.0:.3f} cores"
)
PY
}

# ---------------------------------------------------------------------------
# Host-level CPU controls (best-effort, non-fatal)
# ---------------------------------------------------------------------------

prepare_host_cpu_controls() {
  log "Attempting to apply host-level CPU controls (best-effort)."

  local governor_ok=0 turbo_ok=0

  # Set performance governor on all CPUs
  if ls /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null 2>&1; then
    if echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null 2>&1; then
      governor_ok=1
      log "CPU governor set to 'performance' on all CPUs."
    else
      warn "Could not set CPU governor to 'performance' (sudo write to sysfs failed). Continuing with default scheduler."
    fi
  else
    warn "cpufreq governor sysfs path not found; CPU frequency scaling controls are unavailable on this host."
  fi

  # Disable turbo / boost
  local boost_path=""
  if [[ -f /sys/devices/system/cpu/intel_pstate/no_turbo ]]; then
    boost_path="/sys/devices/system/cpu/intel_pstate/no_turbo"
    if echo "1" | sudo tee "${boost_path}" >/dev/null 2>&1; then
      turbo_ok=1
      log "Intel turbo boost disabled (intel_pstate/no_turbo=1)."
    else
      warn "Could not disable Intel turbo boost. Continuing with turbo enabled."
    fi
  elif [[ -f /sys/devices/system/cpu/cpufreq/boost ]]; then
    boost_path="/sys/devices/system/cpu/cpufreq/boost"
    if echo "0" | sudo tee "${boost_path}" >/dev/null 2>&1; then
      turbo_ok=1
      log "CPU boost disabled (cpufreq/boost=0)."
    else
      warn "Could not disable CPU boost. Continuing with boost enabled."
    fi
  else
    warn "No known boost/turbo sysfs path found; turbo controls are unavailable on this host."
  fi

  HOST_CPU_GOVERNOR_SET="${governor_ok}"
  HOST_CPU_TURBO_DISABLED="${turbo_ok}"

  if (( governor_ok || turbo_ok )); then
    log "Host CPU controls applied: governor_set=${governor_ok} turbo_disabled=${turbo_ok}"
  else
    warn "No host CPU controls could be applied. Results may exhibit higher variance due to CPU frequency scaling."
  fi
}

restore_host_cpu_controls() {
  if (( HOST_CPU_GOVERNOR_SET )); then
    if echo "schedutil" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null 2>&1; then
      log "CPU governor restored to 'schedutil'."
    else
      warn "Could not restore CPU governor to 'schedutil'."
    fi
  fi

  if (( HOST_CPU_TURBO_DISABLED )); then
    if [[ -f /sys/devices/system/cpu/intel_pstate/no_turbo ]]; then
      echo "0" | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo >/dev/null 2>&1 || \
        warn "Could not re-enable Intel turbo boost."
    elif [[ -f /sys/devices/system/cpu/cpufreq/boost ]]; then
      echo "1" | sudo tee /sys/devices/system/cpu/cpufreq/boost >/dev/null 2>&1 || \
        warn "Could not re-enable CPU boost."
    fi
    log "CPU boost/turbo restored."
  fi
}

build_image() {
  if [[ -n "${IMAGE_REF}" ]]; then
    [[ "${IMAGE_REF}" == *@sha256:* ]] || die "--image-ref must be pinned with @sha256:<digest>"
    log "Pulling existing pinned image ${IMAGE_REF}."
    docker pull "${IMAGE_REF}"
    log "Tagging ${IMAGE_REF} as ${IMAGE_TAG} for local Kubernetes."
    docker tag "${IMAGE_REF}" "${IMAGE_TAG}"
    return 0
  fi

  if (( SKIP_IMAGE_BUILD )); then
    log "Skipping Docker build; reusing local ${IMAGE_TAG}."
    docker image inspect "${IMAGE_TAG}" >/dev/null || die "Local image ${IMAGE_TAG} not found while --skip-image-build is set."
    return 0
  fi

  docker build -t "${IMAGE_TAG}" "${REPO_ROOT}"
}

load_image_if_needed() {
  case "${KUBE_CONTEXT}" in
    docker-desktop|docker-desktop-data|rancher-desktop*)
      log "Current context shares the local Docker image store; no explicit image-load step is required."
      ;;
    kind-*)
      if command -v kind >/dev/null 2>&1; then
        local cluster_name="${KUBE_CONTEXT#kind-}"
        log "Loading ${IMAGE_TAG} into kind cluster ${cluster_name}."
        kind load docker-image "${IMAGE_TAG}" --name "${cluster_name}"
      else
        warn "Context ${KUBE_CONTEXT} looks like kind, but the 'kind' CLI is unavailable. Continuing without an explicit image-load step."
      fi
      ;;
    minikube)
      if command -v minikube >/dev/null 2>&1; then
        log "Loading ${IMAGE_TAG} into minikube."
        minikube image load "${IMAGE_TAG}"
      else
        warn "Context ${KUBE_CONTEXT} is minikube, but the 'minikube' CLI is unavailable. Continuing without an explicit image-load step."
      fi
      ;;
    *)
      warn "This script assumes the active cluster can see ${IMAGE_TAG}. Context ${KUBE_CONTEXT} is not handled explicitly for image loading."
      ;;
  esac
}

generate_manifests() {
  log "Generating RQ1.4 fully controlled manifests from ${CONFIG_REL}."
  "${PYTHON_BIN}" "${REPO_ROOT}/k8s/generate_manifests.py" --config "${CONFIG_PATH}" --all
}

validate_generated_manifests() {
  log "Validating that the generated service manifests remain fully controlled."
  "${PYTHON_BIN}" - "${GENERATED_DIR}" <<'PY'
import os
import sys
import yaml

generated_dir = sys.argv[1]
expected_files = [
    "namespace.yaml",
    "monolithic_k8s_1svc.yaml",
    "chain_2svc.yaml",
    "chain_3svc.yaml",
    "chain_4svc.yaml",
    "chain_5svc.yaml",
]
expected_env = {
    "PYTORCH_INTRA_OP_THREADS": "1",
    "PYTORCH_INTER_OP_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
}
errors = []

for file_name in expected_files:
    path = os.path.join(generated_dir, file_name)
    if not os.path.exists(path):
        errors.append(f"missing generated manifest: {file_name}")
        continue

    if file_name == "namespace.yaml":
        continue

    with open(path, "r", encoding="utf-8") as handle:
        docs = [doc for doc in yaml.safe_load_all(handle) if doc]

    for doc in docs:
        if doc.get("kind") != "Deployment":
            continue
        metadata = doc.get("metadata", {})
        name = metadata.get("name", "<unknown>")
        container = doc["spec"]["template"]["spec"]["containers"][0]
        env = {
            item["name"]: str(item.get("value", ""))
            for item in container.get("env", [])
        }
        resources = container.get("resources", {})
        requests = resources.get("requests", {})
        limits = resources.get("limits", {})

        for key, expected_value in expected_env.items():
            actual_value = env.get(key)
            if actual_value != expected_value:
                errors.append(
                    f"{name}: expected {key}={expected_value}, found {actual_value}"
                )

        if str(requests.get("cpu")) != "1":
            errors.append(f"{name}: expected requests.cpu=1, found {requests.get('cpu')}")
        if str(limits.get("cpu")) != "1":
            errors.append(f"{name}: expected limits.cpu=1, found {limits.get('cpu')}")

if errors:
    for error in errors:
        print(error, file=sys.stderr)
    sys.exit(1)
PY
}

render_client_manifest() {
  log "Rendering a fully controlled client pod manifest directly from the config."
  "${PYTHON_BIN}" - "${CONFIG_PATH}" "${KUBE_CONTEXT}" "${KUBE_CLUSTER_INFO}" > "${CLIENT_MANIFEST_PATH}" <<'PY'
import sys
import yaml

config_path, kube_context, kube_cluster_info = sys.argv[1], sys.argv[2], sys.argv[3]

with open(config_path, "r", encoding="utf-8") as handle:
    config = yaml.safe_load(handle)

kubernetes = config["kubernetes"]
threading = config["cpu_stabilisation"]["threading"]
resources = kubernetes.get("client_resources", kubernetes["resources"])

lines = [
    "# Generated by scripts/run_rq14_fully_controlled.sh",
    "apiVersion: v1",
    "kind: Pod",
    "metadata:",
    "  name: benchmark-client",
    f"  namespace: {kubernetes['namespace']}",
    "  labels:",
    "    app: thesis-inference",
    "    role: client",
    "spec:",
    "  restartPolicy: Never",
    "  containers:",
    "    - name: client",
    f"      image: {kubernetes['image']}",
    f"      imagePullPolicy: {kubernetes.get('image_pull_policy', 'IfNotPresent')}",
    '      command: ["sleep", "infinity"]',
    "      env:",
    "        - name: PYTORCH_INTRA_OP_THREADS",
    f"          value: \"{threading['pytorch_intra_op']}\"",
    "        - name: PYTORCH_INTER_OP_THREADS",
    f"          value: \"{threading['pytorch_inter_op']}\"",
    "        - name: OMP_NUM_THREADS",
    f"          value: \"{threading['omp_num_threads']}\"",
    "        - name: MKL_NUM_THREADS",
    f"          value: \"{threading['mkl_num_threads']}\"",
    "        - name: OPENBLAS_NUM_THREADS",
    f"          value: \"{threading['openblas_num_threads']}\"",
    "        - name: KUBE_CLUSTER_CONTEXT",
    f"          value: \"{kube_context}\"",
    "        - name: KUBE_CLUSTER_INFO",
    f"          value: \"{kube_cluster_info}\"",
    "        - name: MY_POD_NAME",
    "          valueFrom:",
    "            fieldRef:",
    "              fieldPath: metadata.name",
    "        - name: MY_NODE_NAME",
    "          valueFrom:",
    "            fieldRef:",
    "              fieldPath: spec.nodeName",
    "        - name: MY_POD_IP",
    "          valueFrom:",
    "            fieldRef:",
    "              fieldPath: status.podIP",
    "      securityContext:",
    "        capabilities:",
    "          add:",
    "            - SYS_NICE",
    "      resources:",
    "        requests:",
    f"          cpu: \"{resources['cpu_request']}\"",
    f"          memory: \"{resources['memory_request']}\"",
    "        limits:",
    f"          cpu: \"{resources['cpu_limit']}\"",
    f"          memory: \"{resources['memory_limit']}\"",
]

print("\n".join(lines))
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

deploy_full_resources() {
  local manifest_name manifest_path

  cleanup_existing_namespace

  log "Applying namespace manifest."
  kubectl apply -f "${GENERATED_DIR}/namespace.yaml"
  RESOURCES_DEPLOYED=1

  for manifest_name in "${CONDITION_MANIFESTS[@]}"; do
    manifest_path="${GENERATED_DIR}/${manifest_name}.yaml"
    log "Applying ${manifest_name}."
    kubectl apply -f "${manifest_path}"
  done

  log "Applying the generated fully controlled client pod manifest."
  kubectl apply -f "${CLIENT_MANIFEST_PATH}"
}

deploy_rolling_base_resources() {
  cleanup_existing_namespace

  log "Applying namespace manifest."
  kubectl apply -f "${GENERATED_DIR}/namespace.yaml"
  RESOURCES_DEPLOYED=1

  log "Applying the generated fully controlled client pod manifest."
  kubectl apply -f "${CLIENT_MANIFEST_PATH}"
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

wait_for_readiness() {
  local manifest_name expected_count

  for manifest_name in "${CONDITION_MANIFESTS[@]}"; do
    expected_count="$(condition_expected_pods "${manifest_name}")"
    wait_for_condition_ready "${manifest_name}" "${expected_count}"
  done

  wait_for_client_ready
}

run_full_benchmark() {
  local benchmark_exit_code

  log "Running the in-cluster fully controlled benchmark with --run-analysis."
  set +e
  kubectl exec -n "${NAMESPACE}" "${CLIENT_POD_NAME}" -- \
    python run_k8s_experiment.py --config "${CONFIG_REL}" --run-analysis 2>&1 | tee "${BENCHMARK_LOG_PATH}"
  benchmark_exit_code=${PIPESTATUS[0]}
  set -e

  (( benchmark_exit_code == 0 )) || die "Benchmark command failed with exit code ${benchmark_exit_code}"
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

parse_results_dir_from_log() {
  local log_path="$1"
  local parsed_path

  parsed_path="$(sed -n 's/^.*Benchmark artifacts directory: //p' "${log_path}" | tail -n 1)"
  if [[ -z "${parsed_path}" ]]; then
    parsed_path="$(sed -n 's/^.*Results directory: //p' "${log_path}" | tail -n 1)"
  fi

  [[ -n "${parsed_path}" ]] || die "Unable to locate the pod-local results directory in ${log_path}"
  printf '%s\n' "${parsed_path}"
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

export_results() {
  POD_RESULTS_DIR="$(parse_results_dir_from_log "${BENCHMARK_LOG_PATH}")"
  log "Copying results from pod path ${POD_RESULTS_DIR}."
  kubectl exec -n "${NAMESPACE}" "${CLIENT_POD_NAME}" -- test -d "${POD_RESULTS_DIR}" || die "Results directory does not exist in the client pod: ${POD_RESULTS_DIR}"
  copy_results_with_fallback "${POD_RESULTS_DIR}" "${HOST_EXPORT_DIR}/$(basename "${POD_RESULTS_DIR}")"
  FINAL_RESULTS_DIR="${HOST_EXPORT_DIR}/$(basename "${POD_RESULTS_DIR}")"
  log "Export completed: ${HOST_EXPORT_DIR}"
}

collect_and_inject_pod_metadata() {
  local condition_name="$1"
  # Pod labels use the raw condition name (underscores preserved — label values allow underscores)
  local meta_file_in_pod="/tmp/rq14_pod_metadata_${condition_name}.json"

  log "Collecting pod metadata for ${condition_name} via kubectl on the host."

  # Build a JSON array of service pod records using kubectl (runs on host).
  # Use -o json + Python parsing to avoid jsonpath dot-notation issues with
  # hyphenated label keys like 'segment-index'.
  local services_json
  services_json="$(
    "${PYTHON_BIN}" - "${NAMESPACE}" "${condition_name}" <<'PY'
import json
import subprocess
import sys

namespace, condition_name = sys.argv[1], sys.argv[2]

raw = subprocess.check_output(
    [
        "kubectl", "get", "pods",
        "-n", namespace,
        "-l", f"condition={condition_name}",
        "-o", "json",
    ],
    text=True,
    stderr=subprocess.DEVNULL,
    timeout=15,
)
pod_list = json.loads(raw)

records = []
for item in pod_list.get("items", []):
    labels = item.get("metadata", {}).get("labels", {})
    spec = item.get("spec", {})
    status = item.get("status", {})
    records.append({
        "pod_name": item.get("metadata", {}).get("name", "unknown"),
        "node_name": spec.get("nodeName", "unknown"),
        "pod_ip": status.get("podIP", "unknown"),
        "segment_index": labels.get("segment-index", "unknown"),
    })

print(json.dumps(records))
PY
  )" || { warn "kubectl pod query failed for ${condition_name}"; return 1; }

  # Inject the JSON file into the benchmark-client pod
  kubectl exec -n "${NAMESPACE}" "${CLIENT_POD_NAME}" -- \
    python3 -c "
import json, sys
data = json.loads(sys.argv[1])
with open('${meta_file_in_pod}', 'w') as f:
    json.dump(data, f)
" "${services_json}" || { warn "Failed to write pod metadata into client pod"; return 1; }

  log "Pod metadata for ${condition_name} injected into pod at ${meta_file_in_pod}."
}

run_condition_benchmark() {
  local condition_name="$1"
  local benchmark_exit_code
  local condition_log_path="${HOST_BENCHMARK_LOG_DIR}/${condition_name}.log"
  local pod_output_dir="${POD_PARTIAL_RESULTS_ROOT}/${condition_name}"
  local host_condition_results_dir="${HOST_PARTIAL_RESULTS_DIR}/${condition_name}"

  # Collect service pod metadata from the host (where kubectl works) and
  # inject it into the client pod as a JSON file before starting the benchmark.
  collect_and_inject_pod_metadata "${condition_name}" || \
    warn "Could not inject pod metadata for ${condition_name}; provenance fields will be 'unknown'."

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

if environment is None:
    environment = {}
environment["rolling_orchestration"] = {
    "enabled": True,
    "conditions": conditions,
    "partial_results_root": os.path.abspath(partial_root),
}

with open(os.path.join(merged_dir, "environment.json"), "w", encoding="utf-8") as handle:
    json.dump(environment, handle, indent=2)

with open(os.path.join(merged_dir, "parity_validation.json"), "w", encoding="utf-8") as handle:
    json.dump({
        "local_validation": local_validation,
        "grpc_validation": grpc_validation,
    }, handle, indent=2)

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

  mkdir -p "${HOST_PARTIAL_RESULTS_DIR}" "${HOST_BENCHMARK_LOG_DIR}"

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
  kubectl get pods -n kube-system -o wide > "${DIAGNOSTICS_DIR}/kubectl_get_kube_system_pods.txt" 2>&1 || true
  kubectl get svc -n kube-system > "${DIAGNOSTICS_DIR}/kubectl_get_kube_system_svc.txt" 2>&1 || true

  local pod_names pod_name
  pod_names="$(kubectl get pods -n "${NAMESPACE}" -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' 2>/dev/null || true)"
  while IFS= read -r pod_name; do
    [[ -n "${pod_name}" ]] || continue
    kubectl describe pod -n "${NAMESPACE}" "${pod_name}" > "${DIAGNOSTICS_DIR}/${pod_name}.describe.txt" || true
    kubectl logs -n "${NAMESPACE}" "${pod_name}" --tail=200 > "${DIAGNOSTICS_DIR}/${pod_name}.log.txt" 2>&1 || true
  done <<< "${pod_names}"

  local kube_system_selector selector_safe kube_pod_names kube_pod_name
  for kube_system_selector in "k8s-app=kube-dns" "k8s-app=kube-proxy"; do
    selector_safe="${kube_system_selector//=/_}"
    kube_pod_names="$(kubectl get pods -n kube-system -l "${kube_system_selector}" -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' 2>/dev/null || true)"
    while IFS= read -r kube_pod_name; do
      [[ -n "${kube_pod_name}" ]] || continue
      kubectl describe pod -n kube-system "${kube_pod_name}" > "${DIAGNOSTICS_DIR}/${selector_safe}_${kube_pod_name}.describe.txt" 2>&1 || true
      kubectl logs -n kube-system "${kube_pod_name}" --tail=200 > "${DIAGNOSTICS_DIR}/${selector_safe}_${kube_pod_name}.log.txt" 2>&1 || true
    done <<< "${kube_pod_names}"
  done
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

prune_image_if_requested() {
  if (( PRUNE_IMAGE )); then
    log "Removing Docker image ${IMAGE_TAG}."
    docker image rm "${IMAGE_TAG}"
  fi
}

main() {
  parse_args "$@"
  cd "${REPO_ROOT}"

  preflight
  capacity_preflight
  prepare_artifact_dirs
  prepare_host_cpu_controls
  build_image
  load_image_if_needed
  generate_manifests
  validate_generated_manifests
  render_client_manifest

  if (( ROLLING_MODE )); then
    run_rolling_benchmark
  else
    deploy_full_resources
    wait_for_readiness
    run_full_benchmark
    export_results
  fi

  cleanup_cluster
  prune_image_if_requested

  if [[ -n "${FINAL_RESULTS_DIR}" ]]; then
    log "RQ1.4 fully controlled run finished successfully. Final results directory: ${FINAL_RESULTS_DIR}"
  else
    log "RQ1.4 fully controlled run finished successfully. Exported artifacts: ${HOST_EXPORT_DIR}"
  fi
}

main "$@"

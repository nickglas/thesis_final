# k8s/base/

Canonical Kubernetes manifests for RQ1.4 chain experiments.

## Structure

- `generated/` — Auto-generated per-condition manifests (from `generate_manifests.py`)
- `client-pod.yaml` — Client pod template for running the benchmark inside the cluster

## Generation

```bash
python k8s/generate_manifests.py --config configs/rq1/1.4/rq1_4_smoke_test.yaml --all
```

This produces `generated/namespace.yaml` and one YAML per configured condition
containing all Deployment + Service resources needed.

Shared values such as namespace, service naming template, gRPC port, max
message sizing, thread settings, image, and image pull policy can be sourced
from the experiment config via `--config`.

## Usage

```bash
# Apply namespace
kubectl apply -f k8s/base/generated/namespace.yaml

# Deploy a condition
kubectl apply -f k8s/base/generated/chain_3svc.yaml

# Run client pod (interactive)
kubectl apply -f k8s/base/client-pod.yaml
kubectl exec -it -n rq14 benchmark-client -- python run_k8s_experiment.py --config configs/rq1/1.4/...
```

If you rebuild the local `thesis-inference:latest` image and reuse the same
tag, restart the `rq14` deployments and recreate `benchmark-client` before
running the benchmark. `kubectl apply` alone does not replace already-running
pods in that case.

## Readiness

The generated pod `readinessProbe` is TCP-level only on the configured gRPC
port. Actual serving readiness is enforced by the runtime path:

- `K8sBenchmarkRunner` checks full-chain gRPC readiness for every service
- live parity validation runs before measurement starts

## Overlays

- `k8s/local/` — Local cluster overrides (image pull policy, resource sizing)
- `k8s/aks/` — AKS-specific overrides (added for RQ1.5)

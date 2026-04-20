# k8s/local/

Local cluster (Docker Desktop, kind, minikube) overrides and helpers.

## Files

- `smoke_test.py` — Automated smoke test: deploys, validates, and tears down
- Overlay patches can be added here (e.g., resource limits for local clusters)

## Recommended smoke run

```bash
python k8s/local/smoke_test.py --config configs/rq1/1.4/rq1_4_smoke_test.yaml
```

The smoke path derives shared K8s values from the experiment config and tests
the monolithic K8s baseline plus one chain condition before a larger run.

## Refreshing local images

If you rebuild the mutable `thesis-inference:latest` tag, `kubectl apply`
alone will not refresh pods that are already running in `rq14`. Rebuild the
image, verify that `kubectl` is pointed at the same local cluster where `rq14`
was deployed, load it into the cluster only when needed, then restart the
workloads.

```bash
kubectl config current-context

docker build -t thesis-inference:latest .

# Docker Desktop: no extra image-load step

# kind only
kind load docker-image thesis-inference:latest

# minikube only
minikube image load thesis-inference:latest

kubectl rollout restart deployment -n rq14 --all
kubectl delete pod -n rq14 benchmark-client --ignore-not-found
kubectl apply -f k8s/base/client-pod.yaml
```

For the current Linux/WSL test workflow, run these commands from WSL and make
sure `kubectl config current-context` matches the local cluster you deployed
`rq14` into. If the context is `docker-desktop`, `minikube image load` does
not affect the active cluster.

## Prerequisites

- A local Kubernetes cluster with `kubectl` configured
- Docker image `thesis-inference:latest` built and accessible
  (for Docker Desktop: `docker build -t thesis-inference:latest .` from repo root)
- Python environment with project dependencies installed

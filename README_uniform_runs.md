# Uniform Experiment Runs

Run these commands from the repository root.

Use WSL bash or another bash shell for the commands below. The wrapper and
the experiment runners are Python/bash based; no PowerShell wrapper is needed.

Do not prefix the full experiment command with `sudo`. The Azure CLI, Docker,
Terraform, and kubeconfig state are tied to your normal user account. CPU
governor, turbo, and priority controls elevate only the narrow sysfs/renice
operations that need privileges. If you want to avoid a password prompt during
the first local benchmark, run this once before starting:

```bash
sudo -v
```

## Full fresh thesis run with one image

This is the canonical "act like we have nothing" command. It creates the
resource group/ACR when needed, builds one `thesis-inference` image, pushes it
to ACR, resolves the immutable digest, and then runs every default thesis stage
with that same pinned image:

- `rq1_1`
- `rq1_2`
- `rq1_3`
- `rq1_4`
- `rq1_4b`
- `rq1_5`
- `rq1_5b`
- `rq2_1_paired`
- `rq2_1_mtls_split`
- `rq2_1_ablation`
- `rq2_2`

```bash
python scripts/run_uniform_image_experiments.py \
  --build-push-image \
  --create-acr \
  --acr-name thesisrq15acr \
  --acr-resource-group rg-thesis-rq15 \
  --acr-location swedencentral \
  --destroy-cloud-on-success \
  --destroy-cloud-on-failure
```

If `thesisrq15acr` already exists and you only want to build/push a new image
into it, omit `--create-acr`.

To inspect the generated plan without spending Azure money:

```bash
python scripts/run_uniform_image_experiments.py \
  --build-push-image \
  --create-acr \
  --acr-name thesisrq15acr \
  --acr-resource-group rg-thesis-rq15 \
  --acr-location swedencentral \
  --destroy-cloud-on-success \
  --destroy-cloud-on-failure \
  --dry-run
```

The wrapper prints the resolved pinned image reference in this form:

```text
<acr>.azurecr.io/thesis-inference@sha256:<digest>
```

That digest is the image identity used for all container-backed stages.

## Login and service checks

### 1. Python environment

```bash
cd /mnt/c/Users/Nick/Desktop/opus
source .venv/bin/activate
python --version
pip install -r requirements.txt
```

### 2. Azure CLI

```bash
az login
az account show -o table
```

If the wrong subscription is selected:

```bash
az account set --subscription "<subscription-name-or-id>"
az account show -o table
```

One-time provider registration for a fresh subscription:

```bash
az provider register --namespace Microsoft.ContainerService
az provider register --namespace Microsoft.ContainerRegistry
az provider register --namespace Microsoft.Compute
az provider register --namespace Microsoft.Network
```

### 3. Docker and ACR

Start Docker Desktop and enable WSL integration for the distro you are using.
Then check Docker from bash:

```bash
docker info
```

The wrapper runs `az acr login --name thesisrq15acr` automatically after the ACR
exists. To test registry login manually:

```bash
az acr login --name thesisrq15acr
```

Optional, only if Docker Hub rate limits base-image pulls:

```bash
docker login
```

### 4. Terraform and Kubernetes tools

Terraform uses the Azure CLI login above, so there is no separate Terraform
cloud login for these local runs.

```bash
terraform version
kubectl version --client
kubelogin --version
```

The AKS runners refresh kubeconfig with `az aks get-credentials` after
provisioning. The RQ1.4/RQ1.4b local Kubernetes stages use `kind`; if it is not
on `PATH`, the wrapper downloads a repo-local binary under `.tools/bin`.

## What is directly comparable

Use only these thesis-facing configs for direct comparison:

- `configs/rq1/1.1/rq1_1_fully_controlled.yaml`
- `configs/rq1/1.2/rq1_2_fully_controlled.yaml`
- `configs/rq1/1.4/rq1_4_fully_controlled.yaml`
- `configs/rq1/1.5/rq1_5_full.yaml`

`python scripts/check_uniform_configs.py` confirms that these four configs share the same core measurement contract:

- ResNet-18 on CPU, FP32, input shape `[1, 3, 224, 224]`
- `5` rounds, `50` warmup iterations, `200` measured iterations, `5` second cooldown, seed `42`
- warmup calibration window `10`, CV threshold `0.02`
- parity validation with `5` inputs at `1e-5`
- single-threaded CPU stabilisation across PyTorch, OMP, MKL, and OpenBLAS

## What is not directly comparable

Do not mix these into the thesis-facing comparison set:

- `*_experimental.yaml`
- `*_threaded.yaml`
- `*_smoke*.yaml`
- `configs/internal_timing/timing_full.yaml`

Internal timing is exploratory, not part of the thesis-facing split benchmark family.

## Important RQ1.5 caveat

RQ1.5 is comparable to RQ1.4 by design, but not identical at the host-control level. The current AKS full config intentionally differs in these ways:

- governor and turbo controls are disabled on AKS managed nodes
- service pod memory is `1Gi` instead of `512Mi`
- the benchmark client pod is `500m` CPU instead of `1` full CPU
- image pull policy is `Always` and the image must be pinned by digest

## Check first

```bash
python scripts/check_uniform_configs.py
```

## Canonical start commands

### RQ1.1 fully controlled

```bash
python run_experiment.py --config configs/rq1/1.1/rq1_1_fully_controlled.yaml --run-analysis
```

### RQ1.2 fully controlled

```bash
python run_experiment.py --config configs/rq1/1.2/rq1_2_fully_controlled.yaml --run-analysis
```

### RQ1.4 fully controlled

Run this from WSL or another bash shell:

```bash
bash scripts/run_rq14_fully_controlled.sh
```

### RQ1.5 fully controlled on an existing AKS cluster

```bash
python scripts/run_rq15_fully_controlled.py
```

### RQ1.5 fully controlled with fresh AKS provisioning and a fresh pinned image

```bash
python scripts/run_rq15_fully_controlled.py --provision --push --build --acr-name <your-acr-name>
```

## Optional exploratory run

This is useful for interpretation, but it is not part of the directly comparable thesis run set:

```bash
python run_internal_timing.py --config configs/internal_timing/timing_full.yaml --run-analysis
```

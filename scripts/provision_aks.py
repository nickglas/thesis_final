"""Provision Azure resources for RQ1.5 AKS experiment.

Creates the resource group, ACR, and AKS cluster required to run RQ1.5.
Wraps `az` CLI commands. Requires the Azure CLI to be installed and logged in
(`az login`) before running.

Usage examples:
    # Step 1: Create resource group
    python scripts/provision_aks.py group \\
        --resource-group rg-thesis-rq15 \\
        --location westeurope

    # Step 2: Create ACR
    python scripts/provision_aks.py acr \\
        --resource-group rg-thesis-rq15 \\
        --acr-name thesisrq15acr \\
        --location westeurope

    # Step 3: Create AKS cluster (Standard_D8s_v5 preferred for 5-svc headroom)
    python scripts/provision_aks.py cluster \\
        --resource-group rg-thesis-rq15 \\
        --cluster-name thesis-rq15 \\
        --nodepool-name rq15pool \\
        --node-count 1 \\
        --node-vm-size Standard_D8s_v5 \\
        --acr-name thesisrq15acr

    # Step 4: Get kubeconfig credentials
    python scripts/provision_aks.py credentials \\
        --resource-group rg-thesis-rq15 \\
        --cluster-name thesis-rq15

    # Or run all steps in sequence:
    python scripts/provision_aks.py all \\
        --resource-group rg-thesis-rq15 \\
        --location westeurope \\
        --acr-name thesisrq15acr \\
        --cluster-name thesis-rq15 \\
        --nodepool-name rq15pool \\
        --node-count 1 \\
        --node-vm-size Standard_D8s_v5

Notes:
    - Use Standard_D8s_v5 (8 vCPU) if budget allows — avoids CPU overcommit
      when running all 5 service pods on the same node.
    - Standard_D4s_v5 (4 vCPU) is the minimum acceptable SKU.
    - Do NOT use Spot/preemptible nodes — preemption invalidates results.
    - Do NOT use Burstable (B-series) VMs — CPU credits introduce variance.
    - The ACR attach step grants AKS the AcrPull role on the registry.
    - Delete the cluster after results are collected to stop charges:
        az aks delete --name thesis-rq15 --resource-group rg-thesis-rq15
"""

import argparse
import subprocess
import sys


def _run(args: list[str], dry_run: bool = False) -> int:
    """Run an az CLI command. Returns the exit code."""
    cmd_str = " ".join(args)
    print(f"  $ {cmd_str}")
    if dry_run:
        print("  [dry-run: not executed]")
        return 0
    result = subprocess.run(args)
    return result.returncode


def _require_az():
    """Check that the az CLI is available."""
    result = subprocess.run(
        ["az", "--version"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        print("ERROR: 'az' CLI not found. Install the Azure CLI and run 'az login'.")
        sys.exit(1)


def cmd_group(args):
    print(f"\n[1/4] Creating resource group: {args.resource_group}")
    rc = _run([
        "az", "group", "create",
        "--name", args.resource_group,
        "--location", args.location,
    ], args.dry_run)
    if rc != 0:
        print("ERROR: Resource group creation failed.")
        sys.exit(rc)
    print("Resource group ready.")


def cmd_acr(args):
    print(f"\n[2/4] Creating ACR: {args.acr_name}")
    rc = _run([
        "az", "acr", "create",
        "--resource-group", args.resource_group,
        "--name", args.acr_name,
        "--sku", "Basic",
        "--location", args.location,
    ], args.dry_run)
    if rc != 0:
        print("ERROR: ACR creation failed.")
        sys.exit(rc)
    print("ACR ready.")


def cmd_cluster(args):
    print(f"\n[3/4] Creating AKS cluster: {args.cluster_name}")
    print(
        f"  node SKU      : {args.node_vm_size}\n"
        f"  node count    : {args.node_count}\n"
        f"  nodepool name : {args.nodepool_name}\n"
        f"  ACR attach    : {args.acr_name}"
    )
    _check_sku(args.node_vm_size)
    rc = _run([
        "az", "aks", "create",
        "--resource-group", args.resource_group,
        "--name", args.cluster_name,
        "--node-count", str(args.node_count),
        "--node-vm-size", args.node_vm_size,
        "--nodepool-name", args.nodepool_name,
        "--attach-acr", args.acr_name,
        "--generate-ssh-keys",
    ], args.dry_run)
    if rc != 0:
        print("ERROR: AKS cluster creation failed.")
        sys.exit(rc)
    print("AKS cluster ready.")


def cmd_credentials(args):
    print(f"\n[4/4] Fetching kubeconfig credentials for: {args.cluster_name}")
    rc = _run([
        "az", "aks", "get-credentials",
        "--resource-group", args.resource_group,
        "--name", args.cluster_name,
        "--overwrite-existing",
    ], args.dry_run)
    if rc != 0:
        print("ERROR: Credentials fetch failed.")
        sys.exit(rc)
    print("Kubeconfig updated.")
    if not args.dry_run:
        print("\nVerify cluster connectivity:")
        _run(["kubectl", "get", "nodes"])


def cmd_all(args):
    """Run all provisioning steps in sequence."""
    cmd_group(args)
    cmd_acr(args)
    cmd_cluster(args)
    cmd_credentials(args)
    print("\nAll provisioning steps complete.")
    print(
        f"\nNext step — push the thesis image to ACR:\n"
        f"  python scripts/push_acr.py \\\n"
        f"    --acr {args.acr_name} \\\n"
        f"    --tag rq15-v1\n"
        f"\nThen generate AKS manifests:\n"
        f"  python k8s/aks/generate_aks_manifests.py \\\n"
        f"    --acr-image {args.acr_name}.azurecr.io/thesis-inference:rq15-v1 \\\n"
        f"    --namespace rq15\n"
    )


def _check_sku(sku: str):
    """Warn if the SKU is unsuitable for the RQ1.5 experiment."""
    sku_lower = sku.lower()
    if sku_lower.startswith("standard_b"):
        print(
            "WARNING: Burstable B-series VMs use CPU credits and introduce "
            "performance variance. Use Standard_D4s_v5 or Standard_D8s_v5."
        )
    if "spot" in sku_lower:
        print(
            "WARNING: Spot/preemptible instances can be evicted during the "
            "experiment. Use on-demand nodes only."
        )


def _add_common_args(parser):
    parser.add_argument("--resource-group", required=True,
                        help="Azure resource group name (e.g. rg-thesis-rq15)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print commands without executing them")


def main():
    parser = argparse.ArgumentParser(
        description="Provision Azure resources for RQ1.5 AKS experiment"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # group
    p_group = sub.add_parser("group", help="Create resource group")
    _add_common_args(p_group)
    p_group.add_argument("--location", default="westeurope",
                         help="Azure region (default: westeurope)")

    # acr
    p_acr = sub.add_parser("acr", help="Create Azure Container Registry")
    _add_common_args(p_acr)
    p_acr.add_argument("--acr-name", required=True,
                       help="ACR name (globally unique, alphanumeric only)")
    p_acr.add_argument("--location", default="westeurope",
                       help="Azure region (default: westeurope)")

    # cluster
    p_cluster = sub.add_parser("cluster", help="Create AKS cluster")
    _add_common_args(p_cluster)
    p_cluster.add_argument("--cluster-name", required=True,
                           help="AKS cluster name (e.g. thesis-rq15)")
    p_cluster.add_argument("--acr-name", required=True,
                           help="ACR name to attach (grants AcrPull role)")
    p_cluster.add_argument("--nodepool-name", default="rq15pool",
                           help="Node pool name (default: rq15pool)")
    p_cluster.add_argument("--node-count", type=int, default=1,
                           help="Number of nodes (default: 1)")
    p_cluster.add_argument(
        "--node-vm-size", default="Standard_D8s_v5",
        help=(
            "VM SKU (default: Standard_D8s_v5 — preferred for 5-svc headroom). "
            "Standard_D4s_v5 is the minimum. Do not use Spot or B-series."
        ),
    )

    # credentials
    p_creds = sub.add_parser("credentials", help="Fetch AKS kubeconfig")
    _add_common_args(p_creds)
    p_creds.add_argument("--cluster-name", required=True,
                         help="AKS cluster name")

    # all
    p_all = sub.add_parser("all", help="Run all provisioning steps in sequence")
    _add_common_args(p_all)
    p_all.add_argument("--location", default="westeurope",
                       help="Azure region (default: westeurope)")
    p_all.add_argument("--acr-name", required=True,
                       help="ACR name (globally unique, alphanumeric only)")
    p_all.add_argument("--cluster-name", required=True,
                       help="AKS cluster name (e.g. thesis-rq15)")
    p_all.add_argument("--nodepool-name", default="rq15pool",
                       help="Node pool name (default: rq15pool)")
    p_all.add_argument("--node-count", type=int, default=1,
                       help="Number of nodes (default: 1)")
    p_all.add_argument(
        "--node-vm-size", default="Standard_D8s_v5",
        help="VM SKU (default: Standard_D8s_v5)",
    )

    args = parser.parse_args()

    _require_az()

    dispatch = {
        "group": cmd_group,
        "acr": cmd_acr,
        "cluster": cmd_cluster,
        "credentials": cmd_credentials,
        "all": cmd_all,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()

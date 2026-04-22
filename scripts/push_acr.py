"""Build, tag, and push the thesis inference image to Azure Container Registry.

Wraps `docker` and `az` CLI commands. Requires:
  - Docker installed and the Docker daemon running.
  - Azure CLI installed and logged in (`az login`).
  - ACR must already exist (create with `python scripts/provision_aks.py acr`).

Usage examples:
    # Log in to ACR and push (builds image first if --build is set):
    python scripts/push_acr.py \\
        --acr thesisrq15acr \\
        --tag rq15-v1 \\
        [--build] \\
        [--print-digest]

    # Push only (image must already be built locally as thesis-inference:latest):
    python scripts/push_acr.py \\
        --acr thesisrq15acr \\
        --tag rq15-v1 \\
        --print-digest

    # Dry run (print commands only):
    python scripts/push_acr.py \\
        --acr thesisrq15acr \\
        --tag rq15-v1 \\
        --dry-run

After pushing, record the digest in configs/rq1/1.5/rq1_5_full.yaml and
regenerate AKS manifests:
    python k8s/aks/generate_aks_manifests.py \\
        --acr-image <acr>.azurecr.io/thesis-inference@sha256:<digest> \\
        --namespace rq15

Reproducibility requirement:
    The thesis-facing run MUST use a pinned digest reference, not a mutable tag.
    The --print-digest flag outputs the digest to stdout for recording.
"""

import argparse
import json
import subprocess
import sys


def _run(args: list[str], dry_run: bool = False, capture: bool = False):
    """Run a shell command. Returns (returncode, stdout) if capture=True."""
    cmd_str = " ".join(args)
    print(f"  $ {cmd_str}")
    if dry_run:
        print("  [dry-run: not executed]")
        return 0, ""
    if capture:
        result = subprocess.run(args, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        return result.returncode, result.stdout.strip()
    else:
        result = subprocess.run(args)
        return result.returncode, ""


def _require_docker():
    result = subprocess.run(
        ["docker", "info"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        print("ERROR: Docker daemon not running or 'docker' not found.")
        sys.exit(1)


def _require_az():
    result = subprocess.run(
        ["az", "--version"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        print("ERROR: 'az' CLI not found. Install the Azure CLI and run 'az login'.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Push thesis inference image to Azure Container Registry"
    )
    parser.add_argument(
        "--acr", required=True,
        help="ACR name (without .azurecr.io suffix), e.g. thesisrq15acr",
    )
    parser.add_argument(
        "--tag", required=True,
        help="Image tag to push, e.g. rq15-v1",
    )
    parser.add_argument(
        "--local-image", default="thesis-inference:latest",
        help="Local Docker image to tag and push (default: thesis-inference:latest)",
    )
    parser.add_argument(
        "--build", action="store_true",
        help=(
            "Build the local image from the Dockerfile before pushing. "
            "If not set, the image must already exist locally."
        ),
    )
    parser.add_argument(
        "--print-digest", action="store_true",
        help=(
            "After push, query the ACR for the content-addressable digest and "
            "print it. Use this value to pin the image in configs and manifests."
        ),
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print commands without executing them",
    )
    args = parser.parse_args()

    _require_docker()
    _require_az()

    acr_registry = f"{args.acr}.azurecr.io"
    remote_image = f"{acr_registry}/thesis-inference:{args.tag}"

    # Step 1: Build local image (optional)
    if args.build:
        print("\n[1/4] Building local image...")
        rc, _ = _run(["docker", "build", "-t", args.local_image, "."], args.dry_run)
        if rc != 0:
            print("ERROR: Docker build failed.")
            sys.exit(rc)
    else:
        print(f"\n[1/4] Skipping build — using existing local image: {args.local_image}")

    # Step 2: Log in to ACR
    print(f"\n[2/4] Logging in to ACR: {acr_registry}")
    rc, _ = _run(["az", "acr", "login", "--name", args.acr], args.dry_run)
    if rc != 0:
        print("ERROR: ACR login failed.")
        sys.exit(rc)

    # Step 3: Tag and push
    print(f"\n[3/4] Tagging: {args.local_image} -> {remote_image}")
    rc, _ = _run(["docker", "tag", args.local_image, remote_image], args.dry_run)
    if rc != 0:
        print("ERROR: Docker tag failed.")
        sys.exit(rc)

    print(f"\n[4/4] Pushing: {remote_image}")
    rc, _ = _run(["docker", "push", remote_image], args.dry_run)
    if rc != 0:
        print("ERROR: Docker push failed.")
        sys.exit(rc)

    print(f"\nImage pushed: {remote_image}")

    # Step 5: Print pinned digest (optional but strongly recommended)
    if args.print_digest:
        print(f"\nQuerying content-addressable digest from ACR...")
        rc, raw = _run(
            [
                "az", "acr", "repository", "show",
                "--name", args.acr,
                "--image", f"thesis-inference:{args.tag}",
                "--query", "digest",
                "--output", "tsv",
            ],
            args.dry_run,
            capture=True,
        )
        if rc != 0:
            print("WARNING: Could not retrieve digest. Check ACR permissions.")
        else:
            digest = raw.strip().strip('"')
            pinned_ref = f"{acr_registry}/thesis-inference@{digest}"
            print(f"\nPinned image reference (use in configs and manifests):")
            print(f"  {pinned_ref}")
            print(
                f"\nUpdate configs/rq1/1.5/rq1_5_full.yaml:\n"
                f"  kubernetes.image: \"{pinned_ref}\"\n"
                f"\nRegenerate AKS manifests:\n"
                f"  python k8s/aks/generate_aks_manifests.py \\\n"
                f"    --acr-image \"{pinned_ref}\" \\\n"
                f"    --namespace rq15\n"
            )
    else:
        print(
            f"\nTip: run with --print-digest to get the content-addressable "
            f"digest for thesis-facing pinning."
        )


if __name__ == "__main__":
    main()

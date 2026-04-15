"""CPU-behaviour stabilisation for reproducible benchmarking.

Applies environment-aware controls to reduce run-to-run variance:
  1. Fixed PyTorch thread counts (intra-op and inter-op)
  2. CPU affinity / core pinning for the benchmark process
  3. Process priority elevation (nice)
  4. ASLR detection and reporting

These controls follow recommendations from:
  - Beyer, Löwe & Wendler, "Reliable benchmarking: requirements and solutions",
    STTT 2019, doi:10.1007/s10009-017-0469-y
  - LLVM Benchmarking Tips, https://llvm.org/docs/Benchmarking.html
  - PyTorch CPU threading docs,
    https://pytorch.org/docs/stable/notes/cpu_threading_torchscript_inference.html
  - Cui & Pericas, "Characterizing and Mitigating Performance Variability
    in Parallel Applications on Modern HPC multicore Systems", ICS 2025

Only controls that are actually available in the current environment are
applied; unavailable controls (e.g. CPU frequency governor on WSL2) are
reported as skipped rather than faked.
"""

import os
import logging
import platform
from typing import Dict, Any, List, Optional

import torch

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Physical core detection (avoids SMT siblings)
# ---------------------------------------------------------------------------

def _detect_physical_cores() -> Optional[List[int]]:
    """Return one logical CPU per physical core, preferring the first sibling.

    On Linux, reads /sys/devices/system/cpu/cpuN/topology/core_id to group
    logical CPUs by physical core, then picks the lowest-numbered logical
    CPU from each group.  Returns None if topology info is unavailable.
    """
    cores: Dict[int, List[int]] = {}
    try:
        available = sorted(os.sched_getaffinity(0))
    except OSError:
        return None

    for cpu in available:
        core_id_path = f"/sys/devices/system/cpu/cpu{cpu}/topology/core_id"
        if not os.path.exists(core_id_path):
            return None
        with open(core_id_path) as f:
            core_id = int(f.read().strip())
        cores.setdefault(core_id, []).append(cpu)

    # One representative per physical core (lowest logical id)
    physical = sorted(min(cpus) for cpus in cores.values())
    return physical


def _detect_aslr() -> Optional[str]:
    """Detect ASLR setting on Linux (0=off, 1=conservative, 2=full)."""
    path = "/proc/sys/kernel/randomize_va_space"
    if os.path.exists(path):
        try:
            with open(path) as f:
                return f.read().strip()
        except OSError:
            return None
    return None


# ---------------------------------------------------------------------------
# Main stabilisation entry point
# ---------------------------------------------------------------------------

def apply_cpu_stabilisation(
    torch_threads: int = 4,
    pin_to_physical_cores: bool = True,
) -> Dict[str, Any]:
    """Apply CPU-behaviour stabilisation and return a metadata dict.

    Parameters
    ----------
    torch_threads : int
        Number of PyTorch intra-op threads.  Should match the number of
        pinned cores for best stability.  Also sets OMP_NUM_THREADS and
        MKL_NUM_THREADS via environment variables.
    pin_to_physical_cores : bool
        If True, restrict the process to one logical CPU per physical core
        (avoiding SMT siblings).  Falls back gracefully if topology info
        is unavailable.

    Returns
    -------
    dict
        Metadata describing all applied (and skipped) controls, suitable
        for inclusion in environment.json.
    """
    meta: Dict[str, Any] = {}

    # ---- 1. PyTorch thread settings ----
    # Fix intra-op threads (used by ATen parallel ops)
    torch.set_num_threads(torch_threads)
    # Fix inter-op threads (graph parallelism); set to 1 for sequential
    # operator execution which is most reproducible for single-input inference
    torch.set_num_interop_threads(1)

    # Also set environment variables so that any child processes or
    # underlying BLAS/OpenMP libraries respect the same thread count.
    os.environ["OMP_NUM_THREADS"] = str(torch_threads)
    os.environ["MKL_NUM_THREADS"] = str(torch_threads)
    os.environ["OPENBLAS_NUM_THREADS"] = str(torch_threads)

    meta["torch_num_threads"] = torch.get_num_threads()
    meta["torch_num_interop_threads"] = torch.get_num_interop_threads()
    meta["omp_num_threads"] = os.environ.get("OMP_NUM_THREADS")
    logger.info(
        f"PyTorch threads: intra-op={torch.get_num_threads()}, "
        f"inter-op={torch.get_num_interop_threads()}"
    )

    # ---- 2. CPU affinity / core pinning ----
    if pin_to_physical_cores:
        physical = _detect_physical_cores()
        if physical is not None:
            # Pin to the requested number of physical cores
            pin_set = physical[:torch_threads] if len(physical) >= torch_threads else physical
            try:
                os.sched_setaffinity(0, pin_set)
                actual = sorted(os.sched_getaffinity(0))
                meta["cpu_affinity_applied"] = True
                meta["cpu_affinity_cores"] = actual
                meta["cpu_affinity_method"] = "os.sched_setaffinity (physical cores only, SMT siblings excluded)"
                logger.info(f"CPU affinity pinned to physical cores: {actual}")
            except OSError as e:
                meta["cpu_affinity_applied"] = False
                meta["cpu_affinity_error"] = str(e)
                logger.warning(f"Could not set CPU affinity: {e}")
        else:
            meta["cpu_affinity_applied"] = False
            meta["cpu_affinity_error"] = "Topology info unavailable; cannot identify physical cores"
            logger.warning("CPU topology info unavailable; skipping core pinning")
    else:
        meta["cpu_affinity_applied"] = False
        meta["cpu_affinity_error"] = "Disabled by configuration"

    # ---- 3. Process priority ----
    try:
        current_nice = os.nice(0)
        if current_nice == 0:
            # Try to raise priority slightly (lower nice = higher priority)
            try:
                os.nice(-5)
                meta["process_nice"] = os.nice(0)
                meta["process_nice_applied"] = True
                logger.info(f"Process nice set to {meta['process_nice']}")
            except PermissionError:
                meta["process_nice"] = current_nice
                meta["process_nice_applied"] = False
                meta["process_nice_error"] = "Insufficient privileges for nice(-5)"
                logger.info("Cannot raise process priority (no root); running at default nice=0")
        else:
            meta["process_nice"] = current_nice
            meta["process_nice_applied"] = False
    except OSError:
        meta["process_nice_applied"] = False
        meta["process_nice_error"] = "os.nice not available"

    # ---- 4. CPU frequency governor ----
    governor_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
    if os.path.exists(governor_path):
        try:
            with open(governor_path) as f:
                meta["cpu_governor"] = f.read().strip()
            meta["cpu_governor_note"] = "Detected but not modified (requires root)"
        except OSError:
            meta["cpu_governor"] = "unreadable"
    else:
        meta["cpu_governor"] = "unavailable"
        meta["cpu_governor_note"] = (
            "cpufreq sysfs not exposed (expected on WSL2/Hyper-V). "
            "CPU frequency is managed by the Windows host."
        )
    logger.info(f"CPU governor: {meta['cpu_governor']}")

    # ---- 5. Turbo boost ----
    turbo_paths = [
        "/sys/devices/system/cpu/intel_pstate/no_turbo",
        "/sys/devices/system/cpu/cpufreq/boost",
    ]
    meta["turbo_boost_control"] = "unavailable"
    for tp in turbo_paths:
        if os.path.exists(tp):
            try:
                with open(tp) as f:
                    meta["turbo_boost_control"] = f"detected at {tp}: {f.read().strip()}"
            except OSError:
                pass
            break
    if meta["turbo_boost_control"] == "unavailable":
        meta["turbo_boost_note"] = (
            "Turbo boost sysfs not exposed (expected on WSL2/Hyper-V). "
            "Boost behaviour is controlled by Windows power plan on the host."
        )
    logger.info(f"Turbo boost: {meta['turbo_boost_control']}")

    # ---- 6. ASLR status ----
    aslr = _detect_aslr()
    meta["aslr_randomize_va_space"] = aslr if aslr is not None else "unreadable"
    if aslr is not None:
        labels = {"0": "disabled", "1": "conservative", "2": "full"}
        logger.info(f"ASLR: {labels.get(aslr, aslr)}")

    # ---- 7. Platform summary ----
    meta["stabilisation_applied"] = True
    meta["platform_is_wsl2"] = "microsoft" in platform.release().lower()

    return meta

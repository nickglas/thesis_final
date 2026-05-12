"""CPU-behaviour stabilisation for reproducible benchmarking.

Applies environment-aware controls to reduce run-to-run variance:
  1. Fixed thread counts (PyTorch, OMP, MKL, OpenBLAS)
  2. CPU affinity / core pinning for the benchmark process
  3. Process priority elevation (nice)
  4. CPU frequency governor control (Linux only, requires root)
  5. Turbo boost control (Linux only, requires root)
  6. ASLR detection and reporting

All controls are driven by the CpuStabilisationConfig dataclass,
which is populated from the cpu_stabilisation section of the YAML config.

These controls follow recommendations from:
  - Beyer, Löwe & Wendler, "Reliable benchmarking: requirements and solutions",
    STTT 2019, doi:10.1007/s10009-017-0469-y
  - LLVM Benchmarking Tips, https://llvm.org/docs/Benchmarking.html
  - PyTorch CPU threading docs,
    https://pytorch.org/docs/stable/notes/cpu_threading_torchscript_inference.html
  - Cui & Pericas, "Characterizing and Mitigating Performance Variability
    in Parallel Applications on Modern HPC multicore Systems", ICS 2025

Only controls that are actually available in the current environment are
applied; unavailable controls are reported as skipped rather than faked.

Metadata records:
  - requested: what the config asked for
  - detected: what the environment supports
  - applied: what was actually set
  - error: why a requested setting could not be applied (if applicable)
"""

import os
import glob
import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

import torch

from src.benchmark.config import CpuStabilisationConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PrivilegedCommandResult:
    """Result for a privileged operation that may use sudo as a narrow helper."""

    error: Optional[str]
    method: str


def _is_effective_root() -> bool:
    return hasattr(os, "geteuid") and os.geteuid() == 0


def _sudo_command_base() -> Optional[List[str]]:
    """Return a sudo prefix, or None if sudo should not be attempted.

    CPU controls are the only operations that should need elevation. The
    experiment orchestrators should keep running as the normal user so CLIs
    such as az, docker, kubectl, and terraform use the user's credentials.
    """
    if _is_effective_root():
        return None
    if os.environ.get("OPUS_CPU_STABILISATION_SUDO", "1").lower() in {"0", "false", "no"}:
        return None
    sudo = shutil.which("sudo")
    if sudo is None:
        return None
    command = [sudo]
    if not sys.stdin.isatty():
        command.append("-n")
    return command


def _sudo_failure_hint() -> str:
    if sys.stdin.isatty():
        return "sudo helper failed"
    return "sudo helper failed; no interactive terminal was available, so run sudo -v first or use a terminal"


def _summarise_methods(methods: List[str]) -> str:
    unique = sorted(set(methods))
    return unique[0] if len(unique) == 1 else "+".join(unique)


# ---------------------------------------------------------------------------
# Physical core detection (avoids SMT siblings)
# ---------------------------------------------------------------------------

def _detect_physical_cores() -> Optional[List[int]]:s/run_uniform_image_experiments.py <your params>
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


def _read_sysfs(path: str) -> Optional[str]:
    """Read a single-line sysfs value, or return None."""
    if os.path.exists(path):
        try:
            with open(path) as f:
                return f.read().strip()
        except OSError:
            return None
    return None


def _write_sysfs(path: str, value: str) -> PrivilegedCommandResult:
    """Write a value to a sysfs file, using sudo only for this write if needed."""
    try:
        with open(path, "w") as f:
            f.write(value)
        return PrivilegedCommandResult(error=None, method="direct")
    except PermissionError as exc:
        sudo_base = _sudo_command_base()
        if sudo_base is None:
            if _is_effective_root():
                error = (
                    f"Permission denied writing to {path} ({exc}); running as "
                    "root was not enough, so the host/container likely does not "
                    "expose this sysfs control as writable"
                )
            else:
                error = (
                    f"Permission denied writing to {path} ({exc}); "
                    "run the experiment as your normal user and allow the CPU "
                    "stabilisation helper to use sudo, or pre-authenticate with sudo -v"
                )
            return PrivilegedCommandResult(
                error=error,
                method="failed",
            )

        # Pass value/path as positional parameters so the shell never has to
        # interpolate untrusted text into the script itself.
        command = [
            *sudo_base,
            "sh",
            "-c",
            'printf "%s" "$1" > "$2"',
            "sh",
            value,
            path,
        ]
        completed = subprocess.run(command, stdout=subprocess.DEVNULL)
        if completed.returncode == 0:
            return PrivilegedCommandResult(error=None, method="sudo")
        return PrivilegedCommandResult(
            error=(
                f"Permission denied writing to {path}; "
                f"{_sudo_failure_hint()} with exit code {completed.returncode}"
            ),
            method="failed",
        )
    except OSError as e:
        return PrivilegedCommandResult(error=f"OS error writing to {path}: {e}", method="failed")


def _get_process_nice() -> Optional[int]:
    try:
        if hasattr(os, "getpriority") and hasattr(os, "PRIO_PROCESS"):
            return int(os.getpriority(os.PRIO_PROCESS, 0))
        if hasattr(os, "nice"):
            return int(os.nice(0))
    except OSError:
        return None
    return None


def _set_process_nice(target_nice: int) -> PrivilegedCommandResult:
    """Set the current process nice value, using sudo renice if required."""
    try:
        if hasattr(os, "setpriority") and hasattr(os, "PRIO_PROCESS"):
            os.setpriority(os.PRIO_PROCESS, 0, target_nice)
        elif hasattr(os, "nice"):
            current = _get_process_nice()
            if current is None:
                return PrivilegedCommandResult(
                    error="Cannot determine current nice value",
                    method="failed",
                )
            os.nice(target_nice - current)
        else:
            return PrivilegedCommandResult(
                error="process priority APIs are not available on this platform",
                method="failed",
            )
        return PrivilegedCommandResult(error=None, method="direct")
    except PermissionError as exc:
        sudo_base = _sudo_command_base()
        if sudo_base is None:
            if _is_effective_root():
                error = (
                    f"Insufficient privileges for nice={target_nice} ({exc}); "
                    "running as root was not enough, so CAP_SYS_NICE may be "
                    "missing in this environment"
                )
            else:
                error = (
                    f"Insufficient privileges for nice={target_nice} ({exc}); "
                    "run the experiment as your normal user and allow the CPU "
                    "stabilisation helper to use sudo, or pre-authenticate with sudo -v"
                )
            return PrivilegedCommandResult(
                error=error,
                method="failed",
            )
        command = [
            *sudo_base,
            "renice",
            "-n",
            str(target_nice),
            "-p",
            str(os.getpid()),
        ]
        completed = subprocess.run(command, stdout=subprocess.DEVNULL)
        if completed.returncode == 0:
            return PrivilegedCommandResult(error=None, method="sudo")
        return PrivilegedCommandResult(
            error=(
                f"sudo renice to {target_nice} failed with exit code "
                f"{completed.returncode}; {_sudo_failure_hint()}"
            ),
            method="failed",
        )
    except OSError as exc:
        return PrivilegedCommandResult(
            error=f"OS error setting nice={target_nice}: {exc}",
            method="failed",
        )


# ---------------------------------------------------------------------------
# Main stabilisation entry point
# ---------------------------------------------------------------------------

def apply_cpu_stabilisation(cfg: CpuStabilisationConfig) -> Dict[str, Any]:
    """Apply CPU-behaviour stabilisation and return a metadata dict.

    Parameters
    ----------
    cfg : CpuStabilisationConfig
        Configuration from the YAML cpu_stabilisation section.

    Returns
    -------
    dict
        Metadata describing all requested, detected, and applied controls,
        suitable for inclusion in environment.json.
    """
    meta: Dict[str, Any] = {}

    # ---- 1. Threading ----
    meta["threading"] = _apply_threading(cfg.threading)

    # ---- 2. CPU affinity ----
    meta["affinity"] = _apply_affinity(cfg.affinity)

    # ---- 3. Process priority ----
    meta["priority"] = _apply_priority(cfg.priority)

    # ---- 4. CPU governor ----
    meta["governor"] = _apply_governor(cfg.governor)

    # ---- 5. Turbo boost ----
    meta["turbo"] = _apply_turbo(cfg.turbo)

    # ---- 6. ASLR (detect only) ----
    aslr = _detect_aslr()
    meta["aslr"] = {
        "detected": aslr,
        "note": "Detection only; disabling requires root and has negligible impact on wall-clock inference latency.",
    }

    return meta


# ---------------------------------------------------------------------------
# Individual control implementations
# ---------------------------------------------------------------------------

def _apply_threading(cfg) -> Dict[str, Any]:
    """Apply thread-count settings to PyTorch and environment variables."""
    torch.set_num_threads(cfg.pytorch_intra_op)
    torch.set_num_interop_threads(cfg.pytorch_inter_op)

    os.environ["OMP_NUM_THREADS"] = str(cfg.omp_num_threads)
    os.environ["MKL_NUM_THREADS"] = str(cfg.mkl_num_threads)
    os.environ["OPENBLAS_NUM_THREADS"] = str(cfg.openblas_num_threads)

    result = {
        "requested": {
            "pytorch_intra_op": cfg.pytorch_intra_op,
            "pytorch_inter_op": cfg.pytorch_inter_op,
            "omp_num_threads": cfg.omp_num_threads,
            "mkl_num_threads": cfg.mkl_num_threads,
            "openblas_num_threads": cfg.openblas_num_threads,
        },
        "applied": {
            "pytorch_intra_op": torch.get_num_threads(),
            "pytorch_inter_op": torch.get_num_interop_threads(),
            "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
            "mkl_num_threads": os.environ.get("MKL_NUM_THREADS"),
            "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
        },
    }

    logger.info(
        f"Threading: intra-op={torch.get_num_threads()}, "
        f"inter-op={torch.get_num_interop_threads()}, "
        f"OMP={cfg.omp_num_threads}, MKL={cfg.mkl_num_threads}, "
        f"OpenBLAS={cfg.openblas_num_threads}"
    )
    return result


def _apply_affinity(cfg) -> Dict[str, Any]:
    """Apply CPU affinity / core pinning."""
    result: Dict[str, Any] = {
        "requested": {
            "enabled": cfg.enabled,
            "num_cores": cfg.num_cores,
            "avoid_smt": cfg.avoid_smt,
            "explicit_cpus": cfg.explicit_cpus,
        },
    }

    if not cfg.enabled:
        result["applied"] = False
        result["reason"] = "Disabled by configuration"
        logger.info("CPU affinity: disabled by configuration")
        return result

    # Determine the pin set
    if cfg.explicit_cpus is not None:
        pin_set = cfg.explicit_cpus
        method = "explicit_cpus from configuration"
    else:
        physical = _detect_physical_cores()
        if physical is not None and cfg.avoid_smt:
            # Pick from physical cores only
            pin_set = physical[:cfg.num_cores] if len(physical) >= cfg.num_cores else physical
            method = f"auto-detected physical cores (SMT excluded), first {cfg.num_cores}"
        elif physical is not None:
            # All logical CPUs available, just take the first N
            try:
                all_cpus = sorted(os.sched_getaffinity(0))
            except OSError:
                all_cpus = list(range(os.cpu_count() or 1))
            pin_set = all_cpus[:cfg.num_cores]
            method = f"first {cfg.num_cores} logical CPUs (SMT not avoided)"
        else:
            result["applied"] = False
            result["detected"] = "Topology info unavailable; cannot identify physical cores"
            result["error"] = "Cannot determine core topology; affinity not applied"
            logger.warning("CPU topology info unavailable; skipping core pinning")
            return result

    result["detected"] = {
        "physical_cores_available": _detect_physical_cores(),
        "total_cpus": os.cpu_count(),
    }

    try:
        os.sched_setaffinity(0, pin_set)
        actual = sorted(os.sched_getaffinity(0))
        result["applied"] = True
        result["applied_cores"] = actual
        result["method"] = method
        logger.info(f"CPU affinity pinned to cores: {actual} ({method})")
    except (OSError, AttributeError) as e:
        result["applied"] = False
        result["error"] = str(e)
        logger.warning(f"Could not set CPU affinity: {e}")

    return result


def _apply_priority(cfg) -> Dict[str, Any]:
    """Apply process priority (nice) adjustment."""
    result: Dict[str, Any] = {
        "requested": {
            "enabled": cfg.enabled,
            "nice_value": cfg.nice_value,
        },
    }

    if not cfg.enabled:
        result["applied"] = False
        result["reason"] = "Disabled by configuration"
        logger.info("Process priority adjustment: disabled by configuration")
        return result

    current_nice = _get_process_nice()
    if current_nice is None:
        result["applied"] = False
        result["error"] = "process priority APIs are not available on this platform"
        logger.info("Process priority APIs not available; skipping priority adjustment")
        return result

    result["detected"] = {"current_nice": current_nice}
    set_result = _set_process_nice(cfg.nice_value)
    final_nice = _get_process_nice()
    if set_result.error is None:
        result["applied"] = True
        result["applied_nice"] = final_nice
        result["method"] = set_result.method
        logger.info(f"Process nice adjusted to {final_nice} ({set_result.method})")
    else:
        result["applied"] = False
        result["applied_nice"] = final_nice if final_nice is not None else current_nice
        result["error"] = set_result.error
        logger.info(
            f"Cannot set nice={cfg.nice_value}; "
            f"running at nice={result['applied_nice']} ({set_result.error})"
        )

    return result


def _apply_governor(cfg) -> Dict[str, Any]:
    """Detect and optionally set CPU frequency governor."""
    result: Dict[str, Any] = {
        "requested": {
            "set_governor": cfg.set_governor,
            "requested_mode": cfg.requested_mode,
        },
    }

    governor_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
    current = _read_sysfs(governor_path)

    if current is not None:
        result["detected"] = current
    else:
        result["detected"] = "unavailable"
        result["note"] = (
            "cpufreq sysfs not exposed (expected on WSL2/Hyper-V or non-Linux). "
            "CPU frequency is managed by the host OS."
        )
        if cfg.set_governor:
            result["applied"] = False
            result["error"] = "Governor sysfs not available; cannot set governor"
            logger.warning(
                f"Governor requested='{cfg.requested_mode}' but cpufreq sysfs "
                "is not available; skipping"
            )
        else:
            result["applied"] = False
            result["reason"] = "Not requested and sysfs unavailable"
        logger.info(f"CPU governor: unavailable")
        return result

    logger.info(f"CPU governor detected: {current}")

    if not cfg.set_governor:
        result["applied"] = False
        result["reason"] = "Not requested by configuration"
        return result

    # Attempt to set governor on all CPU cores
    governor_paths = glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor")
    if not governor_paths:
        result["applied"] = False
        result["error"] = "No governor sysfs paths found"
        return result

    errors = []
    methods = []
    for gp in sorted(governor_paths):
        write_result = _write_sysfs(gp, cfg.requested_mode)
        methods.append(write_result.method)
        if write_result.error:
            errors.append(write_result.error)

    if errors:
        result["applied"] = False
        result["error"] = errors[0]  # Report first error (usually all identical)
        result["method"] = _summarise_methods(methods)
        logger.warning(f"Could not set governor to '{cfg.requested_mode}': {errors[0]}")
    else:
        # Verify
        new_governor = _read_sysfs(governor_path)
        result["applied"] = True
        result["applied_mode"] = new_governor
        result["method"] = _summarise_methods(methods)
        logger.info(f"CPU governor set to '{new_governor}' on {len(governor_paths)} cores")

    return result


def _apply_turbo(cfg) -> Dict[str, Any]:
    """Detect and optionally disable turbo boost."""
    result: Dict[str, Any] = {
        "requested": {
            "disable_turbo": cfg.disable_turbo,
        },
    }

    # Intel pstate: writing "1" to no_turbo disables turbo
    intel_path = "/sys/devices/system/cpu/intel_pstate/no_turbo"
    # Generic cpufreq: writing "0" to boost disables turbo
    generic_path = "/sys/devices/system/cpu/cpufreq/boost"

    intel_val = _read_sysfs(intel_path)
    generic_val = _read_sysfs(generic_path)

    if intel_val is not None:
        result["detected"] = {
            "interface": "intel_pstate",
            "no_turbo": intel_val,
            "turbo_enabled": intel_val == "0",
        }
        turbo_path = intel_path
        disable_value = "1"
    elif generic_val is not None:
        result["detected"] = {
            "interface": "cpufreq_boost",
            "boost": generic_val,
            "turbo_enabled": generic_val == "1",
        }
        turbo_path = generic_path
        disable_value = "0"
    else:
        result["detected"] = "unavailable"
        result["note"] = (
            "Neither intel_pstate/no_turbo nor cpufreq/boost sysfs entries "
            "are exposed. Turbo behaviour is controlled by the host OS."
        )
        if cfg.disable_turbo:
            result["applied"] = False
            result["error"] = "Turbo boost sysfs not available; cannot disable"
            logger.warning("Turbo disable requested but sysfs not available; skipping")
        else:
            result["applied"] = False
            result["reason"] = "Not requested and sysfs unavailable"
        logger.info("Turbo boost control: unavailable")
        return result

    logger.info(f"Turbo boost detected: {result['detected']}")

    if not cfg.disable_turbo:
        result["applied"] = False
        result["reason"] = "Not requested by configuration"
        return result

    write_result = _write_sysfs(turbo_path, disable_value)
    if write_result.error:
        result["applied"] = False
        result["error"] = write_result.error
        result["method"] = write_result.method
        logger.warning(f"Could not disable turbo boost: {write_result.error}")
    else:
        # Verify
        new_val = _read_sysfs(turbo_path)
        result["applied"] = True
        result["applied_value"] = new_val
        result["method"] = write_result.method
        logger.info(f"Turbo boost disabled (wrote '{disable_value}' to {turbo_path})")

    return result

from types import SimpleNamespace

from src.benchmark import cpu_stabilisation as cpu


def test_sysfs_write_uses_sudo_helper_after_permission_error(monkeypatch):
    def fake_open(*_args, **_kwargs):
        raise PermissionError("denied")

    calls = []

    def fake_run(command, stdout=None):
        calls.append((command, stdout))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(cpu, "open", fake_open, raising=False)
    monkeypatch.setattr(cpu, "_is_effective_root", lambda: False)
    monkeypatch.setattr(cpu.shutil, "which", lambda name: "/usr/bin/sudo" if name == "sudo" else None)
    monkeypatch.setattr(cpu.sys, "stdin", SimpleNamespace(isatty=lambda: False))
    monkeypatch.setattr(cpu.subprocess, "run", fake_run)

    result = cpu._write_sysfs("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor", "performance")

    assert result.error is None
    assert result.method == "sudo"
    assert calls == [
        (
            [
                "/usr/bin/sudo",
                "-n",
                "sh",
                "-c",
                'printf "%s" "$1" > "$2"',
                "sh",
                "performance",
                "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor",
            ],
            cpu.subprocess.DEVNULL,
        )
    ]


def test_set_process_nice_uses_sudo_renice_after_permission_error(monkeypatch):
    def fake_setpriority(*_args):
        raise PermissionError("denied")

    calls = []

    def fake_run(command, stdout=None):
        calls.append((command, stdout))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(cpu.os, "PRIO_PROCESS", 0, raising=False)
    monkeypatch.setattr(cpu.os, "setpriority", fake_setpriority, raising=False)
    monkeypatch.setattr(cpu.os, "getpid", lambda: 12345)
    monkeypatch.setattr(cpu, "_is_effective_root", lambda: False)
    monkeypatch.setattr(cpu.shutil, "which", lambda name: "/usr/bin/sudo" if name == "sudo" else None)
    monkeypatch.setattr(cpu.sys, "stdin", SimpleNamespace(isatty=lambda: False))
    monkeypatch.setattr(cpu.subprocess, "run", fake_run)

    result = cpu._set_process_nice(-5)

    assert result.error is None
    assert result.method == "sudo"
    assert calls == [
        (
            ["/usr/bin/sudo", "-n", "renice", "-n", "-5", "-p", "12345"],
            cpu.subprocess.DEVNULL,
        )
    ]

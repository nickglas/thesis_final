import json
import subprocess
from argparse import Namespace
from pathlib import Path

import pytest

import scripts.run_rq22_confidential as rq22


def default_args(tmp_path: Path, **overrides) -> Namespace:
    values = {
        "config": "configs/rq2/2.2/rq2_2_confidential_amd_sev_snp.yaml",
        "results_root": str(tmp_path),
        "provision": False,
        "provisioner": "terraform",
        "acr_name": "testrq22acr",
        "image_ref": None,
        "push": False,
        "build": False,
        "image_tag": "rq22-test",
        "local_image": "thesis-inference:latest",
        "no_auto_push_missing_image": False,
        "attach_image_acr": True,
        "resource_group": "rg-test",
        "cluster_name": "aks-test",
        "region": "westeurope",
        "system_nodepool": "systempool",
        "system_node_count": 1,
        "system_node_vm_size": "Standard_D2s_v3",
        "service1_nodepool": "r22s1std",
        "service1_confidential_nodepool": "r22s1cvm",
        "service1_size": "Standard_D8as_v5",
        "service2_standard_nodepool": "r22s2std",
        "service2_confidential_nodepool": "r22s2cvm",
        "standard_size": "Standard_D8as_v5",
        "confidential_size": "Standard_DC8as_v5",
        "service2_zone": "1",
        "paired_passes": 1,
        "order_seed": 42,
        "order": "standard-first",
        "client_pod": "benchmark-client",
        "readiness_timeout": None,
        "skip_mesh_enable": False,
        "generate_only": False,
        "preserve_namespaces": False,
        "keep_service2_nodepools": False,
        "destroy_infrastructure_on_success": False,
        "destroy_infrastructure_on_failure": False,
    }
    values.update(overrides)
    return Namespace(**values)


def test_execution_plan_alternates_between_passes(tmp_path: Path):
    runner = rq22.RQ22ConfidentialRunner(default_args(tmp_path, paired_passes=2, order="standard-first"))

    assert runner.execution_plan()["passes"] == [
        {"pass": 1, "order": ["standard", "confidential"]},
        {"pass": 2, "order": ["confidential", "standard"]},
    ]


def test_terraform_vars_provision_only_service1_foundation(tmp_path: Path):
    runner = rq22.RQ22ConfidentialRunner(default_args(tmp_path, provision=True))

    tfvars = runner.terraform_vars()

    assert tfvars["location"] == "westeurope"
    assert tfvars["enable_benchmark_pool"] is True
    assert tfvars["nodepool_name"] == "r22s1std"
    assert tfvars["node_vm_size"] == "Standard_D8as_v5"
    assert tfvars["benchmark_node_taint"] == ""
    assert tfvars["benchmark_node_labels"] == {
        "rq": "2.2",
        "rq22-role": "service1-standard",
    }


@pytest.mark.parametrize(
    "key, expected_condition",
    [
        ("standard", "chain_2svc_mtls_standard"),
        ("confidential", "chain_2svc_mtls_confidential_service2"),
    ],
)
def test_condition_config_filters_single_rq22_condition(tmp_path: Path, key: str, expected_condition: str):
    runner = rq22.RQ22ConfidentialRunner(default_args(tmp_path, image_ref="acr.azurecr.io/app@sha256:abc"))

    config = runner.condition_config(key)

    assert [condition["name"] for condition in config["conditions"]] == [expected_condition]
    assert config["kubernetes"]["image"] == "acr.azurecr.io/app@sha256:abc"
    placement = config["kubernetes"]["placement"]
    assert placement["node_pools"] == {
        "service1_standard": "r22s1std",
        "service1_confidential": "r22s1cvm",
        "service2_standard": "r22s2std",
        "service2_confidential": "r22s2cvm",
    }


def test_full_tee_condition_config_places_both_segments_on_confidential_roles(tmp_path: Path):
    runner = rq22.RQ22ConfidentialRunner(
        default_args(
            tmp_path,
            config="configs/rq2/2.2/rq2_2_full_tee_amd_sev_snp.yaml",
            image_ref="acr.azurecr.io/app@sha256:abc",
        )
    )

    assert runner.tee_scope() == "full_2svc"
    config = runner.condition_config("confidential")

    assert [condition["name"] for condition in config["conditions"]] == ["chain_2svc_mtls_confidential_full"]
    placement = config["kubernetes"]["placement"]
    assert placement["node_pools"]["service1_confidential"] == "r22s1cvm"
    assert placement["node_pools"]["service2_confidential"] == "r22s2cvm"


def test_condition_config_uses_pushed_image_digest(tmp_path: Path):
    runner = rq22.RQ22ConfidentialRunner(default_args(tmp_path))
    runner.effective_pinned_image_ref = "targetacr.azurecr.io/thesis-inference@sha256:123abc"

    config = runner.condition_config("standard")

    assert config["kubernetes"]["image"] == "targetacr.azurecr.io/thesis-inference@sha256:123abc"


def test_attach_image_acr_updates_cluster_when_image_uses_existing_acr(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    runner = rq22.RQ22ConfidentialRunner(
        default_args(
            tmp_path,
            acr_name="newrq22acr",
            image_ref="existingacr.azurecr.io/thesis-inference@sha256:abc",
        )
    )
    commands: list[list[str]] = []

    def fake_run_command(args, **_kwargs):
        commands.append(args)
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(rq22, "run_command", fake_run_command)

    runner.attach_image_acr_if_needed()

    assert commands == [
        [
            "az",
            "aks",
            "update",
            "--resource-group",
            "rg-test",
            "--name",
            "aks-test",
            "--attach-acr",
            "existingacr",
        ]
    ]


def test_provisioned_run_requires_image_push_and_builds_into_target_acr(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = rq22.RQ22ConfidentialRunner(default_args(tmp_path, provision=True, acr_name="targetacr"))
    commands: list[list[str]] = []

    def fake_run_command(args, **_kwargs):
        commands.append(args)
        if args[:5] == ["az", "acr", "repository", "show", "--name"]:
            return subprocess.CompletedProcess(args, 0, stdout="sha256:123abc\n", stderr="")
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(rq22, "run_command", fake_run_command)

    pinned = runner.resolve_image_reference()

    assert pinned == "targetacr.azurecr.io/thesis-inference@sha256:123abc"
    assert ["docker", "build", "-t", "thesis-inference:latest", "."] in commands
    assert ["docker", "push", "targetacr.azurecr.io/thesis-inference:rq22-test"] in commands


def test_no_auto_push_missing_image_fails_before_provision_when_config_acr_is_not_visible(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    runner = rq22.RQ22ConfidentialRunner(default_args(tmp_path, provision=True, no_auto_push_missing_image=True))
    monkeypatch.setattr(
        runner,
        "run_logged",
        lambda *args, **_kwargs: subprocess.CompletedProcess(args[0], 3, stdout="", stderr="registry missing"),
    )

    with pytest.raises(rq22.PipelineError, match="not visible in this subscription"):
        runner.validate_image_plan_before_provision()


def test_failure_during_setup_triggers_destroy_on_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = rq22.RQ22ConfidentialRunner(
        default_args(tmp_path, provision=True, destroy_infrastructure_on_failure=True)
    )
    calls: list[str] = []
    runner.prepare_artifacts()

    monkeypatch.setattr(runner, "validate_approved_plan", lambda: calls.append("validate"))
    monkeypatch.setattr(runner, "validate_image_plan_before_provision", lambda: calls.append("image_plan"))
    monkeypatch.setattr(runner, "verify_prerequisites", lambda: calls.append("prereqs"))
    monkeypatch.setattr(runner, "provision_foundation", lambda: calls.append("provision"))

    def fail_resolve():
        calls.append("resolve")
        raise rq22.PipelineError("image problem")

    monkeypatch.setattr(runner, "resolve_image_reference", fail_resolve)
    monkeypatch.setattr(runner, "destroy_infrastructure", lambda reason: calls.append(f"destroy:{reason}"))

    with pytest.raises(rq22.PipelineError, match="image problem"):
        runner.run()

    assert "destroy:failed RQ2.2 rolling run" in calls
    assert json.loads(runner.summary_path.read_text(encoding="utf-8"))["status"] == "failed"


def test_rolling_service2_adds_and_deletes_standard_then_confidential_pools(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    runner = rq22.RQ22ConfidentialRunner(default_args(tmp_path))
    live_commands: list[list[str]] = []

    def fake_run_command(args, **_kwargs):
        live_commands.append(args)
        if args[:4] == ["az", "aks", "nodepool", "add"]:
            name = args[args.index("--name") + 1]
            size = args[args.index("--node-vm-size") + 1]
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=json.dumps(
                    {
                        "name": name,
                        "vmSize": size,
                        "provisioningState": "Succeeded",
                        "availabilityZones": ["1"],
                        "nodeLabels": {},
                    }
                ),
                stderr="",
            )
        if args[:4] == ["az", "aks", "nodepool", "delete"]:
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
        raise AssertionError(f"unexpected live command: {args}")

    monkeypatch.setattr(rq22, "run_command", fake_run_command)
    monkeypatch.setattr(runner, "generate_manifests", lambda context: context.manifest_dir.mkdir(parents=True, exist_ok=True))
    monkeypatch.setattr(runner, "apply_manifests", lambda context: None)
    monkeypatch.setattr(runner, "wait_for_ready", lambda context: None)
    monkeypatch.setattr(runner, "run_benchmark", lambda context: "/tmp/rq22/fake")
    monkeypatch.setattr(runner, "cleanup_namespaces", lambda context: None)

    standard = runner.run_condition("standard", 1, 1)
    confidential = runner.run_condition("confidential", 1, 2)

    assert standard["status"] == "completed"
    assert confidential["status"] == "completed"
    adds = [args for args in live_commands if args[:4] == ["az", "aks", "nodepool", "add"]]
    deletes = [args for args in live_commands if args[:4] == ["az", "aks", "nodepool", "delete"]]
    assert [args[args.index("--name") + 1] for args in adds] == ["r22s2std", "r22s2cvm"]
    assert [args[args.index("--node-vm-size") + 1] for args in adds] == [
        "Standard_D8as_v5",
        "Standard_DC8as_v5",
    ]
    assert all(args[args.index("--zones") + 1] == "1" for args in adds)
    assert [args[args.index("--name") + 1] for args in deletes] == ["r22s2std", "r22s2cvm"]
    assert all("--yes" not in args for args in deletes)
    confidential_labels = adds[1][adds[1].index("--labels") + 1 : adds[1].index("--output")]
    assert "confidential-compute=amd-sev-snp" in confidential_labels


def test_full_tee_adds_and_deletes_service1_and_service2_confidential_pools(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    runner = rq22.RQ22ConfidentialRunner(
        default_args(tmp_path, config="configs/rq2/2.2/rq2_2_full_tee_amd_sev_snp.yaml")
    )
    live_commands: list[list[str]] = []

    def fake_run_command(args, **_kwargs):
        live_commands.append(args)
        if args[:4] == ["az", "aks", "nodepool", "add"]:
            name = args[args.index("--name") + 1]
            size = args[args.index("--node-vm-size") + 1]
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=json.dumps(
                    {
                        "name": name,
                        "vmSize": size,
                        "provisioningState": "Succeeded",
                        "availabilityZones": ["1"],
                        "nodeLabels": {},
                    }
                ),
                stderr="",
            )
        if args[:4] == ["az", "aks", "nodepool", "delete"]:
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
        raise AssertionError(f"unexpected live command: {args}")

    monkeypatch.setattr(rq22, "run_command", fake_run_command)
    monkeypatch.setattr(runner, "generate_manifests", lambda context: context.manifest_dir.mkdir(parents=True, exist_ok=True))
    monkeypatch.setattr(runner, "apply_manifests", lambda context: None)
    monkeypatch.setattr(runner, "wait_for_ready", lambda context: None)
    monkeypatch.setattr(runner, "run_benchmark", lambda context: "/tmp/rq22/fake")
    monkeypatch.setattr(runner, "cleanup_namespaces", lambda context: None)

    record = runner.run_condition("confidential", 1, 1)

    assert record["status"] == "completed"
    assert record["tee_scope"] == "full_2svc"
    assert record["service1_confidential"] is True
    assert record["service2_confidential"] is True
    adds = [args for args in live_commands if args[:4] == ["az", "aks", "nodepool", "add"]]
    deletes = [args for args in live_commands if args[:4] == ["az", "aks", "nodepool", "delete"]]
    assert [args[args.index("--name") + 1] for args in adds] == ["r22s1cvm", "r22s2cvm"]
    assert [args[args.index("--node-vm-size") + 1] for args in adds] == [
        "Standard_DC8as_v5",
        "Standard_DC8as_v5",
    ]
    assert [args[args.index("--name") + 1] for args in deletes] == ["r22s2cvm", "r22s1cvm"]


def test_parse_rejects_destroy_without_provision(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("sys.argv", ["run_rq22_confidential.py", "--destroy-infrastructure-on-success"])

    with pytest.raises(SystemExit):
        rq22.parse_args()


def test_missing_kubectl_error_includes_wsl_install_hint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = rq22.RQ22ConfidentialRunner(default_args(tmp_path))

    def fake_ensure_command(command_name: str):
        if command_name == "kubectl":
            raise rq22.PipelineError("Required command not found: kubectl")

    monkeypatch.setattr(rq22, "ensure_command", fake_ensure_command)
    monkeypatch.setattr(
        rq22,
        "run_command",
        lambda args, **_kwargs: subprocess.CompletedProcess(args, 0, stdout="", stderr=""),
    )

    with pytest.raises(rq22.PipelineError) as exc_info:
        runner.verify_prerequisites()

    message = str(exc_info.value)
    assert "curl -L -o ~/.local/bin/kubectl" in message
    assert "kubelogin-linux-amd64.zip" in message
    assert "export PATH" in message


def test_verify_prerequisites_does_not_require_host_python(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = rq22.RQ22ConfidentialRunner(default_args(tmp_path))
    checked_commands: list[str] = []

    def fake_ensure_command(command_name: str):
        checked_commands.append(command_name)
        if command_name == "python":
            raise AssertionError("verify_prerequisites should not require a host python command")

    monkeypatch.setattr(rq22, "ensure_command", fake_ensure_command)
    monkeypatch.setattr(
        rq22,
        "run_command",
        lambda args, **_kwargs: subprocess.CompletedProcess(args, 0, stdout="", stderr=""),
    )

    runner.verify_prerequisites()

    assert checked_commands == ["az", "kubectl", "kubelogin"]


def test_verify_prerequisites_requires_terraform_when_provisioning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = rq22.RQ22ConfidentialRunner(default_args(tmp_path, provision=True))
    checked_commands: list[str] = []

    def fake_ensure_command(command_name: str):
        checked_commands.append(command_name)

    monkeypatch.setattr(rq22, "ensure_command", fake_ensure_command)
    monkeypatch.setattr(
        rq22,
        "run_command",
        lambda args, **_kwargs: subprocess.CompletedProcess(args, 0, stdout="", stderr=""),
    )

    runner.verify_prerequisites()

    assert checked_commands[:4] == ["az", "kubectl", "kubelogin", "terraform"]


def test_windows_kubectl_in_wsl_path_gets_actionable_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = rq22.RQ22ConfidentialRunner(default_args(tmp_path))

    monkeypatch.setattr(rq22, "ensure_command", lambda command_name: None)

    def fake_run_command(args, **_kwargs):
        if args[:2] == ["kubectl", "version"]:
            raise OSError("Exec format error")
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(rq22, "run_command", fake_run_command)

    with pytest.raises(rq22.PipelineError) as exc_info:
        runner.verify_prerequisites()

    message = str(exc_info.value)
    assert "not executable in this shell" in message
    assert "rm -f ~/.local/bin/kubectl" in message


def test_docker_info_failure_blocks_image_push_before_provision(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = rq22.RQ22ConfidentialRunner(default_args(tmp_path, provision=True, push=True, build=True))

    monkeypatch.setattr(rq22, "ensure_command", lambda command_name: None)

    def fake_run_command(args, **_kwargs):
        if args == ["docker", "info"]:
            return subprocess.CompletedProcess(args, 1, stdout="", stderr="WSL integration disabled")
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(rq22, "run_command", fake_run_command)

    with pytest.raises(rq22.PipelineError) as exc_info:
        runner.verify_prerequisites()

    message = str(exc_info.value)
    assert "`docker info` failed" in message
    assert "WSL Integration" in message
    assert "WSL integration disabled" in message

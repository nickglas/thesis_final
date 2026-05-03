import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

import scripts.preflight_rq22_confidential as preflight
from src.benchmark.config import load_config


REPO_ROOT = Path(__file__).resolve().parents[1]
RQ22_CONFIG = REPO_ROOT / "configs" / "rq2" / "2.2" / "rq2_2_confidential_amd_sev_snp.yaml"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_variant(tmp_path: Path, mutator) -> Path:
    payload = load_yaml(RQ22_CONFIG)
    mutator(payload)
    path = tmp_path / "rq2_2_variant.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def load_manifest_documents(directory: Path) -> list[dict]:
    docs = []
    for path in sorted(directory.glob("*.yaml")):
        for doc in yaml.safe_load_all(path.read_text(encoding="utf-8")):
            if isinstance(doc, dict):
                docs.append(doc)
    return docs


def matching_deployment(docs: list[dict], condition: str, segment: str) -> dict:
    for doc in docs:
        if doc.get("kind") != "Deployment":
            continue
        labels = (doc.get("metadata") or {}).get("labels") or {}
        if labels.get("condition") == condition and labels.get("segment-index") == segment:
            return doc
    raise AssertionError(f"deployment not found: {condition} segment {segment}")


def node_selector(deployment: dict) -> dict:
    return (((deployment.get("spec") or {}).get("template") or {}).get("spec") or {}).get("nodeSelector") or {}


def deployment_labels(deployment: dict) -> dict:
    return (deployment.get("metadata") or {}).get("labels") or {}


def test_rq22_config_matches_approved_amd_only_gate():
    raw = load_yaml(RQ22_CONFIG)
    checks, errors = preflight.config_hard_gate(raw)

    assert errors == []
    assert checks["region"] == "westeurope"
    assert checks["backend"] == "amd_sev_snp"
    assert checks["standard_size"] == "Standard_D8as_v5"
    assert checks["confidential_size"] == "Standard_DC8as_v5"
    assert checks["standard_quota_family"] == "standardDASv5Family"
    assert checks["confidential_quota_family"] == "standardDCASv5Family"


def test_rq22_config_still_loads_through_base_config_parser():
    config = load_config(str(RQ22_CONFIG))

    assert [condition.name for condition in config.conditions] == [
        "chain_2svc_mtls_standard",
        "chain_2svc_mtls_confidential_service2",
    ]
    assert config.kubernetes is not None
    assert config.kubernetes.namespace == "rq22-chain2-mtls"


@pytest.mark.parametrize(
    "mutator, expected",
    [
        (
            lambda payload: payload["confidential_compute"].update({"backend": "intel_tdx"}),
            "backend",
        ),
        (
            lambda payload: payload["confidential_compute"].update({"confidential_size": "Standard_DC4as_v5"}),
            "confidential_size",
        ),
        (
            lambda payload: payload["confidential_compute"].update({"region": "northeurope"}),
            "region",
        ),
    ],
)
def test_rq22_gate_rejects_non_approved_backend_region_or_sku(tmp_path: Path, mutator, expected: str):
    path = write_variant(tmp_path, mutator)
    _, errors = preflight.config_hard_gate(load_yaml(path))

    assert any(expected in error for error in errors)


def test_rq22_manifest_generation_places_service2_by_condition(tmp_path: Path):
    output_dir = tmp_path / "manifests"
    completed = subprocess.run(
        [
            sys.executable,
            "k8s/aks/generate_aks_manifests.py",
            "--config",
            str(RQ22_CONFIG),
            "--output-dir",
            str(output_dir),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    docs = load_manifest_documents(output_dir)

    standard_svc1 = matching_deployment(docs, "chain_2svc_mtls_standard", "1")
    standard_svc2 = matching_deployment(docs, "chain_2svc_mtls_standard", "2")
    confidential_svc1 = matching_deployment(docs, "chain_2svc_mtls_confidential_service2", "1")
    confidential_svc2 = matching_deployment(docs, "chain_2svc_mtls_confidential_service2", "2")

    assert node_selector(standard_svc1)["agentpool"] == "r22s1std"
    assert node_selector(standard_svc2)["agentpool"] == "r22s2std"
    assert node_selector(confidential_svc1)["agentpool"] == "r22s1std"
    assert node_selector(confidential_svc2)["agentpool"] == "r22s2cvm"

    assert deployment_labels(standard_svc2)["confidential-compute"] == "false"
    assert deployment_labels(standard_svc2)["rq22-vm-size"] == "Standard_D8as_v5"
    assert deployment_labels(confidential_svc2)["confidential-compute"] == "true"
    assert deployment_labels(confidential_svc2)["confidential-backend"] == "amd_sev_snp"
    assert deployment_labels(confidential_svc2)["rq22-vm-size"] == "Standard_DC8as_v5"

    assert "affinity" not in (((standard_svc2.get("spec") or {}).get("template") or {}).get("spec") or {})
    assert "affinity" not in (((confidential_svc2.get("spec") or {}).get("template") or {}).get("spec") or {})

    passed, errors = preflight.validate_generated_manifests(output_dir)
    assert passed, errors


def test_rq22_quota_summary_uses_exact_approved_family_values():
    usages = [
        {"name": {"value": "cores", "localizedValue": "Total Regional vCPUs"}, "currentValue": "0", "limit": "20"},
        {
            "name": {"value": "standardDASv5Family", "localizedValue": "Standard DASv5 Family vCPUs"},
            "currentValue": "0",
            "limit": "16",
        },
        {
            "name": {"value": "standardDCASv5Family", "localizedValue": "Standard DCASv5 Family vCPUs"},
            "currentValue": "0",
            "limit": "16",
        },
    ]

    standard = preflight.usage_summary(preflight.usage_record_by_value(usages, preflight.APPROVED_STANDARD_FAMILY))
    confidential = preflight.usage_summary(preflight.usage_record_by_value(usages, preflight.APPROVED_CONFIDENTIAL_FAMILY))

    assert standard["limit"] == 16
    assert confidential["limit"] == 16


def test_zone_sku_restrictions_warn_but_do_not_block():
    summary = {
        "size": "Standard_D8as_v5",
        "restrictions": [
            {
                "type": "Zone",
                "reasonCode": "NotAvailableForSubscription",
                "restrictionInfo": {"locations": ["westeurope"], "zones": ["3", "2"]},
            }
        ],
    }

    assert preflight.blocking_sku_restrictions(summary) == []
    warnings = preflight.sku_restriction_warnings(summary, "westeurope")
    assert warnings == ["Standard_D8as_v5 has subscription zone restrictions in westeurope: unavailable zones=3, 2"]


def test_hardware_near_records_non_blocking_capability_differences():
    standard = {
        "size": "Standard_D8as_v5",
        "vcpus": "8",
        "memory_gb": "32",
        "hyperv_generations": "V2",
        "broad_family": "das_v5",
        "accelerated_networking": "True",
        "ephemeral_os_disk": "False",
        "disk_controller_types": None,
        "confidential_computing_type": None,
        "zone_availability": {"effective_zones": ["1", "2", "3"]},
        "location_info": [{"location": "westeurope", "zones": ["1", "2", "3"]}],
    }
    confidential = {
        "size": "Standard_DC8as_v5",
        "vcpus": "8",
        "memory_gb": "32",
        "hyperv_generations": "V2",
        "broad_family": "das_v5",
        "accelerated_networking": "False",
        "ephemeral_os_disk": "False",
        "disk_controller_types": None,
        "confidential_computing_type": "SNP",
        "zone_availability": {"effective_zones": ["1"]},
        "location_info": [{"location": "westeurope", "zones": ["1"]}],
    }

    overhead_framing, basis, differences = preflight.hardware_near_assessment(standard, confidential)

    assert overhead_framing == "hardware_near"
    assert basis["vcpus_match"] is True
    assert basis["memory_gb_match"] is True
    assert {difference["capability"] for difference in differences} == {
        "AcceleratedNetworkingEnabled",
        "ConfidentialComputingType",
        "zones/locationInfo",
    }
    assert any("confidential SKU Standard_DC8as_v5 is only available in zone 1" in item["message"] for item in differences)


def test_region_sku_restrictions_block():
    summary = {
        "size": "Standard_D8as_v5",
        "restrictions": [
            {
                "type": "Location",
                "reasonCode": "NotAvailableForSubscription",
                "restrictionInfo": {"locations": ["westeurope"]},
            }
        ],
    }

    assert preflight.blocking_sku_restrictions(summary) == summary["restrictions"]


def test_aks_nodepool_validation_records_create_show_delete(monkeypatch: pytest.MonkeyPatch):
    def fake_run_command(args):
        if args[:4] == ["az", "aks", "nodepool", "add"]:
            return preflight.CommandResult(
                args=args,
                returncode=0,
                stdout=json.dumps({"name": "r22vtest", "vmSize": "Standard_DC8as_v5", "provisioningState": "Succeeded"}),
            )
        if args[:4] == ["az", "aks", "nodepool", "show"]:
            return preflight.CommandResult(
                args=args,
                returncode=0,
                stdout=json.dumps({"name": "r22vtest", "vmSize": "Standard_DC8as_v5", "provisioningState": "Succeeded"}),
            )
        if args[:4] == ["az", "aks", "nodepool", "delete"]:
            return preflight.CommandResult(args=args, returncode=0)
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(preflight, "run_command", fake_run_command)
    commands = []

    status = preflight.validate_aks_nodepool("rg-test", "aks-test", commands)

    assert status["status"] == "passed"
    assert status["requested_vm_size"] == "Standard_DC8as_v5"
    assert status["observed_vm_size"] == "Standard_DC8as_v5"
    assert status["deleted"] is True
    assert [command["args"][:4] for command in commands] == [
        ["az", "aks", "nodepool", "add"],
        ["az", "aks", "nodepool", "show"],
        ["az", "aks", "nodepool", "delete"],
    ]

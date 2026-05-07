from types import SimpleNamespace
import sys
import types

import google.protobuf


class _RuntimeVersionShim:
    Domain = SimpleNamespace(PUBLIC="PUBLIC")

    @staticmethod
    def ValidateProtobufRuntimeVersion(*_args, **_kwargs):
        return None


if not hasattr(google.protobuf, "runtime_version"):
    google.protobuf.runtime_version = _RuntimeVersionShim

chain_client_stub = types.ModuleType("src.client.chain_client")
chain_client_stub.ChainClient = object
sys.modules.setdefault("src.client.chain_client", chain_client_stub)

resnet_splits_stub = types.ModuleType("src.models.resnet_splits")
resnet_splits_stub.get_full_model = lambda *_args, **_kwargs: None
resnet_splits_stub.get_chain_segments = lambda *_args, **_kwargs: []
sys.modules.setdefault("src.models.resnet_splits", resnet_splits_stub)

grpc_target_stub = types.ModuleType("src.grpc_target")
grpc_target_stub.resolve_target_address = lambda address: address
sys.modules.setdefault("src.grpc_target", grpc_target_stub)

from src.benchmark.config import ConditionConfig
from src.benchmark.k8s_runner import K8sBenchmarkRunner


SERVICE_ADDRESSES = [
    ("service-1", "service-1.ns.svc.cluster.local:50051"),
    ("service-2", "service-2.ns.svc.cluster.local:50051"),
    ("service-3", "service-3.ns.svc.cluster.local:50051"),
]


def runner_with_k8s(raw_k8s: dict) -> K8sBenchmarkRunner:
    runner = K8sBenchmarkRunner.__new__(K8sBenchmarkRunner)
    runner.raw_config = {"kubernetes": raw_k8s}
    return runner


def chain_condition() -> ConditionConfig:
    return ConditionConfig(
        name="chain_3svc_test",
        type="chain",
        chain_split_points=["layer1", "layer2"],
    )


def test_readiness_checks_all_services_for_plain_or_mesh_default_conditions():
    plain_runner = runner_with_k8s({"mesh": {"enabled": False}})
    mesh_default_runner = runner_with_k8s({
        "mesh": {
            "enabled": True,
            "peer_authentication": {"enabled": False, "strict_workloads": []},
            "authorization_policy": {"enabled": False},
        }
    })

    assert plain_runner._client_visible_readiness_addresses(chain_condition(), SERVICE_ADDRESSES) == SERVICE_ADDRESSES
    assert mesh_default_runner._client_visible_readiness_addresses(chain_condition(), SERVICE_ADDRESSES) == SERVICE_ADDRESSES


def test_readiness_skips_downstream_services_protected_by_strict_peer_authentication():
    runner = runner_with_k8s({
        "mesh": {
            "enabled": True,
            "peer_authentication": {
                "enabled": True,
                "strict_workloads": [
                    {"segment_index": "2", "mode": "STRICT"},
                    {"segment_index": "3", "mode": "STRICT"},
                ],
            },
            "authorization_policy": {"enabled": False},
        }
    })

    assert runner._client_visible_readiness_addresses(chain_condition(), SERVICE_ADDRESSES) == [
        SERVICE_ADDRESSES[0]
    ]


def test_readiness_skips_downstream_services_protected_by_authorization_policy():
    runner = runner_with_k8s({
        "mesh": {
            "enabled": True,
            "peer_authentication": {"enabled": False, "strict_workloads": []},
            "authorization_policy": {
                "enabled": True,
                "downstream_segment_index": "3",
            },
        }
    })

    assert runner._client_visible_readiness_addresses(chain_condition(), SERVICE_ADDRESSES) == [
        SERVICE_ADDRESSES[0],
        SERVICE_ADDRESSES[1],
    ]

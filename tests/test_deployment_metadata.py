from src.benchmark.deployment_metadata import build_environment_deployment_section


def test_build_environment_deployment_section_derives_required_aks_fields():
    digest = "sha256:" + "a" * 64
    deployment_metadata = {
        "chain_2svc": {
            "namespace": "rq15",
            "cluster_context": "thesis-rq15",
            "cluster_info": "Kubernetes control plane is running at https://thesis-rq15.hcp.swedencentral.azmk8s.io:443",
            "cluster_deployment": {
                "cluster_type": "aks",
                "cluster_version": "v1.31.1",
                "node_count": 1,
                "node_instance_type": "Standard_D8s_v3",
                "azure_region": "swedencentral",
                "cni": "azure-cni",
                "namespace": "rq15",
            },
            "client": {
                "pod_name": "benchmark-client",
                "node_name": "aks-rq15pool-00000000-vmss000000",
                "image": f"thesisrq15acr.azurecr.io/thesis-inference@{digest}",
                "image_id": f"docker-pullable://thesisrq15acr.azurecr.io/thesis-inference@{digest}",
            },
            "services": [
                {
                    "service_name": "chain-2svc-svc-1",
                    "node_name": "aks-rq15pool-00000000-vmss000000",
                    "image": f"thesisrq15acr.azurecr.io/thesis-inference@{digest}",
                    "image_id": f"docker-pullable://thesisrq15acr.azurecr.io/thesis-inference@{digest}",
                },
                {
                    "service_name": "chain-2svc-svc-2",
                    "node_name": "aks-rq15pool-00000000-vmss000000",
                    "image": f"thesisrq15acr.azurecr.io/thesis-inference@{digest}",
                    "image_id": f"docker-pullable://thesisrq15acr.azurecr.io/thesis-inference@{digest}",
                },
            ],
        }
    }

    deployment = build_environment_deployment_section(deployment_metadata)

    assert deployment == {
        "type": "kubernetes",
        "cluster_type": "aks",
        "cluster_version": "v1.31.1",
        "node_count": 1,
        "node_instance_type": "Standard_D8s_v3",
        "azure_region": "swedencentral",
        "cni": "azure-cni",
        "namespace": "rq15",
        "pod_colocation_enforced": True,
        "pod_placement": {
            "benchmark-client": "aks-rq15pool-00000000-vmss000000",
            "chain-2svc-svc-1": "aks-rq15pool-00000000-vmss000000",
            "chain-2svc-svc-2": "aks-rq15pool-00000000-vmss000000",
        },
        "container_image_digest": digest,
        "acr_registry": "thesisrq15acr.azurecr.io",
    }
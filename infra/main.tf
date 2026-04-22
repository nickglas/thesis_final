# RQ1.5 AKS infrastructure — Terraform configuration
#
# Provisions:
#   - Azure Resource Group
#   - Azure Container Registry (Basic SKU)
#   - AKS cluster (single node pool, SystemAssigned identity)
#   - AcrPull role assignment from AKS kubelet identity to ACR
#
# Usage:
#   cd infra/
#   terraform init
#   terraform plan -var="acr_name=thesisrq15acr"
#   terraform apply -var="acr_name=thesisrq15acr"
#
# After apply, fetch kubeconfig:
#   az aks get-credentials \
#     --resource-group $(terraform output -raw resource_group_name) \
#     --name $(terraform output -raw cluster_name) \
#     --overwrite-existing
#
# Tear down after results are collected:
#   terraform destroy -var="acr_name=thesisrq15acr"
#
# See terraform.tfvars.example for variable reference.

terraform {
  required_version = ">= 1.3"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# ---------------------------------------------------------------------------
# Resource Group
# ---------------------------------------------------------------------------

resource "azurerm_resource_group" "rq15" {
  name     = var.resource_group_name
  location = var.location
}

# ---------------------------------------------------------------------------
# Azure Container Registry (Basic tier)
# ACR stores the single thesis-inference image.
# admin_enabled = false — AKS pulls via managed identity (AcrPull role).
# ---------------------------------------------------------------------------

resource "azurerm_container_registry" "rq15" {
  name                = var.acr_name
  resource_group_name = azurerm_resource_group.rq15.name
  location            = azurerm_resource_group.rq15.location
  sku                 = "Basic"
  admin_enabled       = false
}

# ---------------------------------------------------------------------------
# AKS Cluster
#
# Single node pool — all service pods run on the same node via pod affinity.
# SystemAssigned identity is the simplest approach for ACR attachment.
#
# Node SKU guidance (from RQ1.5 design D3):
#   Standard_D8s_v5 (8 vCPU) — preferred; avoids CPU overcommit for 5 svc pods.
#   Standard_D4s_v5 (4 vCPU) — minimum acceptable.
#   Do NOT use Spot or B-series (preemption risk / CPU credit variance).
# ---------------------------------------------------------------------------

resource "azurerm_kubernetes_cluster" "rq15" {
  name                = var.cluster_name
  location            = azurerm_resource_group.rq15.location
  resource_group_name = azurerm_resource_group.rq15.name
  dns_prefix          = var.cluster_name

  # kubernetes_version is omitted — Azure picks the current default stable release.
  # Record the actual version from `kubectl version` in environment.json.

  default_node_pool {
    name       = var.nodepool_name
    node_count = var.node_count
    vm_size    = var.node_vm_size

    # os_disk_type = "Managed" (default) with Premium SSD backing on Ds_v5 SKUs.
    # No auto-scaling — node count is fixed for experiment duration.
    enable_auto_scaling = false
  }

  identity {
    type = "SystemAssigned"
  }

  # Disable features not needed for this experiment.
  # Keeping the cluster footprint minimal reduces noise and cost.
  network_profile {
    network_plugin = "kubenet"
    load_balancer_sku = "standard"
  }

  # Suppress the default monitoring / diagnostics addons that generate
  # background pod traffic.  Not needed for thesis measurements.
  http_application_routing_enabled = false

  tags = {
    project     = "thesis"
    experiment  = "rq15"
    environment = "research"
  }
}

# ---------------------------------------------------------------------------
# ACR Pull permission for AKS
#
# Grants the AKS kubelet managed identity the AcrPull role on the ACR so that
# nodes can pull the thesis-inference image without image pull secrets.
# Equivalent to: az aks update --attach-acr <acr-name>
# ---------------------------------------------------------------------------

resource "azurerm_role_assignment" "aks_acr_pull" {
  scope                = azurerm_container_registry.rq15.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.rq15.kubelet_identity[0].object_id
}

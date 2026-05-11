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

locals {
  experiment_tag                 = var.experiment_tag != "" ? var.experiment_tag : (var.enable_benchmark_pool ? "rq21-isolated" : "rq15")
  acr_lookup_resource_group_name = var.acr_resource_group_name != "" ? var.acr_resource_group_name : var.resource_group_name
}

# ---------------------------------------------------------------------------
# Resource Group
# ---------------------------------------------------------------------------

resource "azurerm_resource_group" "rq15" {
  count    = var.create_resource_group ? 1 : 0
  name     = var.resource_group_name
  location = var.location
}

data "azurerm_resource_group" "existing" {
  count = var.create_resource_group ? 0 : 1
  name  = var.resource_group_name
}

locals {
  resource_group_name     = var.create_resource_group ? azurerm_resource_group.rq15[0].name : data.azurerm_resource_group.existing[0].name
  resource_group_location = var.create_resource_group ? azurerm_resource_group.rq15[0].location : data.azurerm_resource_group.existing[0].location
}

# ---------------------------------------------------------------------------
# Azure Container Registry (Basic tier)
# ACR stores the single thesis-inference image.
# admin_enabled = false — AKS pulls via managed identity (AcrPull role).
# ---------------------------------------------------------------------------

resource "azurerm_container_registry" "rq15" {
  count               = var.create_acr ? 1 : 0
  name                = var.acr_name
  resource_group_name = local.resource_group_name
  location            = local.resource_group_location
  sku                 = "Basic"
  admin_enabled       = false
}

data "azurerm_container_registry" "existing" {
  count               = var.create_acr ? 0 : 1
  name                = var.acr_name
  resource_group_name = local.acr_lookup_resource_group_name
}

locals {
  acr_id           = var.create_acr ? azurerm_container_registry.rq15[0].id : data.azurerm_container_registry.existing[0].id
  acr_name         = var.create_acr ? azurerm_container_registry.rq15[0].name : data.azurerm_container_registry.existing[0].name
  acr_login_server = var.create_acr ? azurerm_container_registry.rq15[0].login_server : data.azurerm_container_registry.existing[0].login_server
}

# ---------------------------------------------------------------------------
# AKS Cluster
#
# Single node pool — all service pods run on the same node via pod affinity.
# RQ2.1 final runs enable a small system pool plus a tainted benchmark pool.
# SystemAssigned identity is the simplest approach for ACR attachment.
#
# Node SKU guidance for current thesis runs:
#   RQ1.5 default: Standard_D8s_v3 x1.
#   RQ2.1 isolated: Standard_D2s_v3 system x1 + Standard_D8s_v3 benchmark x1.
#   This keeps the documented DSv3 target at 10 vCPU total.
#   Do NOT use Spot or B-series (preemption risk / CPU credit variance).
# ---------------------------------------------------------------------------

resource "azurerm_kubernetes_cluster" "rq15" {
  name                = var.cluster_name
  location            = local.resource_group_location
  resource_group_name = local.resource_group_name
  dns_prefix          = var.cluster_name

  # kubernetes_version is omitted — Azure picks the current default stable release.
  # Record the actual version from `kubectl version` in environment.json.

  default_node_pool {
    name       = var.enable_benchmark_pool ? var.system_nodepool_name : var.nodepool_name
    node_count = var.enable_benchmark_pool ? var.system_node_count : var.node_count
    vm_size    = var.enable_benchmark_pool ? var.system_node_vm_size : var.node_vm_size
  }

  identity {
    type = "SystemAssigned"
  }

  # Disable features not needed for this experiment.
  # Keeping the cluster footprint minimal reduces noise and cost.
  network_profile {
    network_plugin    = "kubenet"
    load_balancer_sku = "standard"
  }

  # Suppress the default monitoring / diagnostics addons that generate
  # background pod traffic.  Not needed for thesis measurements.
  http_application_routing_enabled = false

  tags = {
    project     = "thesis"
    experiment  = local.experiment_tag
    environment = "research"
  }
}

resource "azurerm_kubernetes_cluster_node_pool" "benchmark" {
  count = var.enable_benchmark_pool ? 1 : 0

  name                  = var.nodepool_name
  kubernetes_cluster_id = azurerm_kubernetes_cluster.rq15.id
  vm_size               = var.node_vm_size
  node_count            = var.node_count
  mode                  = "User"
  node_taints           = var.benchmark_node_taint != "" ? [var.benchmark_node_taint] : []
  node_labels           = var.benchmark_node_labels

  tags = {
    project     = "thesis"
    experiment  = local.experiment_tag
    environment = "research"
    workload    = "benchmark"
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
  scope                = local.acr_id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.rq15.kubelet_identity[0].object_id
}

variable "resource_group_name" {
  description = "Azure resource group name for all RQ1.5 resources."
  type        = string
  default     = "rg-thesis-rq15"
}

variable "location" {
  description = "Azure region. ACR and AKS must be in the same region to avoid cross-region pull latency."
  type        = string
  default     = "swedencentral"
}

variable "acr_name" {
  description = "Azure Container Registry name. Must be globally unique and alphanumeric only (no hyphens)."
  type        = string
  # No default — must be supplied explicitly because ACR names are globally unique.
}

variable "cluster_name" {
  description = "AKS cluster name."
  type        = string
  default     = "thesis-rq15"
}

variable "nodepool_name" {
  description = "Node pool name. Must match the nodeSelector agentpool label used in k8s/aks/generate_aks_manifests.py."
  type        = string
  default     = "rq15pool"
}

variable "node_count" {
  description = "Number of nodes in the pool. 1 is sufficient when pod affinity enforces same-node colocation."
  type        = number
  default     = 1
}

variable "node_vm_size" {
  description = <<-EOT
    VM SKU for AKS nodes.
    Standard_D8s_v3 (8 vCPU, 32 GiB) — DSv3 family has 10 vCPU quota in swedencentral.
    Standard_D8s_v5 (8 vCPU, 32 GiB) is preferred but DSv5 family has 0 quota on this subscription.
    Do NOT use Spot or B-series (preemption/credit variance violate measurement stability).
  EOT
  type        = string
  default     = "Standard_D8s_v3"
}

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
    VM SKU for the benchmark AKS node pool.
    Standard_D8s_v3 (8 vCPU, 32 GiB) is the thesis-facing SKU; keep this fixed
    across single-node and multi-node sensitivity runs so the per-node CPU
    profile is identical. RQ1.5b multi-node uses 6 of these (48 vCPU total).
    Do NOT use Spot or B-series (preemption/credit variance violate measurement stability).
  EOT
  type        = string
  default     = "Standard_D8s_v3"
}

variable "enable_benchmark_pool" {
  description = "When true, provision a dedicated system pool plus a tainted benchmark pool for final RQ2.1 runs. Leave false for the original RQ1.5 single-pool contract."
  type        = bool
  default     = false
}

variable "system_nodepool_name" {
  description = "System node pool name used when enable_benchmark_pool=true. Must fit AKS node-pool naming limits."
  type        = string
  default     = "systempool"
}

variable "system_node_count" {
  description = "Number of nodes in the small system pool when enable_benchmark_pool=true."
  type        = number
  default     = 1
}

variable "system_node_vm_size" {
  description = "VM SKU for the small system pool. Standard_D2s_v3 x1 plus Standard_D8s_v3 x1 keeps RQ2.1 within the documented 10 DSv3 vCPU quota."
  type        = string
  default     = "Standard_D2s_v3"
}

variable "benchmark_node_taint" {
  description = "Taint applied to the benchmark-only pool so unrelated workloads do not schedule there."
  type        = string
  default     = "workload=benchmark:NoSchedule"
}

variable "benchmark_node_labels" {
  description = "Labels applied to the benchmark/user node pool."
  type        = map(string)
  default = {
    workload = "benchmark"
  }
}

variable "experiment_tag" {
  description = "Tag value used to identify the experiment family. Defaults preserve the original RQ1.5/RQ2.1 behavior."
  type        = string
  default     = ""
}

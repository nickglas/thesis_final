output "resource_group_name" {
  description = "Name of the provisioned resource group."
  value       = azurerm_resource_group.rq15.name
}

output "acr_login_server" {
  description = "ACR login server (use as the image registry prefix)."
  value       = azurerm_container_registry.rq15.login_server
}

output "acr_name" {
  description = "ACR resource name (for az acr login)."
  value       = azurerm_container_registry.rq15.name
}

output "cluster_name" {
  description = "AKS cluster name."
  value       = azurerm_kubernetes_cluster.rq15.name
}

output "node_vm_size" {
  description = "VM SKU used for the benchmark node pool."
  value       = var.node_vm_size
}

output "benchmark_pool_enabled" {
  description = "Whether the RQ2.1 isolated benchmark pool was enabled."
  value       = var.enable_benchmark_pool
}

output "benchmark_nodepool_name" {
  description = "Benchmark node pool name used by generated manifests."
  value       = var.nodepool_name
}

output "benchmark_node_taint" {
  description = "Taint applied to the benchmark-only node pool."
  value       = var.benchmark_node_taint
}

output "system_nodepool_name" {
  description = "System node pool name."
  value       = azurerm_kubernetes_cluster.rq15.default_node_pool[0].name
}

output "system_node_vm_size" {
  description = "VM SKU used for the system node pool."
  value       = azurerm_kubernetes_cluster.rq15.default_node_pool[0].vm_size
}

output "get_credentials_command" {
  description = "Run this command to configure kubectl after apply."
  value       = "az aks get-credentials --resource-group ${azurerm_resource_group.rq15.name} --name ${azurerm_kubernetes_cluster.rq15.name} --overwrite-existing"
}

output "push_image_command" {
  description = "Example push_acr.py invocation using the provisioned ACR."
  value       = "python scripts/push_acr.py --acr ${azurerm_container_registry.rq15.name} --tag rq15-v1 --build --print-digest"
}

output "generate_manifests_command" {
  description = "Example generate_aks_manifests.py invocation (replace TAG with actual tag or digest)."
  value       = "python k8s/aks/generate_aks_manifests.py --acr-image ${azurerm_container_registry.rq15.login_server}/thesis-inference:TAG --namespace rq15 --nodepool ${var.nodepool_name}"
}

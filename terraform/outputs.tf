# 📤 Terraform Outputs for Oracle Cloud Infrastructure

# Cluster Information
output "cluster_id" {
  description = "The OCID of the OKE cluster"
  value       = oci_containerengine_cluster.ai_absence_sow_cluster.id
}

output "cluster_name" {
  description = "The name of the OKE cluster"
  value       = oci_containerengine_cluster.ai_absence_sow_cluster.name
}

output "cluster_kubernetes_version" {
  description = "The Kubernetes version of the cluster"
  value       = oci_containerengine_cluster.ai_absence_sow_cluster.kubernetes_version
}

output "cluster_endpoint" {
  description = "The cluster API server endpoint"
  value       = oci_containerengine_cluster.ai_absence_sow_cluster.endpoints[0].public_endpoint
  sensitive   = true
}

# Network Information
output "vcn_id" {
  description = "The OCID of the VCN"
  value       = oci_core_vcn.ai_absence_sow_vcn.id
}

output "public_subnet_id" {
  description = "The OCID of the public subnet"
  value       = oci_core_subnet.public_subnet.id
}

output "private_subnet_id" {
  description = "The OCID of the private subnet"
  value       = oci_core_subnet.private_subnet.id
}

# Node Pool Information
output "node_pool_id" {
  description = "The OCID of the node pool"
  value       = oci_containerengine_node_pool.ai_absence_sow_node_pool.id
}

output "node_pool_kubernetes_version" {
  description = "The Kubernetes version of the node pool"
  value       = oci_containerengine_node_pool.ai_absence_sow_node_pool.kubernetes_version
}

# Load Balancer Information
output "load_balancer_shape" {
  description = "The shape of the load balancer"
  value       = var.load_balancer_shape
}

# Security Information
output "public_security_list_id" {
  description = "The OCID of the public security list"
  value       = oci_core_security_list.public_security_list.id
}

output "private_security_list_id" {
  description = "The OCID of the private security list"
  value       = oci_core_security_list.private_security_list.id
}

# Kubeconfig Command
output "kubeconfig_command" {
  description = "Command to generate kubeconfig"
  value       = "oci ce cluster create-kubeconfig --cluster-id ${oci_containerengine_cluster.ai_absence_sow_cluster.id} --file ~/.kube/config --region ${var.region} --token-version 2.0.0"
}

# Connection Information
output "connection_info" {
  description = "Connection information for the deployed infrastructure"
  value = {
    cluster_id     = oci_containerengine_cluster.ai_absence_sow_cluster.id
    cluster_name   = oci_containerengine_cluster.ai_absence_sow_cluster.name
    region         = var.region
    compartment_id = var.compartment_ocid
    vcn_id         = oci_core_vcn.ai_absence_sow_vcn.id
  }
}

# Cost Information
output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown"
  value = {
    cluster_management = "Free (OKE cluster management)"
    worker_nodes       = "${var.node_pool_size} nodes × ${var.node_ocpus} OCPUs × $0.0464/hour = $${var.node_pool_size * var.node_ocpus * 0.0464 * 24 * 30}"
    load_balancer      = "Flexible LB: ~$18/month"
    storage            = "Block volumes: ~$2-5/month per 50GB"
    bandwidth          = "10TB outbound free, then $0.0085/GB"
  }
}

# Deployment URLs (will be available after ingress setup)
output "application_urls" {
  description = "Application access URLs (available after ingress configuration)"
  value = {
    frontend_service = "http://<load-balancer-ip>"
    backend_api      = "http://<load-balancer-ip>/api"
    health_check     = "http://<load-balancer-ip>/api/health"
    custom_domain    = var.domain_name != "" ? "https://${var.domain_name}" : "Configure domain_name variable"
  }
}
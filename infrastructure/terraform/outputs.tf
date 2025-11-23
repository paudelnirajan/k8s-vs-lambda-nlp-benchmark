output "cluster_endpoint" {
    description = "Endpoint for EKS control plane"
    value = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
    description = "Security group ids attached to the cluster control plane"
    value = module.eks.cluster_security_group_id
}

output "region" {
    description = "AWS region"
    value = var.region
}

output "cluster_name" {
  description = "Kubernetes Cluster Name"
  value       = module.eks.cluster_name
}

output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "aws eks --region ${var.region} update-kubeconfig --name ${module.eks.cluster_name}"
}

output "api_gateway_url" {
  value = "${aws_api_gateway_stage.prod.invoke_url}/predict"
}

output "k8s_load_balancer_hostname" {
  value = kubernetes_service.nlp_service.status.0.load_balancer.0.ingress.0.hostname
}
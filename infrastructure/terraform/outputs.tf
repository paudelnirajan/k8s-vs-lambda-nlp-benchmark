# ============================================
# APPLICATION ENDPOINTS
# ============================================

output "lambda_api_endpoint" {
  description = "Lambda API endpoint (via API Gateway) - for sentiment analysis"
  value       = "${aws_api_gateway_stage.prod.invoke_url}/predict"
}

output "kubernetes_api_endpoint" {
  description = "Kubernetes API endpoint (via ELB) - for sentiment analysis"
  value       = "http://${kubernetes_service.nlp_service.status.0.load_balancer.0.ingress.0.hostname}/predict"
}

output "ec2_frontend_url" {
  description = "EC2 Streamlit Frontend URL"
  value       = "http://${aws_instance.app_server.public_ip}:8501"
}

output "ec2_backend_url" {
  description = "EC2 FastAPI Backend URL"
  value       = "http://${aws_instance.app_server.public_ip}:8000"
}

# ============================================
# EC2 INSTANCE ACCESS
# ============================================

output "ec2_public_ip" {
  description = "EC2 instance public IP address"
  value       = aws_instance.app_server.public_ip
}

output "ssh_command" {
  description = "SSH command to access EC2 instance"
  value       = "ssh -i ${local_file.ssh_key.filename} ubuntu@${aws_instance.app_server.public_ip}"
}

# ============================================
# EKS CLUSTER INFO (for kubectl)
# ============================================

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS control plane endpoint (for kubectl)"
  value       = module.eks.cluster_endpoint
}

output "configure_kubectl_command" {
  description = "Command to configure kubectl for this cluster"
  value       = "aws eks --region ${var.region} update-kubeconfig --name ${module.eks.cluster_name}"
}

# ============================================
# AWS INFO
# ============================================

output "aws_region" {
  description = "AWS region"
  value       = var.region
}

output "eks_security_group_id" {
  description = "Security group ID for EKS cluster"
  value       = module.eks.cluster_security_group_id
}

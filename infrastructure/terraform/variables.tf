variable "region" {
    description = "AWS region"
    type = string
    default = "us-east-1"
}

variable "cluster_name" {
    description = "Name of the EKS cluster"
    type = string
    default = "nlp-sentiment-cluster"
}

variable "github_repo" {
    description = "URL of the github repo to be cloned on EC2 instance"
    type = string
    default = "https://github.com/paudelnirajan/k8s-vs-lambda-nlp-benchmark.git"
}
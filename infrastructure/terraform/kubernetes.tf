resource "kubernetes_deployment" "nlp_deployment" {
  metadata {
    name = "nlp-sentiment-deployment"
    labels = {
      app = "nlp-sentiment"
    }
  }

  spec {
    replicas = 2
    
    selector {
      match_labels = {
        app = "nlp-sentiment"
      }
    }

    template {
      metadata {
        labels = {
          app = "nlp-sentiment"
        }
      }

      spec {
        container {
          image = "${aws_ecr_repository.k8s_repo.repository_url}:latest"
          name  = "nlp-sentiment-container"
          
          image_pull_policy = "Always"

          port {
            container_port = 8000
          }
          
          # 1. Environment Variables
          env {
            name  = "LOG_LEVEL"
            value = "INFO"
          }

          # 2. Readiness Probe
          readiness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 10
            period_seconds        = 5
          }

          # 3. Liveness Probe
          liveness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 15
            period_seconds        = 20
          }

          resources {
            limits = {
              cpu    = "1000m"
              memory = "1Gi"
            }
            requests = {
              cpu    = "500m"
              memory = "512Mi"
            }
          }
        }
      }
    }
  }
  
  depends_on = [aws_ecr_repository.k8s_repo]
}

resource "kubernetes_service" "nlp_service" {
  metadata {
    name = "nlp-sentiment-service"
  }
  spec {
    selector = {
      app = "nlp-sentiment"
    }
    port {
      port        = 80
      target_port = 8000
    }
    type = "LoadBalancer"
  }
}
resource "aws_ecr_repository" "lambda_repo" {
    name = "nlp-sentiment-analysis"
    force_delete = true

    image_scanning_configuration {
        scan_on_push = true
    }
}

resource "aws_ecr_repository" "k8s_repo" {
    name = "nlp-sentiment-k8s"
    force_delete = true

    image_scanning_configuration {
        scan_on_push = true
    }
}

resource "aws_ecr_repository" "backend_repo" {
  name         = "nlp-backend"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "frontend_repo" {
  name         = "nlp-frontend"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }
}
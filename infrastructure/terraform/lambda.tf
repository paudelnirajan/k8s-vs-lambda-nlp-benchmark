# IAM role
resource "aws_iam_role" "lambda_exec" {
  name = "nlp_lambda_exec_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# 2. Lambda function
resource "aws_lambda_function" "sentiment_analyzer" {
  function_name = "nlp_sentiment_analysis"
  role = aws_iam_role.lambda_exec.arn
  package_type = "Image"
  image_uri = "${aws_ecr_repository.lambda_repo.repository_url}:latest"
  timeout = 300
  memory_size = 3008

  depends_on = [ aws_ecr_repository.lambda_repo ]
}

# 3. API Gateway
resource "aws_api_gateway_rest_api" "nlp_api" {
  name = "nlp-sentiment-api"
  description = "NLP Sentiment Analysis API"
}

# --/predict (POST) -- 
resource "aws_api_gateway_resource" "predict" {
  rest_api_id = aws_api_gateway_rest_api.nlp_api.id
  parent_id   = aws_api_gateway_rest_api.nlp_api.root_resource_id
  path_part   = "predict"
}

resource "aws_api_gateway_method" "predict_post" {
  rest_api_id   = aws_api_gateway_rest_api.nlp_api.id
  resource_id   = aws_api_gateway_resource.predict.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "predict_integration" {
  rest_api_id             = aws_api_gateway_rest_api.nlp_api.id
  resource_id             = aws_api_gateway_resource.predict.id
  http_method             = aws_api_gateway_method.predict_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.sentiment_analyzer.invoke_arn
  timeout_milliseconds    = 29000
}

# --- /metrics (GET) ---
resource "aws_api_gateway_resource" "metrics" {
  rest_api_id = aws_api_gateway_rest_api.nlp_api.id
  parent_id   = aws_api_gateway_rest_api.nlp_api.root_resource_id
  path_part   = "metrics"
}

resource "aws_api_gateway_method" "metrics_get" {
  rest_api_id   = aws_api_gateway_rest_api.nlp_api.id
  resource_id   = aws_api_gateway_resource.metrics.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "metrics_integration" {
  rest_api_id             = aws_api_gateway_rest_api.nlp_api.id
  resource_id             = aws_api_gateway_resource.metrics.id
  http_method             = aws_api_gateway_method.metrics_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.sentiment_analyzer.invoke_arn
}

# --- Deployment ---
resource "aws_api_gateway_deployment" "api_deployment" {
  rest_api_id = aws_api_gateway_rest_api.nlp_api.id
  
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.predict.id,
      aws_api_gateway_method.predict_post.id,
      aws_api_gateway_integration.predict_integration.id,
      aws_api_gateway_resource.metrics.id,
      aws_api_gateway_method.metrics_get.id,
      aws_api_gateway_integration.metrics_integration.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "prod" {
  deployment_id = aws_api_gateway_deployment.api_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.nlp_api.id
  stage_name    = "prod"
}

# --- Permissions ---
resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sentiment_analyzer.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.nlp_api.execution_arn}/*/*"
}
#!/bin/bash
set -e

REGION="us-east-1"
FUNCTION_NAME="nlp-sentiment-analysis"
API_NAME="nlp-sentiment-api"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Get function ARN 
FUNCTION_ARN=$(aws lambda get-function --function-name ${FUNCTION_NAME} --region ${REGION} --query 'Configuration.FunctionArn' --output text)

echo "Function ARN: ${FUNCTION_ARN}"

echo "Checking if API '${API_NAME}' already exists..."

# 1. Try to FIND the API ID by its name
API_ID=$(aws apigateway get-rest-apis \
  --query "items[?name=='${API_NAME}'].id" \
  --region ${REGION} \
  --output text)

# 2. Check if the API_ID variable is empty
if [ -z "$API_ID" ]; then
  # 3. IF IT'S EMPTY: Create the API 
  echo "API not found. Creating new API: ${API_NAME}"
  API_ID=$(aws apigateway create-rest-api \
    --name ${API_NAME} \
    --description "NLP Sentiment Analysis API" \
    --region ${REGION} \
    --query 'id' \
    --output text)
else
  # 3. IF IT'S NOT EMPTY
  echo "API already exists. Using API ID: ${API_ID}"
fi

echo "API ID: ${API_ID}"

# Get root resource ID
ROOT_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id ${API_ID} \
  --region ${REGION} \
  --query 'items[?path==`/`].id' \
  --output text)

echo "Checking for /predict resource..."

# 1. Try to FIND the resource
PREDICT_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id ${API_ID} \
  --region ${REGION} \
  --query "items[?path=='/predict'].id" \
  --output text)

# 2. Check if it's empty
if [ -z "$PREDICT_RESOURCE_ID" ]; then
  # 3. IF IT'S EMPTY: Create it
  echo "Creating /predict resource..."
  PREDICT_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id ${API_ID} \
    --parent-id ${ROOT_RESOURCE_ID} \
    --path-part predict \
    --region ${REGION} \
    --query 'id' \
    --output text)
else
  # 3. IF IT'S NOT EMPTY: Use the one we found
  echo "Found existing /predict resource."
fi

echo "Checking for POST method..."
# Check if POST method already exists
EXISTING_METHOD=$(aws apigateway get-method \
  --rest-api-id ${API_ID} \
  --resource-id ${PREDICT_RESOURCE_ID} \
  --http-method POST \
  --region ${REGION} \
  --query 'httpMethod' \
  --output text 2>/dev/null || echo "")

if [ -z "$EXISTING_METHOD" ]; then
  echo "Creating POST method..."
  aws apigateway put-method \
    --rest-api-id ${API_ID} \
    --resource-id ${PREDICT_RESOURCE_ID} \
    --http-method POST \
    --authorization-type NONE \
    --region ${REGION} \
    --output text > /dev/null
else
  echo "POST method already exists. Skipping creation."
fi

echo "Setting up Lambda integration..."
# Check if integration already exists
EXISTING_INTEGRATION=$(aws apigateway get-integration \
  --rest-api-id ${API_ID} \
  --resource-id ${PREDICT_RESOURCE_ID} \
  --http-method POST \
  --region ${REGION} \
  --query 'type' \
  --output text 2>/dev/null || echo "")

if [ -z "$EXISTING_INTEGRATION" ] || [ "$EXISTING_INTEGRATION" != "AWS_PROXY" ]; then
  echo "Creating/updating Lambda integration..."
  aws apigateway put-integration \
    --rest-api-id ${API_ID} \
    --resource-id ${PREDICT_RESOURCE_ID} \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${FUNCTION_ARN}/invocations" \
    --region ${REGION} \
    --output text > /dev/null
  
  # Set timeout to max (29 seconds is hard limit for API Gateway)
  aws apigateway update-integration \
    --rest-api-id ${API_ID} \
    --resource-id ${PREDICT_RESOURCE_ID} \
    --http-method POST \
    --patch-operations op=replace,path=/timeoutInMillis,value=29000 \
    --region ${REGION} \
    --output text > /dev/null 2>&1 || true
else
  echo "Lambda integration already exists. Updating URI..."
  aws apigateway put-integration \
    --rest-api-id ${API_ID} \
    --resource-id ${PREDICT_RESOURCE_ID} \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${FUNCTION_ARN}/invocations" \
    --region ${REGION} \
    --output text > /dev/null
  
  # Set timeout to max (29 seconds is hard limit for API Gateway)
  aws apigateway update-integration \
    --rest-api-id ${API_ID} \
    --resource-id ${PREDICT_RESOURCE_ID} \
    --http-method POST \
    --patch-operations op=replace,path=/timeoutInMillis,value=29000 \
    --region ${REGION} \
    --output text > /dev/null 2>&1 || true
fi

echo "Granting API Gateway permission to invoke Lambda..."
(aws lambda add-permission \
  --function-name ${FUNCTION_NAME} \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/*" \
  --region ${REGION} \
  --output text > /dev/null) || echo "Permission may already exist (this is OK)"

echo "Deploying API..."
# Check if deployment already exists for this stage
EXISTING_DEPLOYMENT=$(aws apigateway get-deployments \
  --rest-api-id ${API_ID} \
  --region ${REGION} \
  --query "items[?stageName=='prod'].id" \
  --output text 2>/dev/null | head -n 1)

if [ -n "$EXISTING_DEPLOYMENT" ]; then
  echo "Updating existing deployment..."
  aws apigateway create-deployment \
    --rest-api-id ${API_ID} \
    --stage-name prod \
    --region ${REGION} \
    --output text > /dev/null
else
  echo "Creating new deployment..."
  aws apigateway create-deployment \
    --rest-api-id ${API_ID} \
    --stage-name prod \
    --region ${REGION} \
    --output text > /dev/null
fi

# Get API endpoint
ENDPOINT="https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/predict"
echo ""
echo "✅ API Gateway setup complete!"
echo "API Endpoint: ${ENDPOINT}"
echo ""
echo "Test with:"
echo "curl -X POST ${ENDPOINT} -H 'Content-Type: application/json' -d '{\"text\": \"I love this!\"}'"
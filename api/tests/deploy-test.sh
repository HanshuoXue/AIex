#!/bin/bash
echo "Deploy to test environment..."

TEST_APP_NAME="api-alex-test-1757506758"
RESOURCE_GROUP="rg-alex"

echo "🔐 Login to ACR..."
az acr login --name alexregistry

# Build multi-architecture Docker image (linux/amd64)
echo "🔨 Build Docker image (linux/amd64)..."
docker buildx build --platform linux/amd64 \
  -t alexregistry.azurecr.io/alex-api-test:latest \
  ./api --push

# Configure App Service to use container
echo "⚙️ Configure App Service container..."
az webapp config container set \
  --name $TEST_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --container-registry-url https://alexregistry.azurecr.io \
  --container-registry-user alexregistry \
  --container-registry-password $(az acr credential show --name alexregistry --query passwords[0].value -o tsv) \
  --docker-custom-image-name alexregistry.azurecr.io/alex-api-test:latest

# az webapp config appsettings set --name $TEST_APP_NAME --resource-group $RESOURCE_GROUP --settings WEBSITES_PORT=8000
# az webapp restart --name $TEST_APP_NAME --resource-group $RESOURCE_GROUP

echo "✅ Test environment deployment completed!"
echo "🌐 Test URL: https://$TEST_APP_NAME.azurewebsites.net"

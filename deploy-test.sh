#!/bin/bash
echo "🚀 部署到测试环境..."

TEST_APP_NAME="api-alex-test-1757506758"
RESOURCE_GROUP="rg-alex"

# 登录到Azure Container Registry
echo "🔐 登录到ACR..."
az acr login --name alexregistry

# 构建多架构Docker镜像 (linux/amd64)
echo "🔨 构建Docker镜像 (linux/amd64)..."
docker buildx build --platform linux/amd64 \
  -t alexregistry.azurecr.io/alex-api-test:latest \
  ./api --push

# 配置App Service使用容器
echo "⚙️ 配置App Service容器..."
az webapp config container set \
  --name $TEST_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --container-registry-url https://alexregistry.azurecr.io \
  --container-registry-user alexregistry \
  --container-registry-password $(az acr credential show --name alexregistry --query passwords[0].value -o tsv) \
  --docker-custom-image-name alexregistry.azurecr.io/alex-api-test:latest

echo "✅ 测试环境部署完成！"
echo "🌐 测试URL: https://$TEST_APP_NAME.azurewebsites.net"

#!/bin/bash

echo "📦 Creating deployment package..."

mkdir -p markily-deploy
cp markily_bot.py markily-deploy/
cp requirements.txt markily-deploy/
cp Dockerfile markily-deploy/
cp docker-compose.yml markily-deploy/
cp .env.example markily-deploy/
cp .dockerignore markily-deploy/
cp docker-deploy.sh markily-deploy/
cp DOCKER_DEPLOY.md markily-deploy/

echo "✅ Deployment package created in markily-deploy/"
echo ""
echo "📤 Upload the markily-deploy/ folder to your VPS"
echo "Then run these commands on your VPS:"
echo ""
echo "cd markily-deploy"
echo "cp .env.example .env"
echo "nano .env"
echo "./docker-deploy.sh"

#!/bin/bash

set -e

echo "🐳 Markily Bot Docker Deployment"
echo "================================"

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your bot token:"
    echo "   nano .env"
    echo ""
    echo "Then run this script again."
    exit 1
fi

if grep -q "YOUR_BOT_TOKEN_HERE" .env; then
    echo "❌ Please set your bot token in .env file first"
    echo "   Edit .env and replace YOUR_BOT_TOKEN_HERE with your actual token"
    exit 1
fi

echo "🏗️  Building Docker image..."
docker-compose build

echo "🚀 Starting Markily Bot..."
docker-compose up -d

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📊 Status:"
docker-compose ps

echo ""
echo "📝 To view logs:"
echo "   docker-compose logs -f markily-bot"
echo ""
echo "🛑 To stop the bot:"
echo "   docker-compose down"
echo ""
echo "🔄 To restart the bot:"
echo "   docker-compose restart"
echo ""
echo "💾 Database is stored in: ./data/markily.db"

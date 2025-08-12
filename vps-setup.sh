#!/bin/bash

echo "🌐 Markily Bot VPS Deployment Commands"
echo "======================================"
echo ""

read -p "Enter your bot token: " BOT_TOKEN

if [ -z "$BOT_TOKEN" ]; then
    echo "❌ Bot token is required!"
    exit 1
fi

echo "📁 Creating project directory..."
mkdir -p ~/markily-bot
cd ~/markily-bot

echo "📝 Creating .env file..."
cat > .env << EOF
BOT_TOKEN=$BOT_TOKEN
EOF

echo "🏗️ Building and starting the bot..."
docker-compose up -d --build

echo ""
echo "✅ Bot deployed successfully!"
echo ""
echo "📊 Check status:"
echo "docker-compose ps"
echo ""
echo "📝 View logs:"
echo "docker-compose logs -f markily-bot"
echo ""
echo "🛑 Stop bot:"
echo "docker-compose down"

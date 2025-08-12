#!/bin/bash

echo "🚀 Setting up Markily Bot on VPS..."

echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

echo "🐍 Installing Python and dependencies..."
sudo apt install -y python3 python3-pip python3-venv git sqlite3

echo "📁 Creating bot directory..."
mkdir -p ~/markily-bot
cd ~/markily-bot

echo "🔧 Setting up virtual environment..."
python3 -m venv markily_env
source markily_env/bin/activate

echo "📚 Installing Python packages..."
pip install python-telegram-bot

echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/markily-bot.service > /dev/null <<EOF
[Unit]
Description=Markily Telegram Debt Manager Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/markily-bot
Environment=PATH=$HOME/markily-bot/markily_env/bin
ExecStart=$HOME/markily-bot/markily_env/bin/python markily_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Deployment script completed!"
echo ""
echo "📋 Next steps:"
echo "1. Upload your markily_bot.py file to ~/markily-bot/"
echo "2. Make sure your bot token is configured"
echo "3. Run: sudo systemctl enable markily-bot"
echo "4. Run: sudo systemctl start markily-bot"
echo "5. Check status: sudo systemctl status markily-bot"

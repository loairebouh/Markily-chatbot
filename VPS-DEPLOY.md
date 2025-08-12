# 🌐 VPS Deployment Guide

## Prerequisites

- Ubuntu/Debian VPS with root access
- Your Telegram Bot Token from @BotFather

## Option 1: Quick One-Command Deployment

### On your VPS, run:

```bash
# Install Docker (if not already installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Deploy the bot
mkdir -p ~/markily-bot && cd ~/markily-bot

# Create all files directly on VPS
cat > markily_bot.py << 'EOF'
# [PASTE YOUR markily_bot.py CONTENT HERE]
EOF

cat > requirements.txt << 'EOF'
python-telegram-bot==22.3
EOF

cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY markily_bot.py .
RUN mkdir -p /app/data

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

RUN useradd --create-home --shell /bin/bash markily
RUN chown -R markily:markily /app
USER markily

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sqlite3; conn = sqlite3.connect('/app/data/markily.db'); conn.close()" || exit 1

CMD ["python", "markily_bot.py"]
EOF

cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  markily-bot:
    build: .
    container_name: markily-telegram-bot
    restart: unless-stopped
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
    volumes:
      - ./data:/app/data
    networks:
      - markily-network
    healthcheck:
      test: ["CMD", "python", "-c", "import sqlite3; conn = sqlite3.connect('/app/data/markily.db'); conn.close()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  markily-network:
    driver: bridge

volumes:
  markily-data:
    driver: local
EOF

# Set your bot token
echo "BOT_TOKEN=YOUR_BOT_TOKEN_HERE" > .env
nano .env  # Edit this file and add your real bot token

# Deploy
docker-compose up -d --build
```

## Option 2: Upload Files Method

### 1. On your local machine:

```bash
# Create deployment package
./package-for-vps.sh

# Upload to VPS (replace with your VPS details)
scp -r markily-deploy/ user@your-vps-ip:~/
```

### 2. On your VPS:

```bash
cd ~/markily-deploy
cp .env.example .env
nano .env  # Add your bot token
chmod +x docker-deploy.sh
./docker-deploy.sh
```

## Management Commands

### Check bot status:

```bash
docker-compose ps
```

### View logs:

```bash
docker-compose logs -f markily-bot
```

### Stop bot:

```bash
docker-compose down
```

### Restart bot:

```bash
docker-compose restart
```

### Update bot:

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Backup database:

```bash
docker cp markily-telegram-bot:/app/data/markily.db ./backup-$(date +%Y%m%d).db
```

## Troubleshooting

### Check if Docker is running:

```bash
sudo systemctl status docker
```

### Check container logs:

```bash
docker logs markily-telegram-bot
```

### Restart Docker service:

```bash
sudo systemctl restart docker
```

### Remove everything and start fresh:

```bash
docker-compose down -v
docker system prune -a
docker-compose up -d --build
```

## Security Notes

- Your bot token is stored in `.env` file - keep it secure
- The bot runs as non-root user inside container
- Database is persistent in `./data/` directory
- Logs are automatically rotated

## Testing Your Bot

1. Find your bot on Telegram
2. Send `/start` command
3. Try commands like:
   - `/addcontact John Doe`
   - `/lend john 100 DZD coffee`
   - `/balance john`

Your bot is now running 24/7 on your VPS! 🎉

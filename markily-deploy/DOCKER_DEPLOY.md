# 🐳 Docker Deployment Guide for Markily Bot

## Prerequisites

- Docker installed on your VPS
- Docker Compose installed
- Your Telegram Bot Token from @BotFather

## Quick Start

### 1. Clone/Upload Your Files

Upload these files to your VPS:

- `markily_bot.py`
- `requirements.txt`
- `Dockerfile`
- `docker-compose.yml`
- `.env.example`

### 2. Set Up Environment

```bash
# Create .env file from template
cp .env.example .env

# Edit .env file and add your bot token
nano .env
```

Add your bot token to the `.env` file:

```
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
```

### 3. Deploy the Bot

```bash
# Build and start the bot
docker-compose up -d

# Check if it's running
docker-compose ps

# View logs
docker-compose logs -f markily-bot
```

## Management Commands

### Start the bot

```bash
docker-compose up -d
```

### Stop the bot

```bash
docker-compose down
```

### Restart the bot

```bash
docker-compose restart
```

### View logs

```bash
# Follow logs in real-time
docker-compose logs -f markily-bot

# View last 100 lines
docker-compose logs --tail=100 markily-bot
```

### Update the bot

```bash
# Stop the bot
docker-compose down

# Rebuild with new code
docker-compose build --no-cache

# Start again
docker-compose up -d
```

### Access the container

```bash
docker-compose exec markily-bot bash
```

### Backup database

```bash
# Copy database from container to host
docker cp markily-telegram-bot:/app/data/markily.db ./backup-$(date +%Y%m%d).db
```

### Restore database

```bash
# Copy database from host to container
docker cp ./backup-20250812.db markily-telegram-bot:/app/data/markily.db
docker-compose restart
```

## File Structure

```
markily-bot/
├── markily_bot.py          # Main bot code
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Docker Compose configuration
├── .env                   # Environment variables (create from .env.example)
├── .env.example           # Environment template
├── .dockerignore          # Files to ignore when building
├── data/                  # Database storage (created automatically)
│   └── markily.db         # SQLite database
└── DOCKER_DEPLOY.md       # This guide
```

## Monitoring

### Check bot health

```bash
docker-compose ps
```

### Check resource usage

```bash
docker stats markily-telegram-bot
```

### Check disk usage

```bash
du -sh data/
```

## Troubleshooting

### Bot not starting

1. Check logs: `docker-compose logs markily-bot`
2. Verify bot token in `.env` file
3. Ensure no other service is using the same container name

### Database issues

1. Check if data directory has proper permissions
2. Verify SQLite file is not corrupted: `sqlite3 data/markily.db ".tables"`

### Permission issues

```bash
# Fix data directory permissions
sudo chown -R $USER:$USER data/
```

### Reset everything

```bash
# Stop and remove containers, networks, and volumes
docker-compose down -v

# Remove the image
docker rmi markily-telegram-bot

# Start fresh
docker-compose up -d --build
```

## Production Recommendations

### 1. Use a reverse proxy (optional)

If you plan to add a web interface later, set up nginx:

```yaml
# Add to docker-compose.yml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
```

### 2. Set up log rotation

Logs are automatically rotated with these settings in docker-compose.yml:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 3. Regular backups

Set up a cron job for automatic backups:

```bash
# Add to crontab (crontab -e)
0 2 * * * cd /path/to/markily-bot && docker cp markily-telegram-bot:/app/data/markily.db ./backups/markily-$(date +\%Y\%m\%d).db
```

### 4. Monitor with docker health checks

The bot includes health checks that restart the container if it becomes unresponsive.

## Security Notes

- Never commit `.env` file to version control
- Keep your bot token secure
- The bot runs as a non-root user inside the container
- Database is stored in a mounted volume for persistence

## Getting Help

If you encounter issues:

1. Check the logs: `docker-compose logs markily-bot`
2. Verify your bot token is correct
3. Ensure Docker and Docker Compose are properly installed
4. Check that ports are not being used by other services

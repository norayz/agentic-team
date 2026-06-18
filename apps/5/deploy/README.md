# Barista Site — Deployment Guide

## Overview
This guide covers deploying the Barista Site application using Docker. The application is a simple Node.js/Express web application with SQLite persistence, suitable for a single coffee shop location.

## Prerequisites
- Docker 20.10+
- Docker Compose 1.29+ (for local development)
- For native deployment: Node.js 20+ and npm 10+

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NODE_ENV` | No | `production` | Environment mode (production/development) |
| `PORT` | No | `3000` | HTTP port the application listens on |
| `DATABASE_PATH` | No | `/app/data/barista.db` | SQLite database file path |

## Local Development

### Using Docker Compose (Recommended)

```bash
# Navigate to project directory
cd apps/5

# Start the application
docker-compose up --build

# The application will be available at http://localhost:3000
```

To stop:
```bash
docker-compose down
```

### Native Development (Without Docker)

```bash
cd apps/5

# Install dependencies
npm install

# Start the development server
npm start

# The application will be available at http://localhost:3000
```

## Production Deployment

### Docker (Single Container)

```bash
# Navigate to project directory
cd apps/5

# Build the Docker image
docker build -t barista-app:1.0.0 .

# Create data directory on host (for persistent database)
mkdir -p ./data

# Run the container
docker run -d \
  --name barista-app \
  --restart unless-stopped \
  -p 3000:3000 \
  -e NODE_ENV=production \
  -e PORT=3000 \
  -v ./data:/app/data \
  barista-app:1.0.0

# Verify the container is running
docker ps | grep barista-app
```

### Docker on a VPS or Server

```bash
# SSH into your server
ssh user@your-server.com

# Clone the repository (or copy the app directory)
git clone https://github.com/your-org/barista-app.git
cd barista-app/apps/5

# Create data directory
mkdir -p data

# Build and run
docker build -t barista-app:latest .
docker run -d \
  --name barista-app \
  --restart always \
  -p 80:3000 \
  -e NODE_ENV=production \
  -v $(pwd)/data:/app/data \
  barista-app:latest
```

### Using Docker Compose on Server

If you prefer to use docker-compose on your server:

```bash
cd /path/to/barista-app/apps/5

# Create .env file with production values
cat > .env << EOF
NODE_ENV=production
PORT=3000
DATABASE_PATH=/app/data/barista.db
EOF

# Start with compose
docker-compose up -d
```

## Database Persistence

The SQLite database is stored in `/app/data/barista.db` inside the container. To persist data:

### With Docker Volume (Recommended)
```bash
# The docker-compose.yml already includes volume mapping
# Database data is stored in ./data/barista.db on the host
```

### Manual Backup
```bash
# Copy database from container
docker cp barista-app:/app/data/barista.db ./barista-backup.db

# Restore database to container
docker cp ./barista-backup.db barista-app:/app/data/barista.db
```

## Health Check

The container includes a health check that tests basic connectivity every 30 seconds:

```bash
# Check container health
docker inspect barista-app --format='{{.State.Health.Status}}'

# Should output: "healthy", "starting", or "unhealthy"
```

Manual health verification:
```bash
curl -i http://localhost:3000/

# Should return HTTP 200
```

## Performance & Scaling

### Memory & CPU
The application is lightweight and suitable for single-location deployment:
- **Memory**: 50-100 MB typical
- **CPU**: Minimal usage for < 100 orders/day

### Recommended Container Limits
```bash
docker run ... \
  --memory=256m \
  --cpus=0.5 \
  barista-app:1.0.0
```

## Logging

### View Container Logs
```bash
# Real-time logs
docker logs -f barista-app

# Last 100 lines
docker logs --tail 100 barista-app
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs barista-app

# Common issues:
# 1. Port 3000 already in use
#    Solution: Use different port: -p 8080:3000
# 2. Database file permission issues
#    Solution: Ensure ./data directory is writable
```

### Database corruption
```bash
# Remove corrupted database (it will be recreated with schema)
rm ./data/barista.db

# Restart container
docker restart barista-app
```

### Slow performance
```bash
# Check resource usage
docker stats barista-app

# Verify database isn't growing too large
ls -lh ./data/barista.db

# Consider archiving old orders if database grows beyond 100MB
```

## Reverse Proxy (Nginx)

For production, run behind a reverse proxy:

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name coffee.example.com;
    client_max_body_size 10M;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Run Nginx container:
```bash
docker run -d \
  --name nginx-reverse-proxy \
  --restart unless-stopped \
  -p 80:80 \
  -v /path/to/nginx.conf:/etc/nginx/conf.d/default.conf \
  nginx:alpine
```

## Monitoring & Maintenance

### Regular Tasks

**Daily**:
- Monitor error logs: `docker logs barista-app | grep ERROR`
- Check container health: `docker inspect barista-app --format='{{.State.Health.Status}}'`

**Weekly**:
- Backup database: `docker cp barista-app:/app/data/barista.db ./backups/barista-$(date +%Y-%m-%d).db`
- Check disk space: `df -h`

**Monthly**:
- Review database size
- Archive old completed orders if needed
- Test backup/restore process

### Useful Commands

```bash
# Stop container gracefully
docker stop barista-app

# Remove container (preserves volume)
docker rm barista-app

# Update to new version
docker pull barista-app:latest
docker stop barista-app
docker rm barista-app
docker run -d ... barista-app:latest

# View resource usage
docker stats barista-app
```

## Security Notes

1. **Non-root user**: Application runs as `nodejs` user (UID 1001), not root
2. **No authentication**: Admin page is accessible via direct URL (security by obscurity for v1)
3. **Database**: SQLite is file-based; ensure proper file permissions (handled by Docker)
4. **Network**: Run behind reverse proxy with TLS/HTTPS in production
5. **Secrets**: Use environment variables for any future sensitive config (never hardcode)

## Deployment Checklist

- [ ] Docker installed on target system
- [ ] Port 3000 (or reverse proxy port) is accessible
- [ ] Data volume is writable
- [ ] Database backup strategy in place
- [ ] Reverse proxy configured (Nginx/HAProxy recommended)
- [ ] HTTPS enabled via reverse proxy or Let's Encrypt
- [ ] Monitoring/alerting configured
- [ ] Rollback procedure documented

## Support & Questions

For issues or questions:
1. Check logs: `docker logs barista-app`
2. Verify database: `docker exec barista-app sqlite3 /app/data/barista.db ".tables"`
3. Test connectivity: `curl -i http://localhost:3000/`

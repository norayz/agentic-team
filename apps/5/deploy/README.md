# Barista Site - Deployment Guide

## Overview

This guide covers deployment of the Barista Site application using Docker. The application is a Node.js/Express web server with SQLite database for persistent order storage.

### Architecture
- **Runtime**: Node.js 20 (Alpine Linux)
- **Framework**: Express.js with EJS server-side rendering
- **Database**: SQLite (single-file, zero-config)
- **Persistence**: Volume-mounted `/app/data` directory
- **Security**: Non-root user (UID 1001), no hardcoded secrets

## Prerequisites

### For Local Development
- Docker 20.10+
- Docker Compose 1.29+
- ~500 MB free disk space

### For Production Deployment
- Docker 20.10+ on target host (VPS, cloud VM, etc.)
- Persistent storage for database (local volume, mounted NFS, or cloud storage)
- ~300 MB free disk space minimum
- (Optional) Reverse proxy with TLS/SSL (Nginx, HAProxy, or cloud load balancer)

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NODE_ENV` | Yes | - | Environment: 'development' or 'production' |
| `PORT` | No | 3000 | Port application listens on inside container |
| `DATABASE_PATH` | Yes | /app/data/barista.db | Path to SQLite database file |
| `TRUST_PROXY` | No | false | Set to true if behind reverse proxy |

## Local Development

### Quick Start

```bash
# Navigate to the app directory
cd apps/5

# Copy example environment file
cp .env.example .env

# Start the application
docker-compose up --build

# The application will be available at http://localhost:3000
```

### Troubleshooting Local Development

**Port 3000 already in use?**
```bash
# Use a different port
PORT=8000 docker-compose up --build
```

**Database not persisting?**
Verify the `./data` volume is mounted:
```bash
docker-compose exec app ls -la /app/data
```

**Container won't start?**
```bash
# Check logs
docker-compose logs app

# Verify image built correctly
docker build -t barista-app:test .
```

## Production Deployment

### Option 1: Single Container on VPS

This is the simplest production setup for a single coffee shop location.

#### Deployment Steps

1. **SSH into your VPS**
   ```bash
   ssh user@your-vps-ip
   ```

2. **Clone the repository**
   ```bash
   git clone <your-repo-url> barista-site
   cd barista-site/apps/5
   ```

3. **Create production environment file**
   ```bash
   cp .env.example .env
   nano .env
   ```

   Recommended production settings:
   ```bash
   NODE_ENV=production
   PORT=3000
   DATABASE_PATH=/app/data/barista.db
   TRUST_PROXY=false
   ```

4. **Create data directory**
   ```bash
   mkdir -p ./data
   chmod 755 ./data
   ```

5. **Build the Docker image**
   ```bash
   docker build -t barista-app:1.0.0 .
   ```

6. **Run the container**
   ```bash
   docker run -d \
     --name barista-app \
     -p 3000:3000 \
     -e NODE_ENV=production \
     -e PORT=3000 \
     -e DATABASE_PATH=/app/data/barista.db \
     -v $(pwd)/data:/app/data \
     --restart unless-stopped \
     barista-app:1.0.0
   ```

7. **Verify the container is running**
   ```bash
   docker ps
   docker logs barista-app
   ```

8. **Test the application**
   ```bash
   curl http://localhost:3000
   ```

### Option 2: Docker Compose on VPS

This matches local development workflow:

```bash
cd barista-site/apps/5

# Create production environment
cp .env.example .env
nano .env  # Set NODE_ENV=production

# Start with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f app
```

### Option 3: With Nginx Reverse Proxy (For HTTPS)

For production with TLS:

1. **Run the app on localhost only**
   ```bash
   docker run -d \
     --name barista-app \
     -p 127.0.0.1:3000:3000 \
     -e NODE_ENV=production \
     -v $(pwd)/data:/app/data \
     --restart unless-stopped \
     barista-app:1.0.0
   ```

2. **Install Nginx**
   ```bash
   sudo apt update && sudo apt install -y nginx certbot python3-certbot-nginx
   ```

3. **Create Nginx config** (`/etc/nginx/sites-available/barista`)
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://127.0.0.1:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

4. **Enable site and get TLS certificate**
   ```bash
   sudo ln -s /etc/nginx/sites-available/barista /etc/nginx/sites-enabled/
   sudo certbot --nginx -d yourdomain.com
   sudo systemctl restart nginx
   ```

## Database Persistence

### Understanding Volume Mounts

The SQLite database is persisted using a volume mount:
```bash
-v $(pwd)/data:/app/data
```

This ensures:
- All orders survive container restarts
- Database can be backed up by copying `./data/barista.db`
- Multiple container restarts don't lose data

### Backup and Restore

**Backup the database:**
```bash
cp ./data/barista.db ./data/barista.db.backup
```

**Restore from backup:**
```bash
cp ./data/barista.db.backup ./data/barista.db
```

**Export orders as JSON:**
```bash
docker exec barista-app sqlite3 /app/data/barista.db \
  '.mode json' 'SELECT * FROM orders;' > orders-export.json
```

## Health Check and Monitoring

### Manual Health Check

```bash
# Check container health status
docker inspect barista-app --format='{{.State.Health.Status}}'
```

### Application Logs

```bash
# View logs
docker logs barista-app

# Follow logs in real-time
docker logs -f barista-app

# View last 100 lines
docker logs --tail=100 barista-app
```

### Memory and CPU Usage

```bash
# Check resource usage
docker stats barista-app
```

Expected metrics for <100 orders/day:
- Memory: 40-80 MB
- CPU: <1% idle
- Storage: <50 MB (database + logs)

## Scaling Notes

This single-container deployment is optimized for:
- **Target**: Single coffee shop location
- **Load**: <100 orders/day
- **Concurrent users**: 10-20 simultaneous browsers
- **Response time**: <500ms on menu/cart pages

## Image Size and Security

### Image Statistics
- **Uncompressed**: 150-180 MB
- **Compressed** (registry): 50-60 MB
- **Memory footprint**: 40-80 MB at runtime

### Security Checklist
- Application runs as non-root user
- No hardcoded secrets in image
- All configuration via environment variables
- Alpine base: minimal attack surface
- Dev dependencies excluded from runtime image
- Health check validates application responsiveness

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs barista-app

# Common issues:
# - PORT already in use: change port in docker run
# - Database file permissions: ensure ./data is writable
# - Out of disk space: check disk usage (df -h)
```

### Orders not persisting
```bash
# Verify volume is mounted
docker inspect barista-app | grep -A 5 Mounts

# Check database file exists
ls -lh ./data/barista.db
```

### App responds slowly
```bash
# Check memory usage
docker stats barista-app

# Check database file size
ls -lh ./data/barista.db

# Run database maintenance
docker exec barista-app sqlite3 /app/data/barista.db VACUUM;
```

### Can't connect to app from browser
```bash
# Verify container is running
docker ps | grep barista-app

# Check if app is listening on correct port
docker exec barista-app netstat -tlnp | grep 3000

# Test locally inside container
docker exec barista-app curl http://localhost:3000
```

## Maintenance Tasks

### Daily (Automated)
- Health check runs every 30s (built into container)
- Logs are rotated by Docker daemon

### Weekly (Manual)
```bash
# Back up database
cp ./data/barista.db ./backups/barista.db.$(date +%Y%m%d)
```

### Monthly (Manual)
```bash
# Clean up old completed orders
docker exec barista-app sqlite3 /app/data/barista.db \
  'DELETE FROM orders WHERE status = "completed" AND pickup_time < date("now", "-90 days");'

# Vacuum database to reclaim space
docker exec barista-app sqlite3 /app/data/barista.db VACUUM;
```

## Deployment Checklist

- [ ] Docker installed and running on target host
- [ ] Persistent storage available and mounted
- [ ] Environment variables configured (.env file)
- [ ] Image builds without errors
- [ ] Container starts and health check passes
- [ ] Application responds on configured port
- [ ] Database file created and writable
- [ ] (Optional) Reverse proxy configured for TLS
- [ ] (Optional) DNS pointing to correct IP
- [ ] Backup strategy in place for database
- [ ] Team has access to deployment procedure

# Deployment Guide — Barista Site

This guide covers deploying the Barista Site (Express.js + SQLite) to production environments.

## Prerequisites

- **Docker** 20.10+ (for container deployment)
- **Docker Compose** 1.29+ (for local development and orchestration)
- **Node.js** 20+ (for local development without Docker)

## Environment Variables

All deployment configurations use environment variables. Do not hardcode values in the image.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NODE_ENV` | No | `development` | Environment mode: `development`, `production`, or `staging` |
| `PORT` | No | `3000` | Server listen port |
| `DB_PATH` | No | `./db/orders.db` | Path to SQLite database file (must be writable) |
| `LOG_LEVEL` | No | `info` | Logging verbosity: `debug`, `info`, `warn`, `error` |

## Local Development

### With Docker Compose (Recommended)

```bash
# Copy the example environment file
cp .env.example .env

# Start the application and its dependencies
docker-compose up --build

# The application will be available at http://localhost:3000

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

### Without Docker (Requires Node.js 20+)

```bash
# Install dependencies
npm install

# Create database directory
mkdir -p db logs

# Start the application
npm start

# The application will be available at http://localhost:3000
```

## Production Deployment

### Option 1: Single Server (Recommended for <100 orders/day)

#### 1. Build the Docker image

```bash
docker build -t barista-site:1.0.0 .
```

#### 2. Create persistent storage directories

```bash
# On your production server
mkdir -p /var/barista-site/db /var/barista-site/logs
chown 1000:1000 /var/barista-site/db /var/barista-site/logs
```

#### 3. Run the container

```bash
docker run -d \
  --name barista-site \
  --restart unless-stopped \
  -p 80:3000 \
  -v /var/barista-site/db:/app/db \
  -v /var/barista-site/logs:/app/logs \
  -e NODE_ENV=production \
  -e LOG_LEVEL=info \
  --health-interval 30s \
  --health-timeout 5s \
  --health-retries 3 \
  barista-site:1.0.0
```

#### 4. Verify the container is healthy

```bash
docker ps  # STATUS should show "healthy"
```

#### 5. Configure reverse proxy (optional but recommended)

For production, run the container behind a reverse proxy (nginx, Caddy, or cloud load balancer):

```nginx
# Example nginx configuration
upstream barista {
    server localhost:3000;
}

server {
    listen 80;
    server_name coffee.example.com;

    location / {
        proxy_pass http://barista;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Option 2: Docker Compose in Production

```bash
# Copy docker-compose.yml to production server
scp docker-compose.yml user@production:/srv/barista-site/
cd /srv/barista-site

# Create .env file with production values
cat > .env <<EOF
NODE_ENV=production
PORT=3000
LOG_LEVEL=warn
EOF

# Create data directories
mkdir -p db logs

# Start services
docker-compose up -d

# View logs
docker-compose logs -f app
```

### Option 3: Kubernetes (For future multi-instance deployment)

Refer to `deploy/k8s/` directory if adding Kubernetes support. Not required for v1.

## Health Checks

The container includes a built-in health check that verifies:
1. Server responds to HTTP requests on port 3000
2. Health check endpoint returns HTTP 200

Verify container health:

```bash
docker inspect barista-site --format='{{.State.Health.Status}}'
# Output: healthy, unhealthy, or none
```

## Database Backups

SQLite stores all data in a single file (`orders.db`). Backup strategies:

### Daily Backup

```bash
#!/bin/bash
# backup-barista.sh

BACKUP_DIR="/backups/barista-site"
DB_PATH="/var/barista-site/db/orders.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"
cp "$DB_PATH" "$BACKUP_DIR/orders_$TIMESTAMP.db"

# Keep only last 30 days
find "$BACKUP_DIR" -name "*.db" -mtime +30 -delete
```

Add to crontab:

```bash
0 2 * * * /usr/local/bin/backup-barista.sh
```

## Monitoring and Logging

### View Container Logs

```bash
# Real-time logs
docker logs -f barista-site

# Last 100 lines
docker logs --tail 100 barista-site

# Logs from the last hour
docker logs --since 1h barista-site
```

### Log Rotation

Configure Docker to rotate logs:

```bash
docker run -d \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=5 \
  barista-site:1.0.0
```

## Troubleshooting

### Container fails to start

```bash
# Check logs
docker logs barista-site

# Verify environment variables
docker inspect barista-site --format='{{.Config.Env}}'

# Check database permissions
docker exec barista-site ls -l /app/db/
```

### Database is locked error

SQLite may report "database is locked" if multiple processes write simultaneously. This is rare in low-traffic scenarios but can occur if:
- The server was not shut down cleanly
- Multiple instances are accessing the same database file

Solution: Remove stale lock files and restart:

```bash
rm /var/barista-site/db/orders.db-shm
rm /var/barista-site/db/orders.db-wal
docker restart barista-site
```

### High memory usage

Node.js has default memory limits. If seeing OOM errors:

```bash
docker run -d \
  -m 512m \
  --memory-swap 512m \
  barista-site:1.0.0
```

## Performance Tuning

### SQLite Configuration

For better concurrency with multiple orders arriving simultaneously, the app should set pragmas in OrderStore:

```javascript
db.run('PRAGMA journal_mode = WAL;');  // Write-Ahead Logging
db.run('PRAGMA synchronous = NORMAL;');
db.run('PRAGMA cache_size = -64000;');  // 64MB cache
```

These should be configured in the backend (see app initialization).

### Container Resource Limits

For a single coffee shop location (<100 orders/day):

```bash
docker run -d \
  --cpus 0.5 \
  -m 256m \
  barista-site:1.0.0
```

## Updating the Application

```bash
# Stop the running container
docker stop barista-site
docker rm barista-site

# Build new image
docker build -t barista-site:1.0.1 .

# Run updated container (database persists in volume)
docker run -d \
  --name barista-site \
  --restart unless-stopped \
  -p 80:3000 \
  -v /var/barista-site/db:/app/db \
  -v /var/barista-site/logs:/app/logs \
  -e NODE_ENV=production \
  barista-site:1.0.1
```

## Support and Issues

For deployment issues, check:
1. Docker container logs: `docker logs barista-site`
2. Database file permissions: `ls -l /var/barista-site/db/`
3. Firewall rules: Ensure port 80/443 is open to clients
4. Reverse proxy configuration: If using nginx/Caddy, verify upstream routing

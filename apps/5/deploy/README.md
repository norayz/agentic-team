# Deployment Guide — Barista Site

## Prerequisites

- **Docker 20.10+**
- **Docker Compose 2.0+** (for local development)

For production, ensure the host has sufficient disk space for SQLite database (`/app/db/orders.db` typically <100 MB for <100 orders/day).

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NODE_ENV` | No | `development` | Set to `production` for deployment |
| `PORT` | No | `3000` | Port the application listens on |
| `DB_PATH` | No | `/app/db/orders.db` | Location of SQLite database file (inside container) |
| `LOG_LEVEL` | No | `info` | Logging level: `debug`, `info`, `warn`, `error` |

## Local Development

```bash
# 1. Clone the repository
git clone <repo-url>
cd apps/5

# 2. Create .env from template (optional, defaults work fine)
cp .env.example .env

# 3. Start the application stack
docker-compose up --build

# 4. Open browser
open http://localhost:3000

# 5. View orders in admin panel
open http://localhost:3000/admin
```

The application will be available at `http://localhost:3000`.

### Stopping the Application

```bash
docker-compose down
```

To stop and also delete the database volume:

```bash
docker-compose down -v
```

## Production Deployment

### Build the Docker Image

```bash
docker build -t barista-site:v1.0 .
```

### Run the Container

```bash
# Create directories for persistent storage
mkdir -p /var/barista/db
mkdir -p /var/barista/logs

# Run the container
docker run -d \
  --name barista-site \
  -p 80:3000 \
  --env NODE_ENV=production \
  --env LOG_LEVEL=info \
  --volume /var/barista/db:/app/db \
  --volume /var/barista/logs:/app/logs \
  --restart unless-stopped \
  barista-site:v1.0
```

### Health Check

Verify the container is healthy:

```bash
# Check container status
docker inspect barista-site --format='{{.State.Health.Status}}'
# Expected output: healthy

# Check logs
docker logs barista-site

# Test the application
curl -I http://localhost/
```

### Updating the Application

```bash
# 1. Pull or build the new version
docker build -t barista-site:v1.1 .

# 2. Stop and remove old container
docker stop barista-site
docker rm barista-site

# 3. Run new container (using same command as above)
docker run -d \
  --name barista-site \
  -p 80:3000 \
  --env NODE_ENV=production \
  --env LOG_LEVEL=info \
  --volume /var/barista/db:/app/db \
  --volume /var/barista/logs:/app/logs \
  --restart unless-stopped \
  barista-site:v1.1
```

### Database Persistence

The SQLite database is stored in `/app/db/orders.db` inside the container. The docker-compose and production run commands above mount this to a host volume so data survives container restarts and updates.

**Backup the database regularly:**

```bash
cp /var/barista/db/orders.db /backup/orders.db.$(date +%Y%m%d)
```

## Reverse Proxy Configuration (Nginx)

For production, run the container on port 3000 internally and use a reverse proxy:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Troubleshooting

### Container fails to start

```bash
docker logs barista-site
```

Common issues:
- **Port 3000 is already in use**: Change the port mapping with `-p 8080:3000`
- **Permission denied on database directory**: Ensure the volume directory is owned by the host user or has 755 permissions

### Database is corrupted

If the SQLite database becomes corrupted, delete it and restart:

```bash
docker exec barista-site rm /app/db/orders.db
docker restart barista-site
```

The application will recreate the database schema on startup.

### Health check failing

The container performs HTTP health checks every 30 seconds. If checks are failing:

```bash
# Check application logs
docker logs barista-site

# Test health endpoint manually
curl -v http://localhost:3000/
```

If the application is running but health checks fail, adjust the health check in `docker-compose.yml` or the container's `HEALTHCHECK` instruction.

### Slow performance

1. Check container resource limits:
   ```bash
   docker stats barista-site
   ```

2. Monitor disk I/O (SQLite can be slow on some I/O-constrained systems):
   ```bash
   # Inside the container
   docker exec barista-site df -h /app/db
   ```

3. For high traffic (>100 orders/day), consider migrating to PostgreSQL in a future version.

## Monitoring & Logging

Application logs are written to `/app/logs` inside the container (mounted to `/var/barista/logs` on host).

```bash
# View recent logs
tail -f /var/barista/logs/*.log

# Inside container via docker exec
docker exec barista-site tail -f /app/logs/app.log
```

## Rollback

To rollback to a previous version:

```bash
# 1. Stop current container
docker stop barista-site
docker rm barista-site

# 2. Run previous version
docker run -d \
  --name barista-site \
  -p 80:3000 \
  --env NODE_ENV=production \
  --env LOG_LEVEL=info \
  --volume /var/barista/db:/app/db \
  --volume /var/barista/logs:/app/logs \
  --restart unless-stopped \
  barista-site:v1.0  # Previous version tag
```

The database volume persists across rollbacks — no data is lost.

## Security Notes

- The admin panel at `/admin` has no authentication. Keep the URL unlisted and consider using a firewall/IP whitelist in production.
- No secrets (passwords, API keys) are baked into the image — all configuration is via environment variables.
- The application runs as a non-root user inside the container.
- For HTTPS, place the container behind a reverse proxy (e.g., Nginx with Let's Encrypt).

## Support

For issues or questions, refer to the project README or contact the development team.

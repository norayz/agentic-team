# Barista Site — Deployment Guide

## Prerequisites

- **Docker** 20.10+
- **Docker Compose** 2.0+ (for local development)
- **Node.js** 20+ (for running without Docker, if needed)

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NODE_ENV` | No | `production` | Node environment mode |
| `PORT` | No | `3000` | Server listening port (inside container) |
| `DATABASE_PATH` | No | `/app/data/barista.db` | Path to SQLite database file |
| `HOST_PORT` | No | `3000` | Host port to expose (docker-compose only) |
| `APP_NAME` | No | `Barista Site` | Display name for the application |
| `COFFEE_SHOP_NAME` | No | `My Coffee House` | Name of the coffee shop (displayed in UI) |

## Local Development

### Quick Start

```bash
# Copy environment template
cp .env.example .env

# (Optional) Edit .env with your values
vim .env

# Start the application with docker-compose
docker-compose up --build

# The application will be available at:
# http://localhost:3000       (customer menu and ordering)
# http://localhost:3000/admin (order management - no auth, unlisted URL)
```

### View Logs

```bash
# Tail logs from the running container
docker-compose logs -f app

# View logs for a specific number of lines
docker-compose logs --tail=50 app
```

### Stop the Application

```bash
# Stop the container
docker-compose down

# Stop and remove volumes (clears database)
docker-compose down -v
```

## Production Deployment

### Prerequisites

- A Linux server or VPS with Docker installed
- A persistent directory for SQLite database (e.g., `/opt/barista/data`)
- Optional: A reverse proxy (nginx) for SSL termination and improved performance

### Step 1: Prepare the Server

```bash
# Create directories for app and data
mkdir -p /opt/barista/data
cd /opt/barista

# Clone or copy the application code
git clone <repository-url> .
# or
cp -r <local-path> .
```

### Step 2: Build the Docker Image

```bash
# Build the production image
cd /opt/barista/apps/5
docker build -t barista:v1.0 .
```

### Step 3: Create `.env` for Production

```bash
cat > /opt/barista/.env << EOF
NODE_ENV=production
PORT=3000
DATABASE_PATH=/app/data/barista.db
COFFEE_SHOP_NAME="My Coffee House"
APP_NAME="Barista Site"
EOF
```

### Step 4: Run the Container

```bash
# Run the container in detached mode
docker run -d \
  --name barista \
  --restart unless-stopped \
  -p 3000:3000 \
  -v /opt/barista/data:/app/data \
  --env-file /opt/barista/.env \
  barista:v1.0

# Verify the container is running
docker ps | grep barista
```

### Step 5: Verify Health

```bash
# Check container is healthy
docker inspect barista --format='{{.State.Health.Status}}'

# Should output: healthy
```

### Step 6: Optional — Configure Reverse Proxy (nginx)

If you want to expose the app on a standard HTTP/HTTPS port:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Reload nginx:
```bash
sudo systemctl reload nginx
```

## Data Persistence

The application uses SQLite with a file-based database stored at `DATABASE_PATH`. In the Docker setup:

- **Local dev**: Database is in `./data/barista.db` (mounted as a volume)
- **Production**: Database is in `/opt/barista/data/barista.db` (mounted as a volume)

**Important**: Always mount a persistent volume for the `/app/data` directory so orders survive container restarts.

## Backup

To backup orders:

```bash
# Copy the SQLite database
cp /opt/barista/data/barista.db /opt/barista/data/barista.db.backup

# Or from docker:
docker cp barista:/app/data/barista.db ./barista.db.backup
```

## Health Check

The container exposes a health endpoint at `GET /health` (every 30 seconds). To check manually:

```bash
# From inside the container or if port 3000 is accessible:
curl http://localhost:3000/health

# Or check docker health status:
docker inspect barista --format='{{.State.Health.Status}}'
```

## Updating the Application

1. Rebuild the image:
   ```bash
   docker build -t barista:v1.1 .
   ```

2. Stop the old container:
   ```bash
   docker stop barista
   docker rm barista
   ```

3. Start the new container (preserving the data volume):
   ```bash
   docker run -d \
     --name barista \
     --restart unless-stopped \
     -p 3000:3000 \
     -v /opt/barista/data:/app/data \
     --env-file /opt/barista/.env \
     barista:v1.1
   ```

## Troubleshooting

### Container exits immediately

Check logs:
```bash
docker logs barista
```

Common causes:
- Missing `node_modules` — rebuild image
- Incorrect `DATABASE_PATH` — ensure `/app/data` is writable
- Port already in use — change `HOST_PORT` or kill the conflicting process

### Health check failing

Verify the app is responding:
```bash
curl http://localhost:3000
```

If it hangs, the app may not have started. Check logs and ensure sufficient resources.

### Database locked errors

If you see `database is locked`, this can happen if:
- Multiple container instances are running on the same database
- The container crashed while writing to the database

Solution: Use only one container instance per database, or implement database connection pooling.

### Orders not persisting after restart

Ensure the data volume is mounted:
```bash
docker inspect barista | grep -A 10 Mounts
```

The output should show `/app/data` mounted to a persistent host path.

## Monitoring

For production, consider:
- **Container logs** — Collect with `docker logs` or a log aggregator
- **Health checks** — Periodically call `GET /health`
- **Resource usage** — Monitor CPU and memory with `docker stats barista`
- **Database size** — Monitor `/opt/barista/data/barista.db` file size

## Security Notes

- The admin page (`/admin`) is **not password-protected**. It is accessed via an unlisted URL and intended for a single operator.
- In a future version, add authentication (e.g., basic auth, OAuth) if multi-operator access is needed.
- Never expose the `/admin` URL in search engines or public documentation.
- The application runs as a non-root user (`appuser`) inside the container for reduced attack surface.

## Support

For issues or questions, refer to:
- Application logs: `docker logs barista`
- Container status: `docker inspect barista`
- Issue tracker: [project repository]

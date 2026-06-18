# Barista Site - Deployment Guide

## Prerequisites

- Docker 20.10+
- Docker Compose 1.29+ (for local development)
- Any OS with Docker support (Linux, macOS, Windows with Docker Desktop)

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| NODE_ENV | No | production | Set to 'development' for debugging, 'production' for stable operation |
| APP_PORT | No | 3000 | Port on which the application will listen |
| DATABASE_PATH | No | /app/data/orders.db | Path to SQLite database file (must be on a persistent volume in containers) |
| APP_NAME | No | Barista Coffee House | Application name displayed in UI |

## Local Development

Quick Start:

```bash
cd apps/5
cp .env.example .env
docker-compose up --build
```

The application will be available at http://localhost:3000

## Production Deployment

Build the image:

```bash
cd apps/5
docker build -t barista-app:1.0.0 .
```

Run the container:

```bash
mkdir -p /data/barista-orders
chown 1001:1001 /data/barista-orders

docker run -d \
  --name barista-app \
  -p 3000:3000 \
  -e NODE_ENV=production \
  -v /data/barista-orders:/app/data \
  --restart unless-stopped \
  barista-app:1.0.0
```

## Data Persistence

The SQLite database MUST be stored on a persistent volume. Without this, all orders are lost when the container is destroyed.

## Health Check

The container includes a health check. Verify:

```bash
docker inspect barista-app --format='{{.State.Health.Status}}'
```

## Security

- Application runs as non-root user (appuser, UID 1001)
- No secrets baked into the image
- Admin endpoint (/admin) is not password-protected (single-operator assumption)
- For production, place behind authentication proxy or firewall

## Image Size

- Runtime image: ~200MB
- Compressed: ~70MB

## Troubleshooting

Check logs:
```bash
docker logs barista-app
```

Restart the container:
```bash
docker restart barista-app
```

Verify data directory permissions:
```bash
ls -la /data/barista-orders/
chown 1001:1001 /data/barista-orders/orders.db
```

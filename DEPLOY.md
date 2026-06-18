# Deployment Guide

## Prerequisites

- Docker 20.10+
- Docker Compose 1.29+ (for local development)
- curl (for health checks)

## Environment Variables

All environment variables are optional; defaults are provided.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_PORT` | No | `8000` | Port on which the FastAPI application listens |
| `DATABASE_URL` | No | `sqlite:///./todos.db` | SQLite database file path (local file only) |
| `APP_ENV` | No | `development` | Application environment (development or production) |

## Local Development

### Using Docker Compose

```bash
# Copy the example environment file
cp .env.example .env

# (Optional) Edit .env with your custom values
# nano .env

# Build and start the application
docker-compose up --build

# The application will be available at http://localhost:8000
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

To stop the application:
```bash
docker-compose down
```

To stop and remove all data (including SQLite database):
```bash
docker-compose down -v
```

### Running Natively (without Docker)

```bash
# Create a virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Production Deployment

### Build the Docker Image

```bash
# Build the image with a version tag
docker build -t todos-api:1.0.0 .
```

### Run the Container

```bash
# Run the container
docker run -d \
  --name todos-api \
  -p 8000:8000 \
  --restart unless-stopped \
  -e API_PORT=8000 \
  -e DATABASE_URL=sqlite:///./todos.db \
  -e APP_ENV=production \
  todos-api:1.0.0
```

### Verify Container Health

```bash
# Check container status
docker ps | grep todos-api

# Check container health
docker inspect todos-api --format='{{.State.Health.Status}}'

# View logs
docker logs -f todos-api

# Test the API
curl http://localhost:8000/todos
```

### Volume Mounting (for persistent data)

For production, you may want to mount a host directory for the SQLite database:

```bash
# Create a directory on the host for database files
mkdir -p /var/lib/todos-api

# Run with volume mount
docker run -d \
  --name todos-api \
  -p 8000:8000 \
  --restart unless-stopped \
  -v /var/lib/todos-api:/app \
  -e API_PORT=8000 \
  -e DATABASE_URL=sqlite:////var/lib/todos-api/todos.db \
  todos-api:1.0.0
```

## Health Check

The Docker image includes a built-in health check that:
- Runs every 30 seconds
- Times out after 5 seconds
- Starts checking after 10 seconds (startup grace period)
- Marks the container unhealthy after 3 consecutive failures

The health check probes the Swagger UI endpoint at `/docs`. If the application is responding, the container is healthy.

## Troubleshooting

### Container exits immediately

```bash
# Check the logs
docker logs todos-api

# Common cause: Port already in use
# Solution: Use a different port
docker run -d \
  --name todos-api \
  -p 8001:8000 \
  todos-api:1.0.0
```

### Database file permissions error

```bash
# Ensure the volume directory is writable
chmod 755 /var/lib/todos-api

# Check container user
docker inspect todos-api --format='{{.Config.User}}'  # Should be "appuser"
```

### API not responding

```bash
# Check if container is healthy
docker inspect todos-api --format='{{.State.Health.Status}}'

# If unhealthy, check recent logs
docker logs --tail 50 todos-api

# Verify port binding
docker port todos-api
```

### SQLite database locked error

This occurs when multiple processes try to write to the database simultaneously. Solutions:
1. Ensure only one container instance is running at a time
2. Use `--restart unless-stopped` to prevent auto-restart conflicts
3. For high concurrency needs, consider migrating to PostgreSQL

## Maintenance

### View database contents

```bash
# Interactive shell in container
docker exec -it todos-api /bin/bash

# Inside container:
sqlite3 todos.db
sqlite> .tables
sqlite> SELECT * FROM todos;
sqlite> .exit
```

### Backup database

```bash
# Copy database from container to host
docker cp todos-api:/app/todos.db ./todos.db.backup
```

### Restore database

```bash
# Copy database from host to container
docker cp ./todos.db.backup todos-api:/app/todos.db

# Restart container to apply
docker restart todos-api
```

### Remove container and image

```bash
# Stop and remove container
docker stop todos-api
docker rm todos-api

# Remove image
docker rmi todos-api:1.0.0
```

## Performance Notes

- **Single-user, local-only workload**: This image is optimized for personal development use
- **Response time**: The API should respond in under 100ms for all endpoints under single-user load
- **Database**: SQLite is sufficient for this workload and does not require external services
- **Concurrency**: Synchronous routes handle the single-user requirement efficiently

## Further Reading

- FastAPI Documentation: https://fastapi.tiangolo.com/
- Uvicorn Documentation: https://www.uvicorn.org/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- Docker Best Practices: https://docs.docker.com/develop/dev-best-practices/

# Multi-stage build for Barista Site (Express + EJS + SQLite)
# Stage 1: Builder
FROM node:20-alpine3.20 AS builder

WORKDIR /build

# Copy package files
COPY package*.json ./

# Install dependencies (including build tools for native modules like sqlite3)
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    && npm ci --only=production

# Stage 2: Runtime
FROM node:20-alpine3.20

# Set environment
ENV NODE_ENV=production

WORKDIR /app

# Create non-root user and group for security
RUN addgroup -g 1001 -S appuser && \
    adduser -S appuser -u 1001

# Copy only node_modules and package files from builder
COPY --from=builder /build/node_modules ./node_modules
COPY package*.json ./

# Copy application source code
COPY src ./src
COPY views ./views
COPY public ./public
COPY data ./data

# Create directory for SQLite database persistence
RUN mkdir -p /app/data && chown appuser:appuser /app/data

# Change ownership of app directory to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port (Express default)
EXPOSE 3000

# Health check: verify app is responding on port 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1

# Start application
CMD ["npm", "start"]

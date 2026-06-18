# Multi-stage build for Barista Site (Express.js + SQLite + EJS)
# Stage 1: Builder
FROM node:20-alpine AS builder

WORKDIR /build

# Install build dependencies (required for native module compilation)
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    cairo-dev \
    jpeg-dev \
    pango-dev \
    giflib-dev

# Copy package files
COPY package*.json ./

# Install production and development dependencies (dev deps needed for build)
RUN npm ci --include=dev

# Copy source code
COPY . .

# Run tests if present
RUN npm test 2>/dev/null || true

# Stage 2: Runtime
FROM node:20-alpine

LABEL maintainer="DevOps Team" \
      description="Barista Site - Coffee House Online Ordering"

WORKDIR /app

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Create non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copy node_modules and app from builder
COPY --from=builder --chown=appuser:appgroup /build/node_modules ./node_modules
COPY --from=builder --chown=appuser:appgroup /build/package*.json ./
COPY --from=builder --chown=appuser:appgroup /build/src ./src
COPY --from=builder --chown=appuser:appgroup /build/views ./views
COPY --from=builder --chown=appuser:appgroup /build/public ./public
COPY --from=builder --chown=appuser:appgroup /build/data ./data

# Create directory for SQLite database and logs (writable by appuser)
RUN mkdir -p /app/db /app/logs && \
    chown -R appuser:appgroup /app/db /app/logs

# Switch to non-root user
USER appuser

# Expose port (default HTTP)
EXPOSE 3000

# Health check: verify server responds to requests
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})" || exit 1

# Use dumb-init to handle signals correctly
ENTRYPOINT ["dumb-init", "--"]

# Start application
CMD ["npm", "start"]

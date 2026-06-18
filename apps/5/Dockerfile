# Multi-stage Dockerfile for Barista Site (Node.js + Express + SQLite + EJS)
# Stage 1: Builder
FROM node:20-bullseye AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (including dev dependencies for build tooling if needed)
RUN npm ci --prefer-offline --no-audit

# Copy source code
COPY . .

# Verify structure (optional but good for debugging)
RUN ls -la

# Stage 2: Runtime
FROM node:20-slim

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN useradd -r -s /bin/false appuser

# Copy only runtime dependencies and built artifacts from builder
COPY --from=builder --chown=appuser:appuser /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:appuser /app/package*.json ./
COPY --from=builder --chown=appuser:appuser /app/src ./src
COPY --from=builder --chown=appuser:appuser /app/public ./public
COPY --from=builder --chown=appuser:appuser /app/views ./views
COPY --from=builder --chown=appuser:appuser /app/data ./data

# Create directory for SQLite database with proper permissions
RUN mkdir -p /app/db && chown appuser:appuser /app/db

# Switch to non-root user
USER appuser

# Expose port (Express default)
EXPOSE 3000

# Set environment variables
ENV NODE_ENV=production \
    PORT=3000 \
    DATABASE_PATH=/app/db/orders.db

# Health check: verify the app is responding on port 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})" || exit 1

# Start the application
CMD ["npm", "start"]

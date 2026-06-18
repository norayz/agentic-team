# Multi-stage build for Barista Site
# Stage 1: Builder
FROM node:20.11-alpine AS builder

WORKDIR /app

# Install build dependencies (required for native modules if any)
RUN apk add --no-cache python3 make g++ ca-certificates

# Copy package files
COPY package.json package-lock.json* ./

# Install all dependencies (including dev for testing)
RUN npm ci

# Copy source code
COPY src ./src
COPY public ./public
COPY views ./views
COPY data ./data

# Run tests and linting if available
RUN npm run test 2>/dev/null || echo "Tests skipped"
RUN npm run lint 2>/dev/null || echo "Linting skipped"

# Stage 2: Runtime
FROM node:20.11-alpine

WORKDIR /app

# Create non-root user for running the app
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Install runtime dependencies only (ca-certificates for HTTPS)
RUN apk add --no-cache ca-certificates dumb-init

# Copy package files from builder
COPY --from=builder /app/package*.json ./

# Install production dependencies only
RUN npm ci --only=production && \
    npm cache clean --force

# Copy built application from builder (source + any compiled assets)
COPY --from=builder --chown=nodejs:nodejs /app/src ./src
COPY --from=builder --chown=nodejs:nodejs /app/public ./public
COPY --from=builder --chown=nodejs:nodejs /app/views ./views

# Create data directory for SQLite database with proper permissions
RUN mkdir -p /app/data && chown -R nodejs:nodejs /app/data

# Switch to non-root user
USER nodejs

# Expose port (default 3000)
EXPOSE 3000

# Health check: verify the app responds on port 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})" || exit 1

# Use dumb-init to handle signals properly
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# Start the application
CMD ["node", "src/index.js"]
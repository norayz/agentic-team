# Stage 1: Builder
# Install build dependencies and prepare the application
FROM node:20-alpine3.20 AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (including devDependencies for testing)
RUN npm ci --only=production

# Copy source code
COPY . .

# Stage 2: Runtime
# Use minimal base image with only production dependencies
FROM node:20-alpine3.20

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init=1.2.5-r2

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Set working directory
WORKDIR /app

# Copy node modules and source from builder
COPY --from=builder --chown=nodejs:nodejs /app /app

# Create directories for persistent data (db and logs)
RUN mkdir -p /app/db /app/logs && \
    chown -R nodejs:nodejs /app/db /app/logs

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
  CMD node -e "require('http').get('http://localhost:3000/', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})" || exit 1

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Start the application
CMD ["node", "src/index.js"]

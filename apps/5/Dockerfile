# Multi-stage build for barista site
# Stage 1: Builder - install dependencies and prepare app
FROM node:20.11-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (including devDependencies for build tools if needed)
RUN npm ci --only=production

# Copy application source
COPY . .

# Stage 2: Runtime - minimal image with only what's needed to run
FROM node:20.11-alpine

WORKDIR /app

# Create non-root user to run the application
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001

# Copy built dependencies from builder
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules

# Copy application source
COPY --from=builder --chown=nodejs:nodejs /app . 

# Create directory for persistent data (database)
RUN mkdir -p /app/data && chown -R nodejs:nodejs /app/data

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 3000

# Set environment variables
ENV NODE_ENV=production
ENV DATABASE_PATH=/app/data/barista.db
ENV PORT=3000

# Health check - test that the server is responding
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/', (res) => { if (res.statusCode !== 200) throw new Error('Health check failed'); })" || exit 1

# Start the application
CMD ["node", "src/server.js"]

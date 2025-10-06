# 🐳 Frontend Container - React + Nginx
# Multi-stage build for optimized production image

# Stage 1: Build React application
FROM node:18-alpine AS builder

LABEL maintainer="AI Absence & SOW Team"
LABEL description="Frontend container with React build and Nginx"

# Set working directory
WORKDIR /app

# Copy package files
COPY unified_ai_chat/frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production --silent

# Copy source code
COPY unified_ai_chat/frontend/ ./

# Build production bundle
RUN npm run build

# Stage 2: Production Nginx server
FROM nginx:1.24-alpine

# Install security updates
RUN apk update && apk upgrade && apk add --no-cache \
    curl \
    && rm -rf /var/cache/apk/*

# Copy built React app
COPY --from=builder /app/build /usr/share/nginx/html

# Copy custom Nginx configuration
COPY docker/frontend/nginx.conf /etc/nginx/nginx.conf
COPY docker/frontend/default.conf /etc/nginx/conf.d/default.conf

# Create nginx user and set permissions
RUN addgroup -g 1001 -S nginx-app && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx-app -g nginx-app nginx-app && \
    chown -R nginx-app:nginx-app /usr/share/nginx/html && \
    chown -R nginx-app:nginx-app /var/cache/nginx && \
    chown -R nginx-app:nginx-app /var/log/nginx && \
    chown -R nginx-app:nginx-app /etc/nginx/conf.d

# Switch to non-root user
USER nginx-app

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Expose port
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
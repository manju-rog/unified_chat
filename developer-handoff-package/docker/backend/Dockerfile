# 🐳 Backend Container - FastAPI + Gunicorn
# Production-ready Python container with security optimizations

FROM python:3.11-slim

LABEL maintainer="AI Absence & SOW Team"
LABEL description="FastAPI backend with Gunicorn WSGI server"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY unified_ai_chat/backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn uvicorn[standard] python-docx openpyxl

# Copy application code
COPY unified_ai_chat/backend/ .
COPY sow_gen_ai/ ./sow_gen_ai/

# Create necessary directories
RUN mkdir -p /app/logs /app/generated_docs && \
    chown -R appuser:appuser /app

# Copy startup script
COPY docker/backend/start.sh /start.sh
RUN chmod +x /start.sh && chown appuser:appuser /start.sh

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5002/api/health || exit 1

# Expose port
EXPOSE 5002

# Start application
CMD ["/start.sh"]
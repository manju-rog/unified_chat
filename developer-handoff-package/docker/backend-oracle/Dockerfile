# 🐳 Backend Dockerfile with Oracle Support
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Oracle client
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    unixodbc-dev \
    curl \
    libaio1 \
    && rm -rf /var/lib/apt/lists/*

# Install Oracle Instant Client
RUN mkdir -p /opt/oracle && \
    cd /opt/oracle && \
    curl -o instantclient-basic-linux.x64-21.1.0.0.0.zip \
    https://download.oracle.com/otn_software/linux/instantclient/211000/instantclient-basic-linux.x64-21.1.0.0.0.zip && \
    unzip instantclient-basic-linux.x64-21.1.0.0.0.zip && \
    rm instantclient-basic-linux.x64-21.1.0.0.0.zip && \
    echo /opt/oracle/instantclient_21_1 > /etc/ld.so.conf.d/oracle-instantclient.conf && \
    ldconfig

# Set Oracle environment variables
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_21_1:$LD_LIBRARY_PATH
ENV PATH=/opt/oracle/instantclient_21_1:$PATH

# Copy requirements first for better caching
COPY unified_ai_chat/backend/requirements.txt .
COPY unified_ai_chat/backend/requirements-oracle.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-oracle.txt

# Copy application code
COPY unified_ai_chat/backend/app ./app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5002

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5002/api/health || exit 1

# Start application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5002"]
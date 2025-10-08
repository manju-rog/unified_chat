# 🐳 Absence Service Container - Spring Boot
# Production-ready Java container with JVM optimizations

FROM openjdk:17-jre-slim

LABEL maintainer="AI Absence & SOW Team"
LABEL description="Spring Boot absence management service"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy Maven wrapper and pom.xml first for better caching
COPY ai_absence-ai_absence_mi/backend/absence-management/mvnw .
COPY ai_absence-ai_absence_mi/backend/absence-management/.mvn .mvn
COPY ai_absence-ai_absence_mi/backend/absence-management/pom.xml .

# Make mvnw executable
RUN chmod +x mvnw

# Copy source code
COPY ai_absence-ai_absence_mi/backend/absence-management/src src

# Build the application
RUN ./mvnw clean package -DskipTests && \
    mv target/*.jar app.jar && \
    rm -rf target .mvn mvnw pom.xml src

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/api/employees || exit 1

# Expose port
EXPOSE 8080

# JVM optimization for containers
ENV JAVA_OPTS="-XX:+UseContainerSupport \
               -XX:MaxRAMPercentage=75.0 \
               -XX:+UseG1GC \
               -XX:+UseStringDeduplication \
               -XX:+OptimizeStringConcat \
               -Djava.security.egd=file:/dev/./urandom"

# Start Spring Boot application
CMD ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
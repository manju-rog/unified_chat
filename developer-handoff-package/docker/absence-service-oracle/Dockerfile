# 🐳 Absence Service Dockerfile with Oracle Support
FROM openjdk:17-jdk-slim as builder

# Set working directory
WORKDIR /app

# Copy Maven wrapper and pom.xml
COPY ai_absence-ai_absence_mi/backend/absence-management/mvnw .
COPY ai_absence-ai_absence_mi/backend/absence-management/.mvn .mvn
COPY ai_absence-ai_absence_mi/backend/absence-management/pom.xml .

# Make mvnw executable
RUN chmod +x mvnw

# Download dependencies
RUN ./mvnw dependency:go-offline -B

# Copy source code
COPY ai_absence-ai_absence_mi/backend/absence-management/src src

# Build application
RUN ./mvnw clean package -DskipTests

# Production stage
FROM openjdk:17-jre-slim

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy JAR from builder stage
COPY --from=builder /app/target/absence-management-*.jar app.jar

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/actuator/health || exit 1

# JVM optimization for containers
ENV JAVA_OPTS="-Xms512m -Xmx1g -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -XX:+UseContainerSupport"

# Start application
CMD ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
# 📋 Deployment Requirements - AI Absence & SOW System

## 🎯 **System Requirements**

### **Minimum Infrastructure Requirements**
- **Kubernetes Cluster**: Version 1.24+
- **Container Runtime**: Docker or containerd
- **Storage**: 50GB available storage
- **Memory**: 8GB RAM minimum (16GB recommended)
- **CPU**: 4 cores minimum (8 cores recommended)
- **Network**: Internet access for AI API calls

### **Database Requirements**
- **PostgreSQL**: Version 13+
- **Storage**: 10GB minimum for database
- **Backup**: Regular backup strategy required
- **Performance**: Connection pooling recommended

---

## 🔧 **External Dependencies**

### **Required External Services**
1. **Google Gemini API**
   - **Purpose**: AI-powered chat functionality
   - **Requirement**: Valid API key
   - **Usage**: Chat responses and SOW generation
   - **Rate Limits**: Monitor API usage

2. **Container Registry**
   - **Purpose**: Store Docker images
   - **Options**: Docker Hub, Oracle Container Registry, AWS ECR, etc.
   - **Access**: Push/pull permissions required

### **Optional External Services**
1. **SSL Certificate Provider**
   - **Purpose**: HTTPS endpoints
   - **Options**: Let's Encrypt, commercial certificates
   
2. **DNS Provider**
   - **Purpose**: Domain name resolution
   - **Requirement**: If using custom domains

---

## 🏗️ **Infrastructure Components**

### **Kubernetes Resources Required**
```yaml
# Namespace
- Namespace: ai-absence-sow

# Compute Resources
- Deployments: 4 (frontend, backend, absence-service, postgres)
- Services: 4 (ClusterIP services)
- ConfigMaps: 2 (app-config, postgres-init-scripts)
- Secrets: 1 (app-secrets)
- PersistentVolumeClaims: 1 (postgres-pvc)

# Optional (DevOps to implement)
- Ingress: 1 (for external access)
- HorizontalPodAutoscaler: 3 (for auto-scaling)
- NetworkPolicies: Multiple (for security)
```

### **Resource Allocation**
```yaml
Frontend:
  requests: { cpu: 100m, memory: 128Mi }
  limits: { cpu: 500m, memory: 512Mi }
  replicas: 2

Backend:
  requests: { cpu: 200m, memory: 256Mi }
  limits: { cpu: 1000m, memory: 1Gi }
  replicas: 2

Absence Service:
  requests: { cpu: 200m, memory: 512Mi }
  limits: { cpu: 1000m, memory: 2Gi }
  replicas: 2

PostgreSQL:
  requests: { cpu: 200m, memory: 512Mi }
  limits: { cpu: 1000m, memory: 2Gi }
  replicas: 1
  storage: 10Gi
```

---

## 🔒 **Security Requirements**

### **Secrets Management**
```bash
# Required Secrets
DB_USERNAME=postgres
DB_PASSWORD=<secure_password>
GEMINI_API_KEY=<your_api_key>

# DevOps Responsibilities:
- Use proper secret management (Vault, Sealed Secrets, etc.)
- Rotate secrets regularly
- Never store secrets in plain text
- Use RBAC for secret access
```

### **Network Security**
- **Internal Communication**: All services communicate within cluster
- **External Access**: Only frontend should be externally accessible
- **Database Access**: Restrict to application services only
- **API Security**: Implement authentication/authorization (DevOps responsibility)

### **Container Security**
- **Non-root Users**: All containers run as non-root
- **Read-only Filesystems**: Where possible
- **Security Contexts**: Implemented in deployments
- **Image Scanning**: Recommended for production

---

## 🌐 **Networking Requirements**

### **Service Communication**
```
Frontend (Port 80)
    ↓
Backend (Port 5002) ←→ Absence Service (Port 8080)
    ↓                        ↓
PostgreSQL (Port 5432) ←────┘
```

### **External Connectivity**
- **Outbound Internet**: Required for Gemini API calls
- **Inbound Traffic**: Only to frontend (via Ingress/LoadBalancer)
- **DNS Resolution**: Internal service discovery via Kubernetes DNS

### **Port Requirements**
- **Frontend**: 80 (HTTP)
- **Backend**: 5002 (HTTP API)
- **Absence Service**: 8080 (HTTP API)
- **PostgreSQL**: 5432 (Database)

---

## 📊 **Monitoring & Observability**

### **Health Check Endpoints**
```bash
# Application Health Checks
GET /api/health           # Backend
GET /actuator/health      # Absence Service
GET /                     # Frontend (returns HTML)

# Database Health
# PostgreSQL connection check via applications
```

### **Logging Requirements**
- **Log Format**: JSON structured logs preferred
- **Log Levels**: INFO for production, DEBUG for troubleshooting
- **Log Retention**: As per organizational policy
- **Centralized Logging**: Recommended (ELK, Fluentd, etc.)

### **Metrics Collection**
- **Application Metrics**: Custom metrics via /metrics endpoints
- **Infrastructure Metrics**: CPU, memory, disk, network
- **Business Metrics**: Chat sessions, absence requests, SOW generation

---

## 🔄 **Deployment Strategy**

### **Recommended Deployment Approach**
1. **Blue-Green Deployment**: For zero-downtime updates
2. **Rolling Updates**: Default Kubernetes strategy
3. **Canary Deployment**: For gradual rollouts

### **Deployment Order**
1. **Database**: Deploy PostgreSQL first
2. **Backend Services**: Deploy backend and absence service
3. **Frontend**: Deploy frontend last
4. **Verification**: Run health checks

### **Rollback Strategy**
- **Database**: Backup before schema changes
- **Applications**: Keep previous image versions
- **Configuration**: Version control all configs

---

## 🚀 **Environment-Specific Configurations**

### **Development Environment**
```yaml
replicas: 1 (all services)
resources: minimal
storage: 5Gi
monitoring: basic
security: relaxed
```

### **Staging Environment**
```yaml
replicas: 1-2 (per service)
resources: moderate
storage: 10Gi
monitoring: full
security: production-like
```

### **Production Environment**
```yaml
replicas: 2+ (per service)
resources: as specified above
storage: 20Gi+
monitoring: comprehensive
security: full hardening
```

---

## 📋 **Pre-Deployment Checklist**

### **Infrastructure Readiness**
- [ ] Kubernetes cluster is operational
- [ ] Container registry is accessible
- [ ] Storage classes are configured
- [ ] Network policies are defined (if required)
- [ ] SSL certificates are available (if required)

### **Application Readiness**
- [ ] Docker images are built and pushed
- [ ] Database schema is ready
- [ ] Configuration values are set
- [ ] Secrets are created securely
- [ ] Health check endpoints are working

### **Security Readiness**
- [ ] RBAC policies are defined
- [ ] Network security is configured
- [ ] Secrets management is implemented
- [ ] Container security is enforced
- [ ] Access controls are in place

### **Operational Readiness**
- [ ] Monitoring is configured
- [ ] Logging is set up
- [ ] Backup strategy is implemented
- [ ] Alerting rules are defined
- [ ] Runbooks are available

---

## 🆘 **Support & Escalation**

### **Developer Responsibilities**
- Application code and logic
- Docker image definitions
- Database schema and migrations
- API documentation
- Unit and integration tests

### **DevOps Responsibilities**
- Infrastructure provisioning
- Security implementation
- Monitoring and alerting
- Backup and disaster recovery
- Performance optimization
- Production troubleshooting

### **Escalation Path**
1. **Level 1**: Application logs and health checks
2. **Level 2**: Infrastructure and platform issues
3. **Level 3**: Developer team for application-specific issues

---

## 📞 **Contact Information**
- **Development Team**: [Contact Information]
- **Repository**: https://github.com/manju-rog/unified_chat
- **Branch**: production-deployment
- **Documentation**: See API_DOCUMENTATION.md and BUILD_INSTRUCTIONS.md
# 👨‍💻 Developer Handoff Package - AI Absence & SOW System

## 📋 **What's Included (Developer Deliverables Only)**

This package contains **only what developers should provide** to DevOps teams for deployment. No DevOps tooling or infrastructure automation included.

### 🎯 **Application Components**
- **Frontend**: React application with complete source code
- **Backend**: FastAPI Python application with all APIs
- **Absence Service**: Spring Boot Java microservice
- **Database**: PostgreSQL schema and initialization scripts

### 📦 **Developer Responsibilities Covered**
- ✅ Application source code (ready to build)
- ✅ Dockerfiles (container definitions)
- ✅ Database schema and seed data
- ✅ Environment configuration templates
- ✅ API documentation
- ✅ Build instructions
- ✅ Application requirements and dependencies
- ✅ Basic deployment manifests (as reference)

### 🚫 **NOT Included (DevOps Responsibilities)**
- ❌ Infrastructure provisioning (Terraform)
- ❌ CI/CD pipelines
- ❌ Monitoring and logging setup
- ❌ Security policies and RBAC
- ❌ Backup and disaster recovery
- ❌ Performance optimization
- ❌ Production secrets management
- ❌ Load balancers and ingress controllers

---

## 🏗️ **Application Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │ Absence Service │
│   (React)       │────│   (FastAPI)     │────│  (Spring Boot)  │
│   Port: 80      │    │   Port: 5002    │    │   Port: 8080    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                │
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │   Port: 5432    │
                       └─────────────────┘
```

## 📋 **Deployment Requirements**

### **System Requirements**
- **Container Runtime**: Docker or compatible
- **Orchestration**: Kubernetes 1.24+
- **Database**: PostgreSQL 13+ OR Oracle Database XE 21c+
- **Storage**: 20GB minimum (50GB for Oracle)
- **Memory**: 4GB minimum (8GB for Oracle)
- **CPU**: 2 cores minimum (4 cores for Oracle)

### **External Dependencies**
- **Gemini API**: Google Generative AI API key required
- **Internet Access**: Required for AI API calls
- **SSL Certificates**: For HTTPS endpoints (DevOps to provide)
- **Database**: PostgreSQL 13+ OR Oracle Database XE 21c+
- **Oracle Registry**: Access required if using Oracle database option

### **Environment Variables Required**
```bash
# Backend Configuration
GEMINI_API_KEY=your_gemini_api_key_here
DB_HOST=postgres-service
DB_PORT=5432
DB_NAME=ai_absence_db
DB_USERNAME=postgres
DB_PASSWORD=your_secure_password

# Frontend Configuration
REACT_APP_API_URL=http://backend-service:5002
REACT_APP_ABSENCE_API_URL=http://absence-service:8080
```

## 🚀 **Quick Start for DevOps**

### **1. Build Applications**
```bash
# Frontend
cd frontend/
npm install
npm run build

# Backend
cd backend/
pip install -r requirements.txt

# Absence Service
cd absence-service/
./mvnw clean package
```

### **2. Build Docker Images**
```bash
docker build -f docker/frontend/Dockerfile -t ai-absence-frontend .
docker build -f docker/backend/Dockerfile -t ai-absence-backend .
docker build -f docker/absence-service/Dockerfile -t ai-absence-service .
```

### **3. Deploy to Kubernetes**
```bash
# Option A: PostgreSQL (default)
kubectl apply -f k8s-manifests/namespace.yaml
kubectl apply -f k8s-manifests/configmap.yaml
kubectl apply -f k8s-manifests/secrets-template.yaml  # Update with real secrets
kubectl apply -f k8s-manifests/database-*.yaml
kubectl apply -f k8s-manifests/*-deployment.yaml

# Option B: Oracle Database
kubectl apply -f k8s-manifests/namespace.yaml
kubectl apply -f k8s-manifests/oracle-configmap.yaml
kubectl apply -f k8s-manifests/oracle-secrets-template.yaml  # Update with real secrets
kubectl apply -f k8s-manifests/oracle-database-*.yaml
kubectl apply -f k8s-manifests/oracle-*-deployment.yaml
```

## 📞 **Developer Contact**
- **Team**: AI Development Team
- **Contact**: [Your Contact Information]
- **Repository**: https://github.com/manju-rog/unified_chat
- **Branch**: production-deployment

---

**Note**: This package contains only application code and basic deployment templates. DevOps team is responsible for production infrastructure, security, monitoring, and operational concerns.
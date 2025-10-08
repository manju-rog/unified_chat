# 🗄️ Database Deployment Options

## 📋 **Available Database Options**

The AI Absence & SOW System supports two database options:

### **Option 1: PostgreSQL (Default)**
- **Files**: `database-deployment.yaml`, `database-init.yaml`
- **ConfigMap**: `configmap.yaml`
- **Secrets**: `secrets-template.yaml`
- **Services**: `backend-deployment.yaml`, `absence-service-deployment.yaml`

### **Option 2: Oracle Database**
- **Files**: `oracle-database-deployment.yaml`, `oracle-database-init.yaml`
- **ConfigMap**: `oracle-configmap.yaml`
- **Secrets**: `oracle-secrets-template.yaml`
- **Services**: `oracle-backend-deployment.yaml`, `oracle-absence-service-deployment.yaml`

---

## 🚀 **PostgreSQL Deployment (Default)**

### **Quick Deploy:**
```bash
# Deploy PostgreSQL version
kubectl apply -f k8s-manifests/namespace.yaml
kubectl apply -f k8s-manifests/configmap.yaml
kubectl apply -f k8s-manifests/secrets-template.yaml  # Update with real secrets first
kubectl apply -f k8s-manifests/database-init.yaml
kubectl apply -f k8s-manifests/database-deployment.yaml
kubectl apply -f k8s-manifests/backend-deployment.yaml
kubectl apply -f k8s-manifests/absence-service-deployment.yaml
kubectl apply -f k8s-manifests/frontend-deployment.yaml
```

### **Docker Images:**
```bash
docker build -f docker/frontend/Dockerfile -t ai-absence-frontend:latest .
docker build -f docker/backend/Dockerfile -t ai-absence-backend:latest .
docker build -f docker/absence-service/Dockerfile -t ai-absence-service:latest .
```

---

## 🔶 **Oracle Database Deployment**

### **Prerequisites:**
1. **Oracle Container Registry Access**
   ```bash
   docker login container-registry.oracle.com
   # Use your Oracle account credentials
   ```

2. **Accept Oracle License**
   - Visit Oracle Container Registry
   - Accept license for Oracle Database Express Edition

### **Quick Deploy:**
```bash
# Deploy Oracle version
kubectl apply -f k8s-manifests/namespace.yaml
kubectl apply -f k8s-manifests/oracle-configmap.yaml
kubectl apply -f k8s-manifests/oracle-secrets-template.yaml  # Update with real secrets first
kubectl apply -f k8s-manifests/oracle-database-init.yaml
kubectl apply -f k8s-manifests/oracle-database-deployment.yaml
kubectl apply -f k8s-manifests/oracle-backend-deployment.yaml
kubectl apply -f k8s-manifests/oracle-absence-service-deployment.yaml
kubectl apply -f k8s-manifests/frontend-deployment.yaml
```

### **Docker Images:**
```bash
docker build -f docker/frontend/Dockerfile -t ai-absence-frontend:latest .
docker build -f docker/backend-oracle/Dockerfile -t ai-absence-backend-oracle:latest .
docker build -f docker/absence-service-oracle/Dockerfile -t ai-absence-service-oracle:latest .
```

---

## ⚙️ **Configuration Differences**

### **PostgreSQL Configuration:**
```yaml
# configmap.yaml
DB_HOST: "postgres-service"
DB_PORT: "5432"
DB_NAME: "ai_absence_db"

# Backend environment
DATABASE_URL: "postgresql://user:pass@postgres-service:5432/ai_absence_db"

# Spring Boot
spring.datasource.url: jdbc:postgresql://postgres-service:5432/ai_absence_db
spring.jpa.database-platform: org.hibernate.dialect.PostgreSQLDialect
```

### **Oracle Configuration:**
```yaml
# oracle-configmap.yaml
DB_HOST: "oracle-service"
DB_PORT: "1521"
DB_SERVICE_NAME: "XE"
DB_SCHEMA: "ai_absence"

# Backend environment
DATABASE_URL: "oracle+cx_oracle://user:pass@oracle-service:1521/XE"

# Spring Boot
spring.datasource.url: jdbc:oracle:thin:@oracle-service:1521:XE
spring.jpa.database-platform: org.hibernate.dialect.Oracle12cDialect
```

---

## 🔒 **Secrets Configuration**

### **PostgreSQL Secrets:**
```bash
# secrets-template.yaml
DB_USERNAME: postgres (base64: cG9zdGdyZXM=)
DB_PASSWORD: your_postgres_password
GEMINI_API_KEY: your_gemini_api_key
```

### **Oracle Secrets:**
```bash
# oracle-secrets-template.yaml
DB_USERNAME: ai_absence (base64: YWlfYWJzZW5jZQ==)
DB_PASSWORD: ai_absence_password
ORACLE_PASSWORD: oracle_system_password
GEMINI_API_KEY: your_gemini_api_key
```

---

## 📊 **Resource Requirements**

### **PostgreSQL:**
```yaml
Database:
  requests: { cpu: 200m, memory: 512Mi }
  limits: { cpu: 1000m, memory: 2Gi }
  storage: 10Gi
```

### **Oracle:**
```yaml
Database:
  requests: { cpu: 500m, memory: 2Gi }
  limits: { cpu: 2000m, memory: 4Gi }
  storage: 20Gi
```

---

## 🔄 **Migration Between Databases**

### **From PostgreSQL to Oracle:**
1. **Export data** from PostgreSQL
2. **Deploy Oracle** version
3. **Transform and import** data to Oracle
4. **Update application** configurations
5. **Switch traffic** to Oracle version

### **From Oracle to PostgreSQL:**
1. **Export data** from Oracle
2. **Deploy PostgreSQL** version
3. **Transform and import** data to PostgreSQL
4. **Update application** configurations
5. **Switch traffic** to PostgreSQL version

---

## 🛠️ **Development vs Production**

### **Development (Recommended: PostgreSQL)**
- **Easier setup** and local development
- **Smaller resource footprint**
- **Free and open source**
- **Better tooling** and community support

### **Production (Choose based on requirements)**

#### **Use PostgreSQL when:**
- Cost optimization is important
- Open source preference
- Smaller to medium scale applications
- Cloud-native deployments

#### **Use Oracle when:**
- Enterprise requirements
- Existing Oracle infrastructure
- Advanced database features needed
- Large scale applications

---

## 📞 **Support Notes**

### **PostgreSQL Support:**
- **Community**: Large open source community
- **Documentation**: Extensive online resources
- **Tooling**: Wide variety of tools available
- **Cloud**: Supported by all major cloud providers

### **Oracle Support:**
- **Enterprise**: Oracle enterprise support available
- **Documentation**: Comprehensive Oracle documentation
- **Tooling**: Oracle-specific tools and utilities
- **Licensing**: Commercial licensing considerations

---

## 🎯 **Recommendation**

### **For Most Use Cases: PostgreSQL**
- Easier to deploy and manage
- Lower resource requirements
- No licensing costs
- Excellent performance for most applications

### **For Enterprise Environments: Oracle**
- If already using Oracle infrastructure
- Need for advanced Oracle-specific features
- Enterprise support requirements
- Large scale, high-performance needs

**Choose the option that best fits your infrastructure and requirements!**
# 🔨 Build Instructions - AI Absence & SOW System

## 📋 **Prerequisites**
- **Docker**: Version 20.0+
- **Node.js**: Version 18+
- **Python**: Version 3.9+
- **Java**: Version 17+
- **Maven**: Version 3.8+

---

## 🏗️ **Building Applications**

### **1. Frontend (React)**
```bash
cd unified_ai_chat/frontend/

# Install dependencies
npm install

# Build for production
npm run build

# Output: build/ directory with static files
```

### **2. Backend (FastAPI)**
```bash
cd unified_ai_chat/backend/

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests (optional)
python -m pytest tests/

# Application is ready to run
```

### **3. Absence Service (Spring Boot)**
```bash
cd ai_absence-ai_absence_mi/backend/absence-management/

# Build with Maven
./mvnw clean package

# Output: target/absence-management-1.0.0.jar
```

---

## 🐳 **Building Docker Images**

### **Build All Images**
```bash
# From project root directory

# Frontend
docker build -f docker/frontend/Dockerfile -t ai-absence-frontend:latest .

# Backend
docker build -f docker/backend/Dockerfile -t ai-absence-backend:latest .

# Absence Service
docker build -f docker/absence-service/Dockerfile -t ai-absence-service:latest .
```

### **Verify Images**
```bash
docker images | grep ai-absence
```

### **Test Images Locally**
```bash
# Test frontend
docker run -p 3000:80 ai-absence-frontend:latest

# Test backend (requires environment variables)
docker run -p 5002:5002 \
  -e GEMINI_API_KEY=your_key \
  -e DB_HOST=localhost \
  ai-absence-backend:latest

# Test absence service
docker run -p 8080:8080 \
  -e SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/ai_absence_db \
  ai-absence-service:latest
```

---

## 🔧 **Development Setup**

### **Local Development Environment**
```bash
# 1. Start PostgreSQL database
docker run -d \
  --name postgres-dev \
  -e POSTGRES_DB=ai_absence_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:13

# 2. Start Backend
cd unified_ai_chat/backend/
export GEMINI_API_KEY=your_api_key
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=ai_absence_db
export DB_USERNAME=postgres
export DB_PASSWORD=password
python -m uvicorn app.main:app --host 0.0.0.0 --port 5002 --reload

# 3. Start Absence Service
cd ai_absence-ai_absence_mi/backend/absence-management/
export SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/ai_absence_db
export SPRING_DATASOURCE_USERNAME=postgres
export SPRING_DATASOURCE_PASSWORD=password
java -jar target/absence-management-1.0.0.jar

# 4. Start Frontend
cd unified_ai_chat/frontend/
export REACT_APP_API_URL=http://localhost:5002
export REACT_APP_ABSENCE_API_URL=http://localhost:8080
npm start
```

---

## 📦 **Packaging for Deployment**

### **Create Deployment Package**
```bash
# Create deployment directory
mkdir ai-absence-deployment
cd ai-absence-deployment

# Copy built applications
cp -r ../unified_ai_chat ./
cp -r ../ai_absence-ai_absence_mi ./
cp -r ../docker ./
cp -r ../k8s-manifests ./

# Copy documentation
cp ../API_DOCUMENTATION.md ./
cp ../BUILD_INSTRUCTIONS.md ./
cp ../README.md ./

# Create archive
tar -czf ai-absence-system-v1.0.0.tar.gz .
```

### **Container Registry Push**
```bash
# Tag images for registry
docker tag ai-absence-frontend:latest your-registry/ai-absence-frontend:v1.0.0
docker tag ai-absence-backend:latest your-registry/ai-absence-backend:v1.0.0
docker tag ai-absence-service:latest your-registry/ai-absence-service:v1.0.0

# Push to registry
docker push your-registry/ai-absence-frontend:v1.0.0
docker push your-registry/ai-absence-backend:v1.0.0
docker push your-registry/ai-absence-service:v1.0.0
```

---

## 🧪 **Testing**

### **Unit Tests**
```bash
# Backend tests
cd unified_ai_chat/backend/
python -m pytest tests/ -v

# Frontend tests
cd unified_ai_chat/frontend/
npm test

# Absence Service tests
cd ai_absence-ai_absence_mi/backend/absence-management/
./mvnw test
```

### **Integration Tests**
```bash
# Start all services locally first, then:
curl http://localhost:5002/api/health
curl http://localhost:8080/actuator/health
curl http://localhost:3000/
```

### **Docker Image Tests**
```bash
# Test image builds
docker build -f docker/frontend/Dockerfile -t test-frontend .
docker build -f docker/backend/Dockerfile -t test-backend .
docker build -f docker/absence-service/Dockerfile -t test-absence .

# Test image runs
docker run --rm test-frontend nginx -t
docker run --rm test-backend python -c "import app.main; print('OK')"
docker run --rm test-absence java -version
```

---

## 🔍 **Troubleshooting Build Issues**

### **Common Frontend Issues**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Fix permission issues
sudo chown -R $(whoami) ~/.npm
```

### **Common Backend Issues**
```bash
# Python dependency conflicts
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall

# Virtual environment issues
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
```

### **Common Java Issues**
```bash
# Maven cache issues
./mvnw dependency:purge-local-repository

# Java version issues
export JAVA_HOME=/path/to/java17
./mvnw clean package
```

### **Docker Build Issues**
```bash
# Clear Docker cache
docker system prune -a

# Build with no cache
docker build --no-cache -f docker/frontend/Dockerfile .

# Check Docker daemon
docker info
```

---

## 📊 **Build Verification**

### **Successful Build Checklist**
- [ ] Frontend builds without errors (`npm run build`)
- [ ] Backend installs dependencies (`pip install -r requirements.txt`)
- [ ] Absence Service compiles (`./mvnw clean package`)
- [ ] All Docker images build successfully
- [ ] Docker images run without immediate crashes
- [ ] Health endpoints respond correctly
- [ ] Database schema initializes properly

### **Build Artifacts**
- **Frontend**: `unified_ai_chat/frontend/build/`
- **Backend**: `unified_ai_chat/backend/` (source code)
- **Absence Service**: `ai_absence-ai_absence_mi/backend/absence-management/target/absence-management-1.0.0.jar`
- **Docker Images**: `ai-absence-frontend:latest`, `ai-absence-backend:latest`, `ai-absence-service:latest`

---

## 📞 **Build Support**
- **Issues**: Check application logs and build output
- **Dependencies**: Ensure all prerequisites are installed
- **Environment**: Verify environment variables are set correctly
- **Contact**: Development Team for build-related questions
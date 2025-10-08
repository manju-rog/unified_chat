# 🚀 Complete Local Deployment Guide for Venkat's Team

## 👥 **For: Anushri & Shreyas (New Team Members)**
**Manager: Venkat**  
**System: Ubuntu/Linux with Docker**  
**Database: SQLite (Current) → PostgreSQL/Oracle (Production Ready)**

---

## 🎯 **What We're Deploying**
**AI Absence & SOW System** - Complete application with:
- **Frontend**: React web application
- **Backend**: FastAPI Python service  
- **Absence Service**: Spring Boot Java service
- **Database**: SQLite (current) + PostgreSQL/Oracle options
- **AI Integration**: Google Gemini API

---

## 📋 **Prerequisites Setup**

### **Step 1: System Requirements**
```bash
# Check your Ubuntu version
lsb_release -a

# Minimum requirements:
# - Ubuntu 18.04+ or similar Linux
# - 8GB RAM
# - 20GB free disk space
# - Internet connection
```

### **Step 2: Install Docker**
```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (avoid sudo)
sudo usermod -aG docker $USER

# Logout and login again, then test
docker --version
docker run hello-world
```

### **Step 3: Install Docker Compose**
```bash
# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Test installation
docker-compose --version
```

### **Step 4: Install Additional Tools**
```bash
# Install Git, Node.js, Python, Java
sudo apt install -y git curl wget

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Python 3.9+
sudo apt install -y python3 python3-pip python3-venv

# Install Java 17
sudo apt install -y openjdk-17-jdk maven

# Verify installations
node --version
python3 --version
java -version
mvn --version
```

---

## 📁 **Project Setup**

### **Step 1: Clone the Repository**
```bash
# Create workspace directory
mkdir -p ~/workspace
cd ~/workspace

# Clone the project
git clone https://github.com/manju-rog/unified_chat.git
cd unified_chat

# Switch to production branch
git checkout production-deployment

# Check project structure
ls -la
```

### **Step 2: Environment Configuration**
```bash
# Copy environment template
cp sow_gen_ai/.env.example sow_gen_ai/.env

# Edit environment file
nano sow_gen_ai/.env
```

**Add these values to `.env`:**
```bash
# Google Gemini API Key (get from Google AI Studio)
GEMINI_API_KEY=your_gemini_api_key_here

# Database Configuration (SQLite - current)
DATABASE_URL=sqlite:///./ai_absence.db

# API URLs (for local development)
REACT_APP_API_URL=http://localhost:5002
REACT_APP_ABSENCE_API_URL=http://localhost:8080

# Application Settings
APP_ENV=development
LOG_LEVEL=DEBUG
```

---

## 🗄️ **Database Options**

### **Option 1: Keep SQLite (Easiest - Current Setup)**
```bash
# SQLite is already configured
# Database file: ai_absence.db
# No additional setup needed
echo "Using SQLite - no additional setup required"
```

### **Option 2: Upgrade to PostgreSQL (Recommended)**
```bash
# Install PostgreSQL locally
sudo apt install -y postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE ai_absence_db;
CREATE USER ai_absence WITH PASSWORD 'ai_absence_password';
GRANT ALL PRIVILEGES ON DATABASE ai_absence_db TO ai_absence;
\q
EOF

# Update .env file
nano sow_gen_ai/.env
# Change DATABASE_URL to:
# DATABASE_URL=postgresql://ai_absence:ai_absence_password@localhost:5432/ai_absence_db
```

### **Option 3: Use Docker PostgreSQL (Recommended for Beginners)**
```bash
# Create docker-compose.yml for database
cat > docker-compose-db.yml << EOF
version: '3.8'
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: ai_absence_db
      POSTGRES_USER: ai_absence
      POSTGRES_PASSWORD: ai_absence_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
EOF

# Start PostgreSQL in Docker
docker-compose -f docker-compose-db.yml up -d

# Check if running
docker ps

# Update .env file
# DATABASE_URL=postgresql://ai_absence:ai_absence_password@localhost:5432/ai_absence_db
```

---

## 🏗️ **Application Build & Run**

### **Method 1: Local Development (Recommended for Development)**

#### **Step 1: Backend Setup**
```bash
# Navigate to backend
cd unified_ai_chat/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (if using PostgreSQL)
# python -m alembic upgrade head

# Start backend server
python -m uvicorn app.main:app --host 0.0.0.0 --port 5002 --reload

# Backend will be available at: http://localhost:5002
# API docs at: http://localhost:5002/docs
```

#### **Step 2: Frontend Setup (New Terminal)**
```bash
# Navigate to frontend
cd ~/workspace/unified_chat/unified_ai_chat/frontend

# Install dependencies
npm install

# Start development server
npm start

# Frontend will be available at: http://localhost:3000
```

#### **Step 3: Absence Service Setup (New Terminal)**
```bash
# Navigate to absence service
cd ~/workspace/unified_chat/ai_absence-ai_absence_mi/backend/absence-management

# Build the application
./mvnw clean package

# Run the service
java -jar target/absence-management-*.jar

# Service will be available at: http://localhost:8080
# Health check: http://localhost:8080/actuator/health
```

### **Method 2: Docker Deployment (Recommended for Production-like Testing)**

#### **Step 1: Build Docker Images**
```bash
# Navigate to project root
cd ~/workspace/unified_chat

# Build all images
docker build -f docker/frontend/Dockerfile -t ai-absence-frontend .
docker build -f docker/backend/Dockerfile -t ai-absence-backend .
docker build -f docker/absence-service/Dockerfile -t ai-absence-service .

# Verify images
docker images | grep ai-absence
```

#### **Step 2: Create Complete Docker Compose**
```bash
# Create complete docker-compose.yml
cat > docker-compose-full.yml << EOF
version: '3.8'

services:
  # Database
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: ai_absence_db
      POSTGRES_USER: ai_absence
      POSTGRES_PASSWORD: ai_absence_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./k8s/database/postgres-init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ai_absence -d ai_absence_db"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Backend API
  backend:
    image: ai-absence-backend
    environment:
      - GEMINI_API_KEY=\${GEMINI_API_KEY}
      - DATABASE_URL=postgresql://ai_absence:ai_absence_password@postgres:5432/ai_absence_db
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=ai_absence_db
      - DB_USERNAME=ai_absence
      - DB_PASSWORD=ai_absence_password
    ports:
      - "5002:5002"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5002/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Absence Service
  absence-service:
    image: ai-absence-service
    environment:
      - SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/ai_absence_db
      - SPRING_DATASOURCE_USERNAME=ai_absence
      - SPRING_DATASOURCE_PASSWORD=ai_absence_password
      - SPRING_PROFILES_ACTIVE=production
    ports:
      - "8080:8080"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Frontend
  frontend:
    image: ai-absence-frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
      - absence-service
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:

networks:
  default:
    name: ai-absence-network
EOF
```

#### **Step 3: Deploy with Docker Compose**
```bash
# Set environment variables
export GEMINI_API_KEY="your_actual_gemini_api_key_here"

# Start all services
docker-compose -f docker-compose-full.yml up -d

# Check status
docker-compose -f docker-compose-full.yml ps

# View logs
docker-compose -f docker-compose-full.yml logs -f

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:5002/docs
# Absence Service: http://localhost:8080/actuator/health
```

---

## 🧪 **Testing the Deployment**

### **Step 1: Health Checks**
```bash
# Test backend
curl http://localhost:5002/api/health

# Test absence service
curl http://localhost:8080/actuator/health

# Test frontend (should return HTML)
curl http://localhost:3000
```

### **Step 2: API Testing**
```bash
# Test backend API
curl -X GET "http://localhost:5002/api/employees"

# Test chat functionality
curl -X POST "http://localhost:5002/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test123"}'

# Test absence service
curl -X GET "http://localhost:8080/api/employees"
```

### **Step 3: Web Interface Testing**
```bash
# Open in browser
firefox http://localhost:3000
# or
google-chrome http://localhost:3000

# Test features:
# 1. Chat interface
# 2. Absence requests
# 3. SOW generation
# 4. Employee management
```

---

## 🔧 **Troubleshooting Common Issues**

### **Issue 1: Docker Permission Denied**
```bash
# Solution: Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again
```

### **Issue 2: Port Already in Use**
```bash
# Check what's using the port
sudo netstat -tulpn | grep :5002

# Kill the process
sudo kill -9 <process_id>

# Or use different ports in docker-compose
```

### **Issue 3: Database Connection Failed**
```bash
# Check PostgreSQL is running
docker-compose -f docker-compose-full.yml ps postgres

# Check database logs
docker-compose -f docker-compose-full.yml logs postgres

# Reset database
docker-compose -f docker-compose-full.yml down -v
docker-compose -f docker-compose-full.yml up -d
```

### **Issue 4: Frontend Not Loading**
```bash
# Check if backend is running
curl http://localhost:5002/api/health

# Check frontend logs
docker-compose -f docker-compose-full.yml logs frontend

# Rebuild frontend image
docker build -f docker/frontend/Dockerfile -t ai-absence-frontend . --no-cache
```

### **Issue 5: Gemini API Not Working**
```bash
# Check API key is set
echo $GEMINI_API_KEY

# Test API key manually
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

---

## 📊 **Monitoring & Logs**

### **View Application Logs**
```bash
# All services
docker-compose -f docker-compose-full.yml logs -f

# Specific service
docker-compose -f docker-compose-full.yml logs -f backend
docker-compose -f docker-compose-full.yml logs -f frontend
docker-compose -f docker-compose-full.yml logs -f absence-service
docker-compose -f docker-compose-full.yml logs -f postgres
```

### **Monitor Resource Usage**
```bash
# Docker stats
docker stats

# System resources
htop
# or
top
```

### **Database Management**
```bash
# Connect to PostgreSQL
docker-compose -f docker-compose-full.yml exec postgres psql -U ai_absence -d ai_absence_db

# Common SQL commands:
# \dt - list tables
# SELECT * FROM employees;
# SELECT * FROM absence_requests;
```

---

## 🛑 **Stop and Cleanup**

### **Stop Services**
```bash
# Stop all services
docker-compose -f docker-compose-full.yml down

# Stop and remove volumes (WARNING: deletes data)
docker-compose -f docker-compose-full.yml down -v

# Stop individual services
docker-compose -f docker-compose-full.yml stop backend
```

### **Cleanup Docker**
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune

# Complete cleanup (WARNING: removes everything)
docker system prune -a --volumes
```

---

## 📋 **Quick Reference Commands**

### **Daily Development Workflow**
```bash
# Start everything
cd ~/workspace/unified_chat
export GEMINI_API_KEY="your_key_here"
docker-compose -f docker-compose-full.yml up -d

# Check status
docker-compose -f docker-compose-full.yml ps

# View logs
docker-compose -f docker-compose-full.yml logs -f

# Access application: http://localhost:3000

# Stop everything
docker-compose -f docker-compose-full.yml down
```

### **Development Mode (Code Changes)**
```bash
# For code changes, use local development:
# Terminal 1: Backend
cd unified_ai_chat/backend && source venv/bin/activate && python -m uvicorn app.main:app --reload

# Terminal 2: Frontend  
cd unified_ai_chat/frontend && npm start

# Terminal 3: Absence Service
cd ai_absence-ai_absence_mi/backend/absence-management && java -jar target/*.jar
```

---

## 🎯 **Success Checklist**

### **✅ Deployment Successful When:**
- [ ] All Docker containers are running (`docker ps`)
- [ ] Frontend loads at http://localhost:3000
- [ ] Backend API docs load at http://localhost:5002/docs
- [ ] Absence service health check passes at http://localhost:8080/actuator/health
- [ ] Database connection works (can see tables)
- [ ] Chat interface responds to messages
- [ ] Can create absence requests
- [ ] Can generate SOW documents

### **✅ Ready for Team Demo When:**
- [ ] All services start with one command
- [ ] Application is accessible via web browser
- [ ] Core features work (chat, absence, SOW)
- [ ] Database persists data between restarts
- [ ] Logs show no critical errors

---

## 📞 **Support & Next Steps**

### **For Anushri & Shreyas:**
1. **Start with Method 2 (Docker)** - easier and more reliable
2. **Use PostgreSQL option** - more production-like
3. **Test each component** individually first
4. **Ask questions** if anything is unclear
5. **Document any issues** you encounter

### **For Venkat:**
- **Deployment time**: 30-60 minutes for first setup
- **Daily startup**: 2-3 minutes
- **Resource usage**: ~4GB RAM, ~10GB disk
- **Team readiness**: After successful deployment, team can demo and develop

### **Production Deployment:**
- Use the `developer-handoff-package/` for Kubernetes deployment
- Follow `DATABASE_OPTIONS.md` for production database choice
- Use `deploy.sh` script for automated deployment

---

## 🎉 **You're Ready!**

**This guide provides everything Anushri and Shreyas need to:**
- ✅ Set up their local development environment
- ✅ Deploy the complete AI Absence & SOW System
- ✅ Test all functionality locally
- ✅ Develop and modify the application
- ✅ Prepare for production deployment

**The system will be running locally and ready for development and demonstration! 🚀**
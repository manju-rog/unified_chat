# 🚀 Oracle Cloud Deployment Guide - AI Absence & SOW System

## 📋 **Deployment Overview**

We'll deploy our system using **Oracle Cloud Infrastructure (OCI)** with the following architecture:

```
Internet → Load Balancer → Compute Instance
                              ├── Frontend (React) - Port 3000
                              ├── Backend (FastAPI) - Port 5002  
                              └── Absence Service (Spring Boot) - Port 8080
```

## 🎯 **Deployment Strategy**

### **Option 1: Single VM Deployment (Recommended for Beginners)**
- All services on one Oracle Cloud VM
- Nginx as reverse proxy
- Simple setup, cost-effective
- Good for development/small production

### **Option 2: Container Deployment (Advanced)**
- Docker containers
- Oracle Container Engine for Kubernetes (OKE)
- Scalable, production-ready

**We'll focus on Option 1 for simplicity.**

## 📦 **What We'll Create**

1. **JAR file** for Spring Boot service
2. **React build** for frontend
3. **Python package** for FastAPI backend
4. **Deployment scripts** for automation
5. **Nginx configuration** for routing
6. **Systemd services** for auto-start
7. **SSL certificates** for HTTPS

## 🛠️ **Prerequisites**

### **Oracle Cloud Account**
- Free tier account (sufficient for this project)
- Credit card for verification (won't be charged)

### **Local Tools Needed**
- SSH client (Terminal on Mac/Linux, PuTTY on Windows)
- SCP/SFTP client for file transfer
- Text editor

## 📋 **Step-by-Step Deployment Process**

### **Phase 1: Prepare Deployment Files (Local)**
1. Create JAR file for Spring Boot
2. Build React production bundle
3. Package Python backend
4. Create deployment scripts
5. Configure environment files

### **Phase 2: Oracle Cloud Setup**
1. Create OCI account
2. Set up compute instance (VM)
3. Configure networking and security
4. Set up domain name (optional)

### **Phase 3: Server Configuration**
1. Install required software (Java, Python, Node.js, Nginx)
2. Transfer application files
3. Configure services
4. Set up SSL certificates
5. Configure firewall

### **Phase 4: Application Deployment**
1. Deploy Spring Boot service
2. Deploy FastAPI backend
3. Deploy React frontend
4. Configure Nginx reverse proxy
5. Set up auto-start services

### **Phase 5: Testing & Monitoring**
1. Test all endpoints
2. Verify UI functionality
3. Set up monitoring
4. Configure backups

## 💰 **Cost Estimation**

### **Oracle Cloud Free Tier (Recommended)**
- **VM.Standard.E2.1.Micro**: FREE (1 OCPU, 1GB RAM)
- **Block Storage**: 200GB FREE
- **Bandwidth**: 10TB outbound FREE
- **Load Balancer**: $0.025/hour (optional)

**Total Monthly Cost: $0 - $20** (depending on usage)

## 🔧 **Technical Requirements**

### **Server Specifications**
- **CPU**: 1-2 cores minimum
- **RAM**: 2GB minimum (4GB recommended)
- **Storage**: 50GB minimum
- **OS**: Ubuntu 20.04 LTS (recommended)

### **Software Stack**
- **Java 11+** (for Spring Boot)
- **Python 3.8+** (for FastAPI)
- **Node.js 16+** (for React build)
- **Nginx** (reverse proxy)
- **PM2** (process manager)

## 🚦 **Deployment Phases Explained**

### **Phase 1: Build & Package (30 minutes)**
- Create production-ready builds
- Package all dependencies
- Prepare configuration files

### **Phase 2: Cloud Setup (45 minutes)**
- Create Oracle Cloud resources
- Configure networking
- Set up security rules

### **Phase 3: Server Setup (60 minutes)**
- Install software dependencies
- Configure system services
- Set up security

### **Phase 4: App Deployment (45 minutes)**
- Deploy all services
- Configure routing
- Test functionality

### **Phase 5: Go Live (30 minutes)**
- Final testing
- DNS configuration
- SSL setup

**Total Time: ~3.5 hours** (for beginners)

## 🎯 **Success Criteria**

After deployment, you'll have:
- ✅ Public URL accessible from anywhere
- ✅ HTTPS security enabled
- ✅ All features working (Absence + SOW)
- ✅ Auto-restart on server reboot
- ✅ Basic monitoring and logs
- ✅ Backup strategy in place

## 📞 **Support & Troubleshooting**

Common issues and solutions will be provided for:
- Connection problems
- Service startup failures
- Performance issues
- Security configurations

---

**Next: Let's start with Phase 1 - Building deployment packages!**
# 📚 API Documentation - AI Absence & SOW System

## 🎯 **Overview**
The AI Absence & SOW System provides REST APIs for managing employee absence requests and Statement of Work (SOW) generation through an AI-powered chat interface.

## 🏗️ **Service Architecture**

### **Backend Service (FastAPI) - Port 5002**
- **Purpose**: Main API gateway and AI chat interface
- **Technology**: Python FastAPI
- **Base URL**: `http://backend-service:5002`

### **Absence Service (Spring Boot) - Port 8080**
- **Purpose**: Employee and absence management
- **Technology**: Java Spring Boot
- **Base URL**: `http://absence-service:8080`

---

## 🔗 **Backend API Endpoints**

### **Health Check**
```http
GET /api/health
```
**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

### **Chat Interface**
```http
POST /api/chat
Content-Type: application/json
```
**Request:**
```json
{
  "message": "I need to request vacation for next week",
  "session_id": "session_123",
  "context": {
    "employee_id": 1,
    "mode": "absence"
  }
}
```
**Response:**
```json
{
  "response": "I'll help you request vacation. What dates do you need?",
  "session_id": "session_123",
  "suggestions": [
    "February 15-16, 2024",
    "Next Monday and Tuesday",
    "Custom dates"
  ],
  "context": {
    "mode": "absence",
    "step": "date_selection"
  }
}
```

### **Employee Data**
```http
GET /api/employees
GET /api/employees/{employee_id}
```

### **Session Management**
```http
POST /api/sessions
GET /api/sessions/{session_id}
DELETE /api/sessions/{session_id}
```

---

## 🔗 **Absence Service API Endpoints**

### **Health Check**
```http
GET /actuator/health
```

### **Employee Management**
```http
GET /api/employees
POST /api/employees
GET /api/employees/{id}
PUT /api/employees/{id}
DELETE /api/employees/{id}
```

### **Absence Requests**
```http
GET /api/absence-requests
POST /api/absence-requests
GET /api/absence-requests/{id}
PUT /api/absence-requests/{id}
DELETE /api/absence-requests/{id}
```

**Create Absence Request:**
```http
POST /api/absence-requests
Content-Type: application/json
```
**Request:**
```json
{
  "employee_id": 1,
  "start_date": "2024-02-15",
  "end_date": "2024-02-16",
  "absence_type": "vacation",
  "reason": "Family vacation"
}
```

### **SOW Management**
```http
GET /api/sow-requests
POST /api/sow-requests
GET /api/sow-requests/{id}
PUT /api/sow-requests/{id}
DELETE /api/sow-requests/{id}
```

---

## 🔧 **Configuration**

### **Environment Variables**

#### Backend Service
```bash
GEMINI_API_KEY=your_gemini_api_key
DB_HOST=postgres-service
DB_PORT=5432
DB_NAME=ai_absence_db
DB_USERNAME=postgres
DB_PASSWORD=your_password
```

#### Absence Service
```bash
SPRING_DATASOURCE_URL=jdbc:postgresql://postgres-service:5432/ai_absence_db
SPRING_DATASOURCE_USERNAME=postgres
SPRING_DATASOURCE_PASSWORD=your_password
SPRING_PROFILES_ACTIVE=production
```

### **Database Schema**
- **employees**: Employee information
- **absence_requests**: Absence request records
- **sow_requests**: Statement of Work requests
- **chat_sessions**: Chat session tracking

---

## 🚀 **Deployment Notes**

### **Container Ports**
- **Frontend**: 80
- **Backend**: 5002
- **Absence Service**: 8080
- **PostgreSQL**: 5432

### **Health Check Endpoints**
- **Backend**: `GET /api/health`
- **Absence Service**: `GET /actuator/health`
- **Frontend**: `GET /` (returns HTML)

### **Resource Requirements**
- **Frontend**: 100m CPU, 128Mi memory
- **Backend**: 200m CPU, 256Mi memory
- **Absence Service**: 200m CPU, 512Mi memory
- **Database**: 200m CPU, 512Mi memory

### **Dependencies**
- **Backend → Database**: PostgreSQL connection required
- **Backend → Gemini API**: Internet access for AI features
- **Absence Service → Database**: PostgreSQL connection required
- **Frontend → Backend**: API connectivity required
- **Frontend → Absence Service**: Direct API connectivity required

---

## 🔒 **Security Considerations**

### **Authentication**
- Currently uses session-based authentication
- DevOps to implement proper authentication (OAuth, JWT, etc.)

### **API Security**
- All APIs should be behind authentication
- Rate limiting recommended for chat endpoints
- Input validation implemented in application code

### **Database Security**
- Use strong passwords for database connections
- Enable SSL/TLS for database connections in production
- Regular security updates for PostgreSQL

---

## 📊 **Monitoring & Logging**

### **Application Logs**
- **Backend**: Structured JSON logging to stdout
- **Absence Service**: Spring Boot logging to stdout
- **Frontend**: Nginx access logs

### **Metrics Endpoints**
- **Backend**: `/api/metrics` (custom metrics)
- **Absence Service**: `/actuator/metrics` (Spring Boot Actuator)

### **Key Metrics to Monitor**
- API response times
- Database connection pool usage
- Chat session creation rate
- Error rates by endpoint
- Memory and CPU usage

---

## 🐛 **Troubleshooting**

### **Common Issues**
1. **Database Connection Failures**
   - Check PostgreSQL service availability
   - Verify connection credentials
   - Check network connectivity between services

2. **AI API Failures**
   - Verify Gemini API key is valid
   - Check internet connectivity
   - Monitor API rate limits

3. **Frontend Not Loading**
   - Check if backend services are healthy
   - Verify API URLs in frontend configuration
   - Check browser console for JavaScript errors

### **Debug Endpoints**
- **Backend**: `GET /api/debug/info`
- **Absence Service**: `GET /actuator/info`

---

## 📞 **Developer Support**
- **Repository**: https://github.com/manju-rog/unified_chat
- **Branch**: production-deployment
- **Contact**: Development Team
- **Documentation**: See README.md in each service directory
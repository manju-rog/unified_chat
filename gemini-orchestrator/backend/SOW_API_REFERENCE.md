# SOW Tool Endpoints - API Reference

## Base URL
```
http://localhost:8000/sow
```

## Endpoints

### 1. Start SOW Session

**Endpoint**: `POST /sow/start`

**Description**: Creates a new SOW session and returns a unique session ID.

**Request Body**:
```json
{
  "project_name": "Predictive Maintenance System"
}
```

**Response** (Success):
```json
{
  "ok": true,
  "sow_id": "a99b2111-543e-4dac-8273-323d27296360",
  "message": "Started SOW session for project 'Predictive Maintenance System'. SOW ID: a99b2111-543e-4dac-8273-323d27296360"
}
```

**Response** (Error):
```json
{
  "ok": false,
  "reason": "Error message here"
}
```

---

### 2. Update SOW Session

**Endpoint**: `POST /sow/update`

**Description**: Updates an existing SOW session with collected information. All fields except `sow_id` are optional.

**Request Body**:
```json
{
  "sow_id": "a99b2111-543e-4dac-8273-323d27296360",
  "oracle_rep": {
    "name": "John Smith",
    "email": "john.smith@oracle.com",
    "phone": "+1-555-0100",
    "address": "500 Oracle Parkway, Redwood City, CA"
  },
  "billing_contact": {
    "name": "Jane Doe",
    "email": "jane.doe@company.com",
    "phone": "+1-555-0200"
  },
  "services": [
    {
      "name": "AI Model Development",
      "description": "Develop and train predictive maintenance models"
    },
    {
      "name": "System Integration",
      "description": "Integrate AI models with existing systems"
    }
  ],
  "deliverables": [
    {
      "name": "Trained ML Models",
      "description": "Production-ready machine learning models"
    },
    {
      "name": "Integration Documentation",
      "description": "Complete technical documentation"
    }
  ],
  "acceptance": "All models must achieve 95% accuracy on test data"
}
```

**Response** (Success):
```json
{
  "ok": true,
  "message": "Updated SOW session a99b2111-543e-4dac-8273-323d27296360"
}
```

**Response** (Error - SOW not found):
```json
{
  "ok": false,
  "reason": "SOW session a99b2111-543e-4dac-8273-323d27296360 not found"
}
```

---

### 3. Generate SOW Document

**Endpoint**: `POST /sow/generate/{sow_id}`

**Description**: Generates a DOCX file from the SOW session data and returns a download URL.

**Path Parameter**:
- `sow_id`: The SOW session identifier

**Example Request**:
```
POST /sow/generate/a99b2111-543e-4dac-8273-323d27296360
```

**Response** (Success):
```json
{
  "ok": true,
  "url": "/files/a99b2111-543e-4dac-8273-323d27296360.docx",
  "message": "SOW document generated successfully"
}
```

**Response** (Error - SOW not found):
```json
{
  "ok": false,
  "reason": "SOW session a99b2111-543e-4dac-8273-323d27296360 not found"
}
```

**Response** (Error - python-docx not installed):
```json
{
  "ok": false,
  "reason": "python-docx library not installed. Run: pip install python-docx"
}
```

---

## Data Models

### ContactInfo
```typescript
{
  name: string;          // Required
  email: string;         // Required
  phone?: string;        // Optional
  address?: string;      // Optional
}
```

### ServiceItem
```typescript
{
  name: string;          // Required
  description: string;   // Required
}
```

### DeliverableItem
```typescript
{
  name: string;          // Required
  description: string;   // Required
}
```

---

## Example Workflow

### Step 1: Start SOW
```bash
curl -X POST http://localhost:8000/sow/start \
  -H "Content-Type: application/json" \
  -d '{"project_name": "My Project"}'
```

### Step 2: Update with Oracle Rep
```bash
curl -X POST http://localhost:8000/sow/update \
  -H "Content-Type: application/json" \
  -d '{
    "sow_id": "YOUR_SOW_ID",
    "oracle_rep": {
      "name": "John Smith",
      "email": "john@oracle.com"
    }
  }'
```

### Step 3: Update with Services
```bash
curl -X POST http://localhost:8000/sow/update \
  -H "Content-Type: application/json" \
  -d '{
    "sow_id": "YOUR_SOW_ID",
    "services": [
      {
        "name": "Consulting",
        "description": "Technical consulting services"
      }
    ]
  }'
```

### Step 4: Generate Document
```bash
curl -X POST http://localhost:8000/sow/generate/YOUR_SOW_ID
```

---

## Testing

Run the test suite:
```bash
cd gemini-orchestrator/backend
python test_sow_endpoints.py
```

---

## Notes

1. **Storage**: SOW sessions are stored in-memory. Restarting the server will clear all sessions.
2. **File Location**: Generated DOCX files are saved to `/tmp/{sow_id}.docx`
3. **File Serving**: The `/files/*` endpoint needs to be implemented separately (Task 8.3)
4. **Validation**: All requests are validated using Pydantic models
5. **Error Handling**: All endpoints return structured error responses with `ok: false` and `reason` field

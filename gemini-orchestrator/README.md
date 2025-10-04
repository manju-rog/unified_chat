# Gemini Orchestrator

AI-powered orchestrator for Absence Management and SOW Generation using Google Gemini.

## Project Structure

```
gemini-orchestrator/
├── backend/          # FastAPI backend
│   ├── app/         # Application code
│   ├── .env         # Environment variables
│   └── requirements.txt
└── frontend/        # Next.js frontend
    ├── src/         # Source code
    ├── .env.local   # Environment variables
    └── package.json
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a Python virtual environment:
```bash
python3 -m venv venv
```

3. Activate the virtual environment:
```bash
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Add your Gemini API key to `.env`

6. Start the backend server:
```bash
uvicorn app.main:app --reload --port 8000
```

The backend will be available at http://localhost:8000

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure environment variables:
   - Copy `.env.local.example` to `.env.local`
   - Verify the backend URL is correct

4. Start the development server:
```bash
npm run dev
```

The frontend will be available at http://localhost:3000

## Environment Variables

### Backend (.env)
- `GEMINI_API_KEY`: Your Google Gemini API key
- `BACKEND_PORT`: Port for the backend server (default: 8000)
- `FRONTEND_URL`: Frontend URL for CORS (default: http://localhost:3000)

### Frontend (.env.local)
- `NEXT_PUBLIC_BACKEND_URL`: Backend API URL (default: http://localhost:8000)

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.

## Usage Examples

### Absence Management

The system understands natural language commands for managing employee absences:

**Marking Absences:**
- "Mark Manju absent today"
- "John is sick today"
- "Sarah will be on leave tomorrow"
- "Mark employee EMP123 absent on 2024-01-15 due to vacation"

**Marking Presence:**
- "Mark John present today"
- "Sarah is back at work"
- "Employee EMP456 is present on 2024-01-16"

**Checking Status:**
- "Is Manju absent today?"
- "Check John's status for tomorrow"
- "What's Sarah's attendance on 2024-01-15?"

### SOW Generation

The system guides you through a conversational workflow to create SOW documents:

**Starting a SOW:**
1. User: "Generate a SOW for Predictive Maintenance project"
2. System: Starts SOW session and asks for Oracle representative details
3. User: Provides contact information
4. System: Asks for billing contact
5. User: Provides billing details
6. System: Asks for services
7. User: Lists services to be provided
8. System: Asks for deliverables
9. User: Lists expected deliverables
10. System: Asks for acceptance criteria
11. User: Provides acceptance criteria
12. System: Generates DOCX file and provides download link

**Example Conversation:**
```
User: "Create a statement of work for Cloud Migration"
AI: "I'll help you create a SOW for Cloud Migration. First, who is the Oracle representative?"
User: "John Smith, john.smith@oracle.com, 555-1234"
AI: "Got it. Now, who should we contact for billing?"
User: "Jane Doe, jane.doe@company.com"
AI: "Perfect. What services will be provided?"
User: "Cloud infrastructure setup, data migration, and training"
AI: "Great. What are the key deliverables?"
User: "Migrated database, configured cloud environment, and training documentation"
AI: "Excellent. What are the acceptance criteria?"
User: "All systems operational in cloud, zero data loss, and team trained"
AI: "SOW is ready! Here's your download link: [Download SOW]"
```

### Out-of-Scope Requests

The system politely refuses requests outside its domain:

- User: "What's the weather today?"
- AI: "Sorry, I can help only with Absence and SOW generation."

### Session Continuity

The system maintains context across multiple messages:

```
User: "Mark Manju absent today"
AI: "Done! Manju is marked absent for today."
User: "What about tomorrow?"
AI: "Should I mark Manju absent for tomorrow as well?"
User: "Yes"
AI: "Done! Manju is marked absent for tomorrow."
```

## Development

### Backend
- Framework: FastAPI
- Language: Python 3.10+
- AI: Google Gemini API

### Frontend
- Framework: Next.js 14
- Language: TypeScript
- Styling: Tailwind CSS

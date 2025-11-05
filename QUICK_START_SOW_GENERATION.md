# Quick Start: SOW Generation in Unified Chat

## Overview
The unified chat now properly integrates with the new_sow application to generate professional Statement of Work (SOW) documents with full support for standard services packages.

## How to Use

### Option 1: Via Unified Chat UI (Recommended)

1. **Start the Application**
   ```bash
   # All services should be running:
   # - Unified Chat Backend: http://localhost:8001
   # - Unified Chat Frontend: http://localhost:3000
   # - new_sow Backend: http://localhost:8002
   ```

2. **Access the Chat Interface**
   - Open browser to http://localhost:3000
   - The unified chat interface will load

3. **Generate SOW Document**
   - Type your message to start SOW generation
   - Follow the 7-step conversation flow:

   **Step 1: Project Info**
   ```
   Example: "Data Extraction, Compression, and Transfer Implementation for OPF to G-COP"
   ```

   **Step 2: Services** ⭐ **KEY STEP**
   - Click "📦 Standard Package" button, OR
   - Type "standard" for standard services, OR
   - Type "custom" and provide your own services
   
   **Standard Package Includes:**
   - Design Review & Feedback
   - Development of Applications (File Transfer mechanism)
   - Quality Assurance (Connectivity, SIT, Functional, Non-Functional)
   - TDM Coordination
   - Pre-Go Live, Go Live, and Post Go Live Support
   - 15 detailed scope items across 4 sprints

   **Step 3: Deliverables**
   ```
   Example: "Data Extraction Module, File Compression Module, File Transfer Interface, Archival Module"
   ```

   **Step 4: Timeline**
   ```
   Example: "Start: January 2025, End: April 2025, 16 sprints, 2 weeks per sprint"
   ```

   **Step 5: Resources**
   - Use the + and - buttons to add team members, OR
   - Type manually: "3 Developers, 2 Testers, 1 DevOps, 1 Project Manager"

   **Step 6: Contacts**
   - Select from available contacts (e.g., "MUFG Bank"), OR
   - Type custom contact information

   **Step 7: Budget**
   ```
   Example: "Total: $500,000, 4 milestones of $125,000 each"
   ```

4. **Generate Document**
   - Click "📄 Generate SOW Document" button
   - Wait for generation (typically 30-60 seconds)
   - Document will be available for download

5. **Download Document**
   - Document is saved in `generated_docs_sow/` folder
   - Also available in `new_sow/output/` folder
   - Filename format: `SOW_ProjectName_doc_TIMESTAMP_ID.docx`

### Option 2: Via API (For Automation)

```python
import requests

# Direct generation via new_sow API
response = requests.post(
    "http://localhost:8002/api/generate-direct",
    json={
        "template_path": "/path/to/sample_sow_template.docx",
        "project_data": {
            "project_info": "Your project description",
            "services": "standard",  # ← Use "standard" for standard package
            "deliverables": "Your deliverables",
            "timeline": "Your timeline",
            "resources": "Your resources",
            "contacts": "Your contacts",
            "budget": "Your budget"
        },
        "session_id": "unique_session_id"
    },
    timeout=120
)

result = response.json()
print(f"Document: {result['filename']}")
```

## Standard vs Custom Services

### Standard Services
- **When to use**: For typical development projects with standard phases
- **How to select**: Type "standard" or click "Standard Package" button
- **What you get**: Pre-defined comprehensive service package with 15 scope items
- **Benefit**: Saves time, ensures completeness, professional formatting

### Custom Services
- **When to use**: For unique projects with specific requirements
- **How to select**: Type "custom" or provide your own service description
- **What you get**: AI-enhanced services based on your input
- **Benefit**: Flexibility for specialized projects

## Troubleshooting

### Issue: Standard services not appearing in document
**Solution**: 
- Ensure you typed exactly "standard" (lowercase)
- Check that new_sow application is running (http://localhost:8002/health)
- Verify the generated document in `new_sow/output/` folder

### Issue: Document generation fails
**Solution**:
- Check all services are running
- Verify Gemini API key is set in environment variables
- Check logs in `new_sow/logs/` folder

### Issue: Document missing information
**Solution**:
- Ensure all 7 steps were completed
- Provide more detailed information in each step
- Check that contacts exist in `contacts_data.json`

## Verification

To verify standard services are working:

```bash
# Run the test script
python test_standard_services_flow.py

# Expected output:
# ✅ TEST PASSED: Standard services flow is working correctly!
```

## Document Output

### Generated Document Includes:
- ✅ Project Information (document number, name, objectives)
- ✅ Services (standard package or custom)
- ✅ Deliverables with sprint allocation
- ✅ Timeline and milestones
- ✅ Resource allocation
- ✅ Contact information (client and contractor)
- ✅ Budget and payment terms
- ✅ Assumptions and terms

### Standard Services Content:
When "standard" is selected, the document will contain:

**Service Name:**
"Design and Development / Test / Post-Go-live support for Data Extraction, Compression, and transfer Implementation"

**Service Description:**
- Design Review & Feedback
- Development of Applications (File Transfer mechanism)
- Quality Assurance (Connectivity, SIT, Functional, Non-Functional)
- TDM Coordination
- Pre-Go Live Support
- Go Live Support
- Post Go Live Support

**Scope Items (15 total):**
1. Requirements review & feedback
2. Test documentation
3. Development of Data Extraction using View/Query through Sprint #1
4. Development of File Compression & Hashing for the Data Extracted through Sprint #2
5. Development of File Transfer interface for the Compressed Data through Sprint #3
6. Development of Archival/ Data retention and Recovery option for File transfer through Sprint #4
7. Three (3) Weeks of Functional Testing (FIT) support activities
8. Two (2) Weeks of User Acceptance Testing (UAT) support activities
9. One (1) Week of System Integration Testing (SIT) support activities
10. One week (1) Weeks of Non-Functional Testing (NFT) support activities
11. Defect Triage & Test Summary Report Documentation
12. TDM Coordination with FIS Vendor, Change & Delivery teams
13. One (1) week of pre-Go-live support
14. Go-live support
15. One (1) week of post-Go-live support

## Tips for Best Results

1. **Be Specific**: Provide detailed information in each step
2. **Use Standard Services**: When applicable, use standard package for consistency
3. **Check Contacts**: Verify contact information is in the database
4. **Review Timeline**: Ensure timeline is realistic for deliverables
5. **Verify Output**: Always review generated document before sending to client

## Support

For issues or questions:
1. Check logs in `new_sow/logs/` folder
2. Verify all services are running
3. Run test script to verify integration
4. Review `SOW_INTEGRATION_FIX_SUMMARY.md` for technical details

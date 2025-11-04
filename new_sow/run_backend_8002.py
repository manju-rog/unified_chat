#!/usr/bin/env python3
"""Run new_sow backend on port 8002"""

import uvicorn

if __name__ == "__main__":
    print("🚀 Starting new_sow backend on port 8002...")
    print("📋 This runs separately from unified chat (port 8001)")
    print("🔗 API will be available at: http://localhost:8002")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )

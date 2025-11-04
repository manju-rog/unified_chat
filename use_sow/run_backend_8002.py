#!/usr/bin/env python3
"""
Run use_sow backend on port 8002 (separate from unified chat)
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("🚀 Starting use_sow backend on port 8002...")
    print("📋 This runs separately from unified chat (port 8001)")
    print("🔗 API will be available at: http://localhost:8002")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8002,
        reload=settings.DEBUG
    )
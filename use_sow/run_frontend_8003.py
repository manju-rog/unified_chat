#!/usr/bin/env python3
"""
Run use_sow frontend on port 8003 (separate from unified chat frontend)
"""

import subprocess
import sys
import os

if __name__ == "__main__":
    print("🚀 Starting use_sow frontend on port 8003...")
    print("📋 This runs separately from unified chat frontend (port 3000)")
    print("🔗 Frontend will be available at: http://localhost:8003")
    
    # Change to frontend directory
    os.chdir("frontend")
    
    # Run streamlit on port 8003
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_app.py", 
            "--server.port", "8003",
            "--server.address", "0.0.0.0"
        ])
    except KeyboardInterrupt:
        print("\\n👋 use_sow frontend stopped")
    except Exception as e:
        print(f"❌ Error running frontend: {e}")
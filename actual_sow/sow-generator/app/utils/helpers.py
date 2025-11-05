import uuid
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_session_id() -> str:
    """Generate unique session ID"""
    return f"session_{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"

def generate_template_id() -> str:
    """Generate unique template ID"""
    return f"template_{uuid.uuid4().hex[:8]}"

def generate_document_id() -> str:
    """Generate unique document ID"""
    return f"doc_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"

def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
    """Validate file extension"""
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_extensions

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace unsafe characters
    unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    return filename

def parse_json_response(response: str) -> Optional[Dict[str, Any]]:
    """Parse JSON from Gemini response, handling markdown code blocks"""
    try:
        # Remove markdown code blocks if present
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        
        # Parse JSON
        return json.loads(response.strip())
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        logger.error(f"Response was: {response}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing JSON: {e}")
        return None

def calculate_progress(stage: str) -> float:
    """Calculate completion progress based on stage"""
    stage_weights = {
        "initial": 0.0,
        "project_info": 12.5,
        "services": 25.0,
        "deliverables": 37.5,
        "timeline": 50.0,
        "resources": 62.5,
        "contacts": 75.0,
        "budget": 87.5,
        "completed": 100.0
    }
    return stage_weights.get(stage, 0.0)

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount"""
    return f"${amount:,.2f}" if currency == "USD" else f"{amount:,.2f} {currency}"

def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """Validate that end date is after start date"""
    return end_date > start_date

def create_backup(file_path: str) -> str:
    """Create backup of file"""
    if os.path.exists(file_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.backup_{timestamp}"
        import shutil
        shutil.copy2(file_path, backup_path)
        return backup_path
    return ""

def log_conversation(session_id: str, role: str, message: str):
    """Log conversation to file"""
    from app.config import settings
    log_file = os.path.join(settings.LOGS_DIR, f"{session_id}.log")
    
    with open(log_file, 'a', encoding='utf-8') as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {role.upper()}: {message}\n")

from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    """Application configuration settings"""
    
    # API Configuration
    APP_NAME: str = "SOW Generator API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Gemini API Configuration
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"  # Use latest model
    GEMINI_TEMPERATURE: float = 0.7
    GEMINI_MAX_TOKENS: int = 2048
    
    # Directory Configuration
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    TEMPLATE_DIR: str = os.path.join(BASE_DIR, "templates")
    OUTPUT_DIR: str = os.path.join(BASE_DIR, "output")
    LOGS_DIR: str = os.path.join(BASE_DIR, "logs")
    
    # File Configuration
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".docx"]
    
    # Session Configuration
    SESSION_TIMEOUT: int = 3600  # 1 hour in seconds
    MAX_SESSIONS: int = 1000
    SESSION_CLEANUP_INTERVAL: int = 300  # 5 minutes
    
    # API Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]
    ALLOW_CREDENTIALS: bool = True
    ALLOW_METHODS: List[str] = ["*"]
    ALLOW_HEADERS: List[str] = ["*"]
    
    # WebSocket Configuration
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30  # seconds
    WEBSOCKET_TIMEOUT: int = 300  # 5 minutes
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # Document Generation Configuration
    DEFAULT_DOCUMENT_FORMAT: str = "docx"
    PRESERVE_FORMATTING: bool = True
    AUTO_SAVE_DRAFTS: bool = True
    
    # Gemini API Retry Configuration
    GEMINI_MAX_RETRIES: int = 3
    GEMINI_RETRY_DELAY: int = 5  # seconds
    GEMINI_TIMEOUT: int = 30  # seconds
    
    # Database Configuration (for future Redis integration)
    REDIS_URL: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    USE_REDIS: bool = False
    
    # Security Configuration
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Feature Flags
    ENABLE_ANALYTICS: bool = False
    ENABLE_TEMPLATE_VALIDATION: bool = True
    ENABLE_AUTO_BACKUP: bool = True
    ENABLE_CONVERSATION_LOGGING: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from .env

# Create global settings instance
settings = Settings()

# Ensure directories exist
def setup_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        settings.TEMPLATE_DIR,
        settings.OUTPUT_DIR,
        settings.LOGS_DIR
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        
    # Create .gitkeep files in empty directories
    for directory in directories:
        gitkeep_path = os.path.join(directory, ".gitkeep")
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, 'w') as f:
                f.write("")

# Setup directories on import
setup_directories()

# Configuration validation
def validate_config():
    """Validate critical configuration settings"""
    errors = []
    
    # Check API key
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
        errors.append("GEMINI_API_KEY is not configured. Please set it in .env file")
    
    # Check directories are writable
    for directory in [settings.TEMPLATE_DIR, settings.OUTPUT_DIR, settings.LOGS_DIR]:
        if not os.access(directory, os.W_OK):
            errors.append(f"Directory {directory} is not writable")
    
    # Check model name
    valid_models = [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.0-pro",
        "gemini-pro"
    ]
    if settings.GEMINI_MODEL not in valid_models:
        errors.append(f"Invalid GEMINI_MODEL: {settings.GEMINI_MODEL}. Valid options: {', '.join(valid_models)}")
    
    if errors:
        print("\n⚠️  Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease fix these errors before starting the application.\n")
    
    return len(errors) == 0

# Print configuration summary
def print_config_summary():
    """Print configuration summary"""
    if settings.DEBUG:
        print("\n" + "="*60)
        print("SOW Generator - Configuration Summary")
        print("="*60)
        print(f"App Name:          {settings.APP_NAME}")
        print(f"Version:           {settings.APP_VERSION}")
        print(f"Debug Mode:        {settings.DEBUG}")
        print(f"Gemini Model:      {settings.GEMINI_MODEL}")
        print(f"Template Dir:      {settings.TEMPLATE_DIR}")
        print(f"Output Dir:        {settings.OUTPUT_DIR}")
        print(f"Logs Dir:          {settings.LOGS_DIR}")
        print(f"Session Timeout:   {settings.SESSION_TIMEOUT}s")
        print(f"Max File Size:     {settings.MAX_FILE_SIZE / 1024 / 1024}MB")
        print(f"Redis Enabled:     {settings.USE_REDIS}")
        print("="*60 + "\n")

# Export commonly used settings
__all__ = [
    'settings',
    'setup_directories',
    'validate_config',
    'print_config_summary'
]

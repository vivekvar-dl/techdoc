import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SENTRY_DSN = os.getenv('SENTRY_DSN')

# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# Application Configuration
MAX_FILE_SIZE_MB = 10
ALLOWED_FILE_TYPES = {
    'application/pdf': '.pdf',
    'text/plain': '.txt',
    'text/markdown': '.md',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx'
}

# Model Configuration
GEMINI_MODEL = 'gemini-pro'
MAX_TOKENS = 2048

# Cache Configuration
CACHE_EXPIRATION = 3600  # 1 hour 
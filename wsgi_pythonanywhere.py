"""
WSGI Configuration for DataStraw on PythonAnywhere

INSTRUCTIONS:
1. Copy this entire file content
2. Paste into your WSGI configuration file on PythonAnywhere
   (usually at /var/www/yourusername_pythonanywhere_com_wsgi.py)
3. Replace 'yourusername' with your actual PythonAnywhere username
4. Save and reload your web app

This file configures PythonAnywhere to run your FastAPI application.
"""

import sys
import os
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════
# IMPORTANT: Replace 'yourusername' with your actual PythonAnywhere username
# ═══════════════════════════════════════════════════════════════════
project_home = '/home/yourusername/ai_news_intelligence'  # ⚠️ CHANGE THIS

# Add project directory to Python path
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Add backend directory to Python path
backend_path = os.path.join(project_home, 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Change working directory to backend (important for relative file paths)
os.chdir(backend_path)

# ═══════════════════════════════════════════════════════════════════
# Load Environment Variables
# ═══════════════════════════════════════════════════════════════════

# Method 1: Load from .env file (RECOMMENDED)
from dotenv import load_dotenv
env_path = os.path.join(project_home, '.env')
load_dotenv(env_path)

# Method 2: Set environment variables directly (ALTERNATIVE)
# Uncomment and use this if .env file doesn't work:
"""
os.environ['GROQ_API_KEY'] = 'your_groq_api_key_here'
os.environ['NEWSDATA_API_KEY'] = 'your_newsdata_api_key_here'
os.environ['OPENWEATHER_API_KEY'] = 'your_openweather_api_key_here'
os.environ['DATABASE_URL'] = 'sqlite:///./news_intelligence.db'
os.environ['JWT_SECRET_KEY'] = 'your-secret-jwt-key-here'
os.environ['ENVIRONMENT'] = 'production'
"""

# ═══════════════════════════════════════════════════════════════════
# Import FastAPI Application
# ═══════════════════════════════════════════════════════════════════

# Import the FastAPI app from main.py
# Note: We import 'app' but rename it to 'application' for PythonAnywhere
from main import app as application

# PythonAnywhere will use the 'application' variable to run your app
# FastAPI apps are ASGI-compatible by default, so this works out of the box

# ═══════════════════════════════════════════════════════════════════
# Optional: Logging Configuration
# ═══════════════════════════════════════════════════════════════════

import logging

# Configure logging to help with debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info("=" * 80)
logger.info("DataStraw WSGI Configuration Loaded Successfully")
logger.info(f"Project Home: {project_home}")
logger.info(f"Backend Path: {backend_path}")
logger.info(f"Working Directory: {os.getcwd()}")
logger.info(f"Python Path: {sys.path[:3]}")
logger.info("=" * 80)

# ═══════════════════════════════════════════════════════════════════
# That's it! Your FastAPI app is now configured for PythonAnywhere
# ═══════════════════════════════════════════════════════════════════

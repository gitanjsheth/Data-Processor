"""Configuration module that loads environment variables from .env file."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration
PG_DSN = os.getenv('PG_DSN', 'postgresql://localhost:5432/contacts_db')

# Directory configuration
UPLOAD_DIR = os.getenv('UPLOAD_DIR', './upload')
EXPORT_DIR = os.getenv('EXPORT_DIR', './exports')

# Worker configuration
WORKERS = int(os.getenv('WORKERS', '6'))

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True) 
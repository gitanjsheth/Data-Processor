"""Schema management for the database."""

import os
from pathlib import Path

try:
    from .db import get_connection
except ImportError:
    from db import get_connection

def load_schema():
    """Load and execute the schema.sql file to create database tables."""
    schema_path = Path(__file__).parent / 'schema.sql'
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(schema_sql)
            conn.commit()
    
    print("Schema loaded successfully")

def drop_schema():
    """Drop all tables (useful for testing)."""
    drop_sql = """
    DROP TABLE IF EXISTS people_sources CASCADE;
    DROP TABLE IF EXISTS people CASCADE;
    DROP TABLE IF EXISTS source_files CASCADE;
    DROP TABLE IF EXISTS cities CASCADE;
    """
    
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(drop_sql)
            conn.commit()
    
    print("Schema dropped successfully")

def reset_schema():
    """Drop and recreate the schema."""
    drop_schema()
    load_schema() 
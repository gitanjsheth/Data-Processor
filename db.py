"""Database connection pool using psycopg."""

import psycopg
from psycopg_pool import ConnectionPool
from psycopg import sql

try:
    from .config import PG_DSN
except ImportError:
    from config import PG_DSN

# Global connection pool
_pool = None

def get_pool():
    """Get or create the database connection pool."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=PG_DSN,
            min_size=2,
            max_size=10,
            timeout=30
        )
    return _pool

def get_connection():
    """Get a connection from the pool."""
    return get_pool().connection()

def execute_query(query, params=None):
    """Execute a query and return results."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            if cursor.description:
                return cursor.fetchall()
            return cursor.rowcount

def execute_many(query, params_list):
    """Execute a query with multiple parameter sets."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, params_list)
            return cursor.rowcount

def close_pool():
    """Close the connection pool."""
    global _pool
    if _pool:
        _pool.close()
        _pool = None 
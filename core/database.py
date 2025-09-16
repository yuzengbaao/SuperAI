# core/database.py
import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
import logging

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", 5432)
DB_NAME = os.getenv("POSTGRES_DB", "superai_db")
DB_USER = os.getenv("POSTGRES_USER", "superai_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# --- Connection Pool ---
connection_pool = None

def get_connection_pool():
    """
    Initializes and returns a thread-safe PostgreSQL connection pool.
    """
    global connection_pool
    if connection_pool is None:
        try:
            logging.info(f"Initializing PostgreSQL connection pool for database '{DB_NAME}' at {DB_HOST}:{DB_PORT}")
            connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            logging.info("PostgreSQL connection pool initialized successfully.")
        except psycopg2.OperationalError as e:
            logging.error(f"Could not connect to PostgreSQL database: {e}")
            raise
    return connection_pool

def get_db_connection():
    """
    Gets a connection from the pool.
    Remember to close the connection using `release_db_connection`.
    """
    try:
        pool = get_connection_pool()
        conn = pool.getconn()
        return conn
    except Exception as e:
        logging.error(f"Failed to get connection from pool: {e}")
        return None

def release_db_connection(conn):
    """
    Releases a connection back to the pool.
    """
    if conn:
        try:
            pool = get_connection_pool()
            pool.putconn(conn)
        except Exception as e:
            logging.error(f"Failed to release connection back to pool: {e}")

def close_connection_pool():
    """
    Closes all connections in the pool.
    Should be called on application shutdown.
    """
    global connection_pool
    if connection_pool:
        logging.info("Closing PostgreSQL connection pool.")
        connection_pool.closeall()
        connection_pool = None

# --- Context Manager for easy connection handling ---
class DatabaseConnection:
    """
    A context manager to simplify getting and releasing database connections.
    
    Usage:
        with DatabaseConnection() as conn:
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version();")
                    db_version = cursor.fetchone()
                    print(db_version)
    """
    def __enter__(self):
        self.conn = get_db_connection()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        release_db_connection(self.conn)

# --- Example Usage ---
if __name__ == '__main__':
    logging.info("Running database module self-test...")
    
    try:
        with DatabaseConnection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version();")
                record = cursor.fetchone()
                logging.info(f"Successfully connected to database. Version: {record}")
                cursor.close()
            else:
                logging.error("Self-test failed: Could not get a database connection.")
    except Exception as e:
        logging.error(f"An error occurred during database self-test: {e}")
    finally:
        close_connection_pool()
        logging.info("Database module self-test finished.")

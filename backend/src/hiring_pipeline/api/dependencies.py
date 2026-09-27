from fastapi import Request
from src.hiring_pipeline.logger_config import setup_logger
from cassandra.cluster import Cluster, Session
from typing import Optional
import time
import threading
import os
from dotenv import load_dotenv
from cassandra.auth import PlainTextAuthProvider

# Load environment variables
load_dotenv()

log = setup_logger(__name__)

latest_data = {}
data_lock = threading.Lock()

CASS_SESSION_LOCK = threading.Lock()
CASS_SESSION_DATA = {
    'cluster': None,
    'session': None,
    'last_used': None,
    'ttl_seconds': 3600,  # 1 hour
    'cleanup_timer': None
}


def _cleanup_cassandra_session():
    """Internal function to cleanup idle Cassandra session after TTL expires."""
    with CASS_SESSION_LOCK:
        if CASS_SESSION_DATA['session'] is not None:
            log.info("[Cassandra] TTL expired. Cleaning up idle session.")
            try:
                if CASS_SESSION_DATA['cluster'] is not None:
                    CASS_SESSION_DATA['cluster'].shutdown()
            except Exception as e:
                log.error(f"[Cassandra] Error during cleanup: {e}")
            finally:
                CASS_SESSION_DATA['cluster'] = None
                CASS_SESSION_DATA['session'] = None
                CASS_SESSION_DATA['last_used'] = None
                CASS_SESSION_DATA['cleanup_timer'] = None


def _reset_cleanup_timer():
    """Reset the cleanup timer to TTL seconds from now."""
    if CASS_SESSION_DATA['cleanup_timer'] is not None:
        CASS_SESSION_DATA['cleanup_timer'].cancel()
    
    timer = threading.Timer(CASS_SESSION_DATA['ttl_seconds'], _cleanup_cassandra_session)
    timer.daemon = True
    timer.start()
    CASS_SESSION_DATA['cleanup_timer'] = timer


def get_cassandra_session() -> Session:
    """FastAPI dependency to get or create a shared Cassandra session with 1-hour TTL."""
    # FIX: Standardize how the variables are fetched
    CASSANDRA_HOST = os.getenv('CASSANDRA_HOST', 'localhost').split(',')
    CASSANDRA_PORT = int(os.getenv('CASSANDRA_PORT', '9042'))
    KEYSPACE_NAME = os.getenv('CASSANDRA_KEYSPACE', 'user_keyspace')
    auth_provider = None
    
    if os.getenv("ENVIRONMENT") == "production":
        username = os.getenv('CASSANDRA_USERNAME')
        password = os.getenv('CASSANDRA_PASSWORD')
        if username and password:
            auth_provider = PlainTextAuthProvider(username=username, password=password)
            log.debug("[Cassandra] Using authenticated connection")
        else:
            log.warning("[Cassandra] Production mode but no credentials found")

    with CASS_SESSION_LOCK:
        current_time = time.time()
        
        if CASS_SESSION_DATA['session'] is not None:
            CASS_SESSION_DATA['last_used'] = current_time
            _reset_cleanup_timer()
            return CASS_SESSION_DATA['session']
        
        log.info(f"[Cassandra] Creating new session to {CASSANDRA_HOST}:{CASSANDRA_PORT}")
        try:
            if auth_provider:
                cluster = Cluster(CASSANDRA_HOST, port=CASSANDRA_PORT, auth_provider=auth_provider)
            else:
                cluster = Cluster(CASSANDRA_HOST, port=CASSANDRA_PORT)
            
            # FIX: Connect without a keyspace first to prevent NoHostAvailable crashes
            session = cluster.connect()
            
            # FIX: Auto-create the keyspace if it does not exist
            session.execute(f"""
                CREATE KEYSPACE IF NOT EXISTS {KEYSPACE_NAME} 
                WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': '1'}}
            """)
            
            # FIX: Set the keyspace for subsequent queries
            session.set_keyspace(KEYSPACE_NAME)
            
            CASS_SESSION_DATA['cluster'] = cluster
            CASS_SESSION_DATA['session'] = session
            CASS_SESSION_DATA['last_used'] = current_time
            
            _reset_cleanup_timer()
            
            log.info("[Cassandra] Session created successfully with 1-hour TTL")
            return session
            
        except Exception as e:
            log.error(f"[Cassandra] Failed to create session: {e}")
            raise
"""
Database configuration and utilities for SkyDash
Handles PostgreSQL connections and database operations
"""

import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

class DatabaseManager:
    """
    PostgreSQL database manager for SkyDash
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_config = config.get('database', {})
        self.connection = None
        
        # Default database configuration
        self.host = self.db_config.get('host', 'localhost')
        self.port = self.db_config.get('port', 5432)
        self.database = self.db_config.get('database', 'skyhost')
        self.username = self.db_config.get('username', 'skyhost')
        self.password = self.db_config.get('password', 'Klokken!12!?!')
        
    def connect(self) -> bool:
        """
        Establish connection to PostgreSQL database
        """
        if not PSYCOPG2_AVAILABLE:
            print("PostgreSQL adapter (psycopg2) not available")
            return False
        
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
                cursor_factory=RealDictCursor
            )
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """
        Close database connection
        """
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[List[Dict]]:
        """
        Execute a SELECT query and return results
        """
        if not self.connection:
            if not self.connect():
                return None
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            print(f"Query execution failed: {e}")
            return None
    
    def execute_command(self, command: str, params: Optional[tuple] = None) -> bool:
        """
        Execute an INSERT/UPDATE/DELETE command
        """
        if not self.connection:
            if not self.connect():
                return False
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(command, params)
                self.connection.commit()
                return True
        except Exception as e:
            print(f"Command execution failed: {e}")
            self.connection.rollback()
            return False
    
    def create_tables(self) -> bool:
        """
        Create necessary tables for SkyDash
        """
        tables = [
            """
            CREATE TABLE IF NOT EXISTS skydash_logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level VARCHAR(20) NOT NULL,
                module VARCHAR(50),
                action VARCHAR(100),
                message TEXT,
                details JSONB,
                user_id VARCHAR(50),
                session_id VARCHAR(100)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS skydash_sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(100) UNIQUE NOT NULL,
                user_id VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address INET,
                user_agent TEXT,
                is_active BOOLEAN DEFAULT TRUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS skydash_config (
                id SERIAL PRIMARY KEY,
                key VARCHAR(100) UNIQUE NOT NULL,
                value JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS skydash_system_health (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cpu_usage DECIMAL(5,2),
                memory_usage DECIMAL(5,2),
                disk_usage DECIMAL(5,2),
                load_average DECIMAL(5,2),
                active_connections INTEGER,
                system_status VARCHAR(20)
            )
            """
        ]
        
        for table_sql in tables:
            if not self.execute_command(table_sql):
                print(f"Failed to create table: {table_sql[:50]}...")
                return False
        
        return True
    
    def log_to_database(self, level: str, module: str, action: str, 
                       message: str, details: Optional[Dict] = None,
                       user_id: Optional[str] = None, 
                       session_id: Optional[str] = None):
        """
        Log an event to the database
        """
        command = """
            INSERT INTO skydash_logs 
            (level, module, action, message, details, user_id, session_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        details_json = json.dumps(details) if details else None
        
        self.execute_command(command, (
            level, module, action, message, details_json, user_id, session_id
        ))
    
    def get_system_health_history(self, hours: int = 24) -> List[Dict]:
        """
        Get system health data from the last N hours
        """
        query = """
            SELECT * FROM skydash_system_health 
            WHERE timestamp >= NOW() - INTERVAL '%s hours'
            ORDER BY timestamp DESC
        """
        
        return self.execute_query(query, (hours,)) or []
    
    def save_system_health(self, cpu_usage: float, memory_usage: float,
                          disk_usage: float, load_average: float,
                          active_connections: int, system_status: str):
        """
        Save current system health metrics
        """
        command = """
            INSERT INTO skydash_system_health 
            (cpu_usage, memory_usage, disk_usage, load_average, 
             active_connections, system_status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        self.execute_command(command, (
            cpu_usage, memory_usage, disk_usage, load_average,
            active_connections, system_status
        ))
    
    def get_config_value(self, key: str) -> Any:
        """
        Get a configuration value from database
        """
        query = "SELECT value FROM skydash_config WHERE key = %s"
        result = self.execute_query(query, (key,))
        
        if result and len(result) > 0:
            return result[0]['value']
        return None
    
    def set_config_value(self, key: str, value: Any):
        """
        Set a configuration value in database
        """
        command = """
            INSERT INTO skydash_config (key, value, updated_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (key) 
            DO UPDATE SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP
        """
        
        value_json = json.dumps(value) if not isinstance(value, str) else value
        self.execute_command(command, (key, value_json))
    
    def cleanup_old_logs(self, days: int = 30):
        """
        Clean up log entries older than specified days
        """
        command = """
            DELETE FROM skydash_logs 
            WHERE timestamp < NOW() - INTERVAL '%s days'
        """
        
        return self.execute_command(command, (days,))
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics
        """
        stats = {}
        
        # Table sizes
        tables = ['skydash_logs', 'skydash_sessions', 'skydash_config', 'skydash_system_health']
        
        for table in tables:
            query = f"SELECT COUNT(*) as count FROM {table}"
            result = self.execute_query(query)
            if result:
                stats[f"{table}_count"] = result[0]['count']
        
        # Database size
        query = """
            SELECT pg_size_pretty(pg_database_size(current_database())) as size
        """
        result = self.execute_query(query)
        if result:
            stats['database_size'] = result[0]['size']
        
        return stats
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test database connection and return status
        """
        result = {
            'connected': False,
            'error': None,
            'version': None,
            'database': self.database,
            'host': self.host,
            'port': self.port
        }
        
        if not PSYCOPG2_AVAILABLE:
            result['error'] = "psycopg2 not available"
            return result
        
        try:
            if self.connect():
                result['connected'] = True
                
                # Get PostgreSQL version
                version_result = self.execute_query("SELECT version()")
                if version_result:
                    result['version'] = version_result[0]['version']
                
        except Exception as e:
            result['error'] = str(e)
        
        return result

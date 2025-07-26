"""
Logging system for SkyDash Terminal Admin
"""

import os
import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: str
    level: str
    action: str
    module: str
    user: str
    details: Dict[str, Any]
    success: bool
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None

class Logger:
    """Advanced logging system with JSON output and AI learning integration"""
    
    def __init__(self, config=None):
        self.config = config
        self.log_dir = Path("/var/log/skydash") if config is None else Path(config.get_log_dir())
        self.domains_dir = self.log_dir / "domains"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Set up logging
        self._setup_logging()
        
        # Current user (will be set by auth system)
        self.current_user = "unknown"
        
        # Performance tracking
        self._action_start_times = {}
    
    def _ensure_directories(self):
        """Create log directories with proper permissions"""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.domains_dir.mkdir(parents=True, exist_ok=True)
            
            # Set permissions
            os.chmod(self.log_dir, 0o755)
            os.chmod(self.domains_dir, 0o755)
        except PermissionError:
            # Fallback to user directory
            self.log_dir = Path.home() / ".skydash" / "logs"
            self.domains_dir = self.log_dir / "domains"
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.domains_dir.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self):
        """Configure Python logging system"""
        # Main application logger
        self.logger = logging.getLogger('skydash')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # JSON formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler with rotation
        log_file = self.log_dir / "skydash.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler for debug
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def set_user(self, username: str):
        """Set current user for logging"""
        self.current_user = username
    
    def start_action(self, action_id: str):
        """Start timing an action"""
        self._action_start_times[action_id] = datetime.now()
    
    def _get_duration(self, action_id: str) -> Optional[int]:
        """Get action duration in milliseconds"""
        if action_id in self._action_start_times:
            start_time = self._action_start_times[action_id]
            duration = (datetime.now() - start_time).total_seconds() * 1000
            del self._action_start_times[action_id]
            return int(duration)
        return None
    
    def _create_log_entry(
        self,
        level: str,
        action: str,
        module: str = "core",
        details: Dict[str, Any] = None,
        success: bool = True,
        error_message: str = None,
        action_id: str = None
    ) -> LogEntry:
        """Create a structured log entry"""
        return LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            action=action,
            module=module,
            user=self.current_user,
            details=details or {},
            success=success,
            duration_ms=self._get_duration(action_id) if action_id else None,
            error_message=error_message
        )
    
    def _write_json_log(self, entry: LogEntry, log_file: str = "activity.json"):
        """Write log entry to JSON file"""
        json_log_file = self.log_dir / log_file
        
        try:
            # Read existing logs
            logs = []
            if json_log_file.exists():
                with open(json_log_file, 'r') as f:
                    try:
                        logs = json.load(f)
                    except json.JSONDecodeError:
                        logs = []
            
            # Add new entry
            logs.append(asdict(entry))
            
            # Keep only last 1000 entries to prevent huge files
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            # Write back
            with open(json_log_file, 'w') as f:
                json.dump(logs, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Failed to write JSON log: {e}")
    
    def _write_domain_log(self, domain: str, entry: LogEntry, log_type: str = "activity"):
        """Write log entry to domain-specific file"""
        domain_dir = self.domains_dir / domain
        domain_dir.mkdir(exist_ok=True)
        
        log_file = domain_dir / f"{log_type}.json"
        
        try:
            # Read existing logs
            logs = []
            if log_file.exists():
                with open(log_file, 'r') as f:
                    try:
                        logs = json.load(f)
                    except json.JSONDecodeError:
                        logs = []
            
            # Add new entry
            logs.append(asdict(entry))
            
            # Keep only last 500 entries per domain
            if len(logs) > 500:
                logs = logs[-500:]
            
            # Write back
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Failed to write domain log for {domain}: {e}")
    
    def log_action(
        self,
        action: str,
        module: str = "core",
        details: Dict[str, Any] = None,
        domain: str = None,
        action_id: str = None
    ):
        """Log a successful action"""
        entry = self._create_log_entry(
            level="INFO",
            action=action,
            module=module,
            details=details,
            success=True,
            action_id=action_id
        )
        
        # Write to main log
        self.logger.info(f"{action} - {details or {}}")
        self._write_json_log(entry)
        
        # Write to domain log if specified
        if domain:
            self._write_domain_log(domain, entry)
    
    def log_error(
        self,
        error_message: str,
        action: str = "unknown",
        module: str = "core",
        details: Dict[str, Any] = None,
        domain: str = None,
        action_id: str = None
    ):
        """Log an error"""
        entry = self._create_log_entry(
            level="ERROR",
            action=action,
            module=module,
            details=details,
            success=False,
            error_message=error_message,
            action_id=action_id
        )
        
        # Write to main log
        self.logger.error(f"{action} failed: {error_message} - {details or {}}")
        self._write_json_log(entry, "errors.json")
        
        # Write to domain log if specified
        if domain:
            self._write_domain_log(domain, entry, "errors")
    
    def log_warning(
        self,
        warning_message: str,
        action: str = "unknown",
        module: str = "core",
        details: Dict[str, Any] = None,
        domain: str = None
    ):
        """Log a warning"""
        entry = self._create_log_entry(
            level="WARNING",
            action=action,
            module=module,
            details=details,
            success=True,
            error_message=warning_message
        )
        
        # Write to main log
        self.logger.warning(f"{action}: {warning_message} - {details or {}}")
        self._write_json_log(entry, "warnings.json")
        
        # Write to domain log if specified
        if domain:
            self._write_domain_log(domain, entry, "warnings")
    
    def log_ai_interaction(
        self,
        query: str,
        response: str,
        confidence: float,
        module: str,
        success: bool = True,
        details: Dict[str, Any] = None
    ):
        """Log AI interactions for learning"""
        ai_details = {
            "query": query,
            "response": response,
            "confidence": confidence,
            **(details or {})
        }
        
        entry = self._create_log_entry(
            level="INFO",
            action="ai_interaction",
            module=module,
            details=ai_details,
            success=success
        )
        
        self._write_json_log(entry, "ai_interactions.json")
    
    def log_system_metric(
        self,
        metric_name: str,
        value: float,
        unit: str,
        details: Dict[str, Any] = None
    ):
        """Log system metrics for monitoring"""
        metric_details = {
            "metric": metric_name,
            "value": value,
            "unit": unit,
            **(details or {})
        }
        
        entry = self._create_log_entry(
            level="INFO",
            action="system_metric",
            module="monitoring",
            details=metric_details,
            success=True
        )
        
        self._write_json_log(entry, "metrics.json")
    
    def get_recent_logs(self, log_type: str = "activity", limit: int = 50) -> list:
        """Get recent log entries"""
        log_file = self.log_dir / f"{log_type}.json"
        
        if not log_file.exists():
            return []
        
        try:
            with open(log_file, 'r') as f:
                logs = json.load(f)
                return logs[-limit:] if logs else []
        except Exception as e:
            self.logger.error(f"Failed to read logs: {e}")
            return []
    
    def get_domain_logs(self, domain: str, log_type: str = "activity", limit: int = 50) -> list:
        """Get logs for a specific domain"""
        log_file = self.domains_dir / domain / f"{log_type}.json"
        
        if not log_file.exists():
            return []
        
        try:
            with open(log_file, 'r') as f:
                logs = json.load(f)
                return logs[-limit:] if logs else []
        except Exception as e:
            self.logger.error(f"Failed to read domain logs for {domain}: {e}")
            return []
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the last N hours"""
        errors = self.get_recent_logs("errors", 1000)
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        recent_errors = [
            error for error in errors
            if datetime.fromisoformat(error['timestamp']).timestamp() > cutoff_time
        ]
        
        # Group by module and error type
        summary = {}
        for error in recent_errors:
            module = error.get('module', 'unknown')
            action = error.get('action', 'unknown')
            key = f"{module}.{action}"
            
            if key not in summary:
                summary[key] = {
                    'count': 0,
                    'last_occurrence': error['timestamp'],
                    'sample_error': error['error_message']
                }
            
            summary[key]['count'] += 1
            if error['timestamp'] > summary[key]['last_occurrence']:
                summary[key]['last_occurrence'] = error['timestamp']
        
        return summary

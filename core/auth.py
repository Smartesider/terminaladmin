"""
Authentication manager for SkyDash Terminal Admin
"""

import os
import pwd
import hashlib
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class AuthSession:
    """User authentication session"""
    username: str
    login_time: float
    last_activity: float
    session_id: str
    auth_method: str

class AuthManager:
    """Handle authentication and session management"""
    
    def __init__(self, config=None):
        self.config = config
        self.sessions = {}
        self.failed_attempts = {}
        self.current_session: Optional[AuthSession] = None
        
        # Configuration defaults
        self.max_attempts = 3 if config is None else config.get("auth.max_login_attempts", 3)
        self.session_timeout = 3600 if config is None else config.get("auth.session_timeout", 3600)
        self.ssh_key_path = None if config is None else config.get("auth.ssh_key_path")
        
        # Get current system user
        self.system_user = self._get_current_user()
    
    def _get_current_user(self) -> str:
        """Get current system username"""
        try:
            return pwd.getpwuid(os.getuid()).pw_name
        except Exception:
            return "unknown"
    
    def _generate_session_id(self, username: str) -> str:
        """Generate unique session ID"""
        timestamp = str(time.time())
        data = f"{username}_{timestamp}_{os.getpid()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _check_ssh_key_auth(self) -> bool:
        """Check if user has valid SSH key authentication"""
        # For terminal admin, we assume if user can run the script, they're authenticated
        # In a real implementation, you might check SSH agent or specific key files
        
        if self.ssh_key_path and Path(self.ssh_key_path).exists():
            # In real implementation: verify SSH key or agent
            return True
        
        # Fallback: check if user is in appropriate groups
        try:
            user_groups = [g.gr_name for g in os.getgrouplist(self.system_user, os.getgid())]
            admin_groups = ['sudo', 'wheel', 'admin', 'docker']
            return any(group in admin_groups for group in user_groups)
        except Exception:
            return False
    
    def _check_rate_limiting(self, username: str) -> bool:
        """Check if user is rate limited due to failed attempts"""
        if username not in self.failed_attempts:
            return True
        
        attempts_data = self.failed_attempts[username]
        
        # Reset attempts if enough time has passed (1 hour)
        if time.time() - attempts_data['last_attempt'] > 3600:
            del self.failed_attempts[username]
            return True
        
        # Check if user has exceeded max attempts
        return attempts_data['count'] < self.max_attempts
    
    def _record_failed_attempt(self, username: str):
        """Record a failed authentication attempt"""
        current_time = time.time()
        
        if username not in self.failed_attempts:
            self.failed_attempts[username] = {
                'count': 1,
                'first_attempt': current_time,
                'last_attempt': current_time
            }
        else:
            self.failed_attempts[username]['count'] += 1
            self.failed_attempts[username]['last_attempt'] = current_time
    
    def _create_session(self, username: str, auth_method: str) -> AuthSession:
        """Create a new authentication session"""
        current_time = time.time()
        session_id = self._generate_session_id(username)
        
        session = AuthSession(
            username=username,
            login_time=current_time,
            last_activity=current_time,
            session_id=session_id,
            auth_method=auth_method
        )
        
        self.sessions[session_id] = session
        return session
    
    def authenticate(self) -> bool:
        """Perform authentication check"""
        username = self.system_user
        
        # Check rate limiting
        if not self._check_rate_limiting(username):
            print(f"Too many failed attempts for user {username}. Please try again later.")
            return False
        
        # Check SSH key authentication
        if self._check_ssh_key_auth():
            # Create session
            self.current_session = self._create_session(username, "ssh_key")
            
            # Clear any previous failed attempts
            if username in self.failed_attempts:
                del self.failed_attempts[username]
            
            return True
        else:
            # Record failed attempt
            self._record_failed_attempt(username)
            return False
    
    def is_authenticated(self) -> bool:
        """Check if current session is authenticated and valid"""
        if not self.current_session:
            return False
        
        # Check session timeout
        current_time = time.time()
        if current_time - self.current_session.last_activity > self.session_timeout:
            self.logout()
            return False
        
        # Update last activity
        self.current_session.last_activity = current_time
        return True
    
    def get_current_user(self) -> Optional[str]:
        """Get current authenticated username"""
        if self.current_session:
            return self.current_session.username
        return None
    
    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """Get current session information"""
        if not self.current_session:
            return None
        
        return {
            "username": self.current_session.username,
            "login_time": self.current_session.login_time,
            "last_activity": self.current_session.last_activity,
            "session_id": self.current_session.session_id,
            "auth_method": self.current_session.auth_method,
            "session_duration": time.time() - self.current_session.login_time
        }
    
    def logout(self):
        """End current session"""
        if self.current_session:
            session_id = self.current_session.session_id
            if session_id in self.sessions:
                del self.sessions[session_id]
            self.current_session = None
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session.last_activity > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
    
    def get_failed_attempts_info(self, username: str = None) -> Dict[str, Any]:
        """Get information about failed login attempts"""
        target_user = username or self.system_user
        
        if target_user not in self.failed_attempts:
            return {"attempts": 0, "locked": False}
        
        attempts_data = self.failed_attempts[target_user]
        current_time = time.time()
        
        # Check if still locked
        time_since_last = current_time - attempts_data['last_attempt']
        is_locked = (attempts_data['count'] >= self.max_attempts and time_since_last < 3600)
        
        return {
            "attempts": attempts_data['count'],
            "locked": is_locked,
            "lockout_remaining": max(0, 3600 - time_since_last) if is_locked else 0,
            "last_attempt": attempts_data['last_attempt']
        }
    
    def require_auth(self, func):
        """Decorator to require authentication for functions"""
        def wrapper(*args, **kwargs):
            if not self.is_authenticated():
                raise PermissionError("Authentication required")
            return func(*args, **kwargs)
        return wrapper

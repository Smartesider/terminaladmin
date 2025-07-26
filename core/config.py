"""
Core configuration management for SkyDash Terminal Admin
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """Configuration manager for SkyDash"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".skydash"
        self.config_file = self.config_dir / "config.yaml"
        self.log_dir = Path("/var/log/skydash")
        self.domains_dir = Path("/var/log/skydash/domains")
        
        # Default configuration
        self.default_config = {
            "app": {
                "name": "SkyDash Terminal Admin",
                "version": "1.0.0",
                "port": 8022,
                "debug": False
            },
            "auth": {
                "ssh_key_path": str(Path.home() / ".ssh/authorized_keys"),
                "session_timeout": 3600,
                "max_login_attempts": 3,
                "enable_captcha": True
            },
            "logging": {
                "level": "INFO",
                "format": "json",
                "max_file_size": "10MB",
                "backup_count": 5,
                "log_dir": str(self.log_dir)
            },
            "modules": {
                "email": {
                    "enabled": True,
                    "mailu_config": "/opt/mailu/mailu.env",
                    "test_recipient": "admin@localhost"
                },
                "portainer": {
                    "enabled": True,
                    "api_url": "http://localhost:9000/api",
                    "api_token": "",
                    "timeout": 30
                },
                "vhosts": {
                    "enabled": True,
                    "nginx_config_dir": "/etc/nginx/sites-available",
                    "ssl_cert_dir": "/etc/letsencrypt/live",
                    "dns_servers": ["8.8.8.8", "1.1.1.1"]
                },
                "system": {
                    "enabled": True,
                    "update_interval": 5,
                    "history_days": 7,
                    "alert_thresholds": {
                        "cpu": 80,
                        "memory": 85,
                        "disk": 90
                    }
                },
                "fix": {
                    "enabled": True,
                    "scan_directories": ["/home", "/opt", "/etc/nginx"],
                    "backup_before_fix": True,
                    "auto_fix_safe": True
                }
            },
            "ai": {
                "enabled": True,
                "log_interactions": True,
                "learning_mode": True,
                "confidence_threshold": 0.7,
                "max_suggestions": 5
            }
        }
        
        self._config = None
        self._ensure_directories()
        self._load_config()
    
    def _ensure_directories(self):
        """Create necessary directories"""
        dirs = [self.config_dir, self.log_dir, self.domains_dir]
        
        for directory in dirs:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                # Set appropriate permissions for log directory
                if directory == self.log_dir:
                    os.chmod(directory, 0o755)
            except PermissionError:
                # Fallback to user directory if we can't write to /var/log
                if directory == self.log_dir:
                    self.log_dir = self.config_dir / "logs"
                    self.log_dir.mkdir(parents=True, exist_ok=True)
                elif directory == self.domains_dir:
                    self.domains_dir = self.log_dir / "domains"
                    self.domains_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self):
        """Load configuration from file or create default"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self._config = yaml.safe_load(f)
                    # Merge with defaults for any missing keys
                    self._config = self._merge_configs(self.default_config, self._config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
                self._config = self.default_config.copy()
        else:
            self._config = self.default_config.copy()
            self._save_config()
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Recursively merge user config with defaults"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'auth.session_timeout')"""
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self._config
        
        try:
            # Navigate to the parent of the target key
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # Set the value
            config[keys[-1]] = value
            self._save_config()
            return True
        except Exception as e:
            print(f"Error setting config value: {e}")
            return False
    
    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Get configuration for a specific module"""
        return self.get(f"modules.{module_name}", {})
    
    def is_module_enabled(self, module_name: str) -> bool:
        """Check if a module is enabled"""
        return self.get(f"modules.{module_name}.enabled", True)
    
    def get_log_dir(self) -> Path:
        """Get the log directory path"""
        return self.log_dir
    
    def get_domains_dir(self) -> Path:
        """Get the domains log directory path"""
        return self.domains_dir
    
    def get_config_dir(self) -> Path:
        """Get the configuration directory path"""
        return self.config_dir
    
    def reload(self):
        """Reload configuration from file"""
        self._load_config()
    
    def export_config(self) -> Dict[str, Any]:
        """Export current configuration as dictionary"""
        return self._config.copy()
    
    def import_config(self, config_dict: Dict[str, Any]) -> bool:
        """Import configuration from dictionary"""
        try:
            self._config = self._merge_configs(self.default_config, config_dict)
            self._save_config()
            return True
        except Exception as e:
            print(f"Error importing config: {e}")
            return False

"""
Dynamic module loader for SkyDash Terminal Admin
"""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import traceback

class ModuleLoader:
    """Dynamic module loading system for SkyDash modules"""
    
    def __init__(self, modules_dir: str = None):
        self.modules_dir = Path(modules_dir) if modules_dir else Path(__file__).parent.parent / "modules"
        self.loaded_modules = {}
        self.module_registry = {}
        
        # Ensure modules directory exists
        self.modules_dir.mkdir(exist_ok=True)
        
        # Register core modules
        self._register_core_modules()
    
    def _register_core_modules(self):
        """Register built-in module information"""
        self.module_registry = {
            "email_manager": {
                "name": "Email Management",
                "description": "Manage Mailu email accounts, test SMTP, analyze delivery",
                "file": "email_manager.py",
                "class": "EmailManager",
                "enabled": True,
                "dependencies": ["requests", "smtplib", "dns"]
            },
            "portainer_manager": {
                "name": "Portainer & Containers",
                "description": "Monitor Docker containers via Portainer API",
                "file": "portainer_manager.py", 
                "class": "PortainerManager",
                "enabled": True,
                "dependencies": ["requests", "docker"]
            },
            "vhosts_manager": {
                "name": "VHosts & SSL",
                "description": "Validate domains, SSL certificates, DNS configuration",
                "file": "vhosts_manager.py",
                "class": "VHostsManager", 
                "enabled": True,
                "dependencies": ["requests", "ssl", "dns", "cryptography"]
            },
            "system_health": {
                "name": "System Health",
                "description": "Monitor CPU/RAM/disk, service status, fail2ban logs",
                "file": "system_health.py",
                "class": "SystemHealth",
                "enabled": True,
                "dependencies": ["psutil", "subprocess"]
            },
            "system_fixer": {
                "name": "System Fixer",
                "description": "Scan and fix configuration issues, auto-repair",
                "file": "system_fixer.py",
                "class": "SystemFixer",
                "enabled": True,
                "dependencies": ["subprocess", "shutil"]
            }
        }
    
    def get_available_modules(self) -> Dict[str, Dict[str, Any]]:
        """Get list of all available modules"""
        return self.module_registry.copy()
    
    def get_module_info(self, module_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific module"""
        return self.module_registry.get(module_name)
    
    def is_module_available(self, module_name: str) -> bool:
        """Check if a module is available"""
        if module_name not in self.module_registry:
            return False
        
        module_info = self.module_registry[module_name]
        module_file = self.modules_dir / module_info["file"]
        
        return module_file.exists()
    
    def check_module_dependencies(self, module_name: str) -> Dict[str, bool]:
        """Check if module dependencies are satisfied"""
        if module_name not in self.module_registry:
            return {}
        
        module_info = self.module_registry[module_name]
        dependencies = module_info.get("dependencies", [])
        
        dependency_status = {}
        for dep in dependencies:
            try:
                importlib.import_module(dep)
                dependency_status[dep] = True
            except ImportError:
                dependency_status[dep] = False
        
        return dependency_status
    
    def load_module(self, module_name: str) -> Optional[Any]:
        """Load and return a module instance"""
        # Check if already loaded
        if module_name in self.loaded_modules:
            return self.loaded_modules[module_name]
        
        # Check if module is registered
        if module_name not in self.module_registry:
            print(f"Module '{module_name}' not found in registry")
            return None
        
        module_info = self.module_registry[module_name]
        
        # Check if module is enabled
        if not module_info.get("enabled", True):
            print(f"Module '{module_name}' is disabled")
            return None
        
        # Check if module file exists
        module_file = self.modules_dir / module_info["file"]
        if not module_file.exists():
            print(f"Module file not found: {module_file}")
            return None
        
        try:
            # Load module dynamically
            spec = importlib.util.spec_from_file_location(module_name, module_file)
            if spec is None or spec.loader is None:
                print(f"Could not load module spec for {module_name}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Get the module class
            class_name = module_info.get("class", module_name.title())
            if hasattr(module, class_name):
                module_class = getattr(module, class_name)
                module_instance = module_class()
                
                # Cache the loaded module
                self.loaded_modules[module_name] = module_instance
                
                return module_instance
            else:
                print(f"Class '{class_name}' not found in module {module_name}")
                return None
                
        except Exception as e:
            print(f"Error loading module {module_name}: {e}")
            traceback.print_exc()
            return None
    
    def reload_module(self, module_name: str) -> Optional[Any]:
        """Reload a module (useful for development)"""
        # Remove from cache
        if module_name in self.loaded_modules:
            del self.loaded_modules[module_name]
        
        # Remove from sys.modules if present
        if module_name in sys.modules:
            del sys.modules[module_name]
        
        # Load fresh
        return self.load_module(module_name)
    
    def unload_module(self, module_name: str):
        """Unload a module from memory"""
        if module_name in self.loaded_modules:
            del self.loaded_modules[module_name]
        
        if module_name in sys.modules:
            del sys.modules[module_name]
    
    def get_loaded_modules(self) -> List[str]:
        """Get list of currently loaded modules"""
        return list(self.loaded_modules.keys())
    
    def register_module(
        self,
        module_name: str,
        module_info: Dict[str, Any]
    ) -> bool:
        """Register a new module"""
        required_fields = ["name", "description", "file", "class"]
        
        # Validate module info
        for field in required_fields:
            if field not in module_info:
                print(f"Missing required field '{field}' in module info")
                return False
        
        # Add module to registry
        self.module_registry[module_name] = {
            "enabled": True,
            "dependencies": [],
            **module_info
        }
        
        return True
    
    def unregister_module(self, module_name: str) -> bool:
        """Unregister a module"""
        if module_name in self.module_registry:
            # Unload if loaded
            self.unload_module(module_name)
            
            # Remove from registry
            del self.module_registry[module_name]
            return True
        
        return False
    
    def enable_module(self, module_name: str) -> bool:
        """Enable a module"""
        if module_name in self.module_registry:
            self.module_registry[module_name]["enabled"] = True
            return True
        return False
    
    def disable_module(self, module_name: str) -> bool:
        """Disable a module"""
        if module_name in self.module_registry:
            # Unload if currently loaded
            self.unload_module(module_name)
            
            # Mark as disabled
            self.module_registry[module_name]["enabled"] = False
            return True
        return False
    
    def get_module_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all modules"""
        status = {}
        
        for module_name, module_info in self.module_registry.items():
            is_loaded = module_name in self.loaded_modules
            is_available = self.is_module_available(module_name)
            dependencies = self.check_module_dependencies(module_name)
            all_deps_ok = all(dependencies.values()) if dependencies else True
            
            status[module_name] = {
                "name": module_info["name"],
                "enabled": module_info.get("enabled", True),
                "available": is_available,
                "loaded": is_loaded,
                "dependencies_ok": all_deps_ok,
                "dependencies": dependencies
            }
        
        return status
    
    def create_module_template(self, module_name: str, class_name: str = None) -> str:
        """Create a template for a new module"""
        if class_name is None:
            class_name = ''.join(word.capitalize() for word in module_name.split('_'))
        
        template = f'''"""
{module_name.replace('_', ' ').title()} Module for SkyDash Terminal Admin
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box
from typing import Dict, Any

class {class_name}:
    """
    {module_name.replace('_', ' ').title()} management module
    """
    
    def __init__(self):
        self.name = "{module_name.replace('_', ' ').title()}"
        self.version = "1.0.0"
        self.description = "Module description here"
    
    def run(self, console: Console, logger, config):
        """Main module entry point"""
        self.console = console
        self.logger = logger
        self.config = config
        
        self.logger.log_action(f"Started {{self.name}} module", module="{module_name}")
        
        try:
            self._show_main_menu()
        except KeyboardInterrupt:
            self.console.print("\\n[yellow]Module interrupted by user[/yellow]")
        except Exception as e:
            self.logger.log_error(str(e), module="{module_name}")
            self.console.print(f"[red]Module error: {{e}}[/red]")
        finally:
            self.logger.log_action(f"Exited {{self.name}} module", module="{module_name}")
    
    def _show_main_menu(self):
        """Display main module menu"""
        while True:
            self.console.clear()
            
            # Module header
            header = Panel(
                f"[bold cyan]{{self.name}}[/bold cyan]\\n{{self.description}}",
                title="Module Menu",
                border_style="cyan"
            )
            self.console.print(header)
            self.console.print()
            
            # Menu options
            menu = Panel(
                """[bold cyan](1)[/bold cyan] Option 1
[bold cyan](2)[/bold cyan] Option 2
[bold cyan](3)[/bold cyan] Option 3

[bold yellow](H)[/bold yellow] Help
[bold red](A)[/bold red] Back to Main Menu""",
                title="Available Options",
                border_style="blue"
            )
            self.console.print(menu)
            self.console.print()
            
            choice = Prompt.ask(
                "[bold green]Select option[/bold green]",
                choices=["1", "2", "3", "H", "A"],
                default="A"
            ).upper()
            
            if choice == "1":
                self._option_1()
            elif choice == "2":
                self._option_2()
            elif choice == "3":
                self._option_3()
            elif choice == "H":
                self._show_help()
            elif choice == "A":
                break
    
    def _option_1(self):
        """Handle option 1"""
        self.console.print("[cyan]Option 1 functionality not yet implemented[/cyan]")
        self.console.input("\\nPress Enter to continue...")
    
    def _option_2(self):
        """Handle option 2"""
        self.console.print("[cyan]Option 2 functionality not yet implemented[/cyan]")
        self.console.input("\\nPress Enter to continue...")
    
    def _option_3(self):
        """Handle option 3"""
        self.console.print("[cyan]Option 3 functionality not yet implemented[/cyan]")
        self.console.input("\\nPress Enter to continue...")
    
    def _show_help(self):
        """Show module help"""
        help_text = f"""[bold cyan]{{self.name}} Help[/bold cyan]

This module provides functionality for {{self.description.lower()}}.

[bold]Available Options:[/bold]
• Option 1: Description here
• Option 2: Description here  
• Option 3: Description here

[bold]Usage Tips:[/bold]
• Add usage tips here
• Add more information here

[bold]Configuration:[/bold]
• Configuration details here
"""
        
        panel = Panel(help_text, title="Help", border_style="yellow")
        self.console.print(panel)
        self.console.input("\\nPress Enter to continue...")
'''
        
        return template

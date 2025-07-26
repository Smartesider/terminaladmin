#!/usr/bin/env python3
"""
SkyDash Terminal Admin System
AI-driven DevOps control center for servers and containers
"""

import os
import sys
import json
import importlib
from datetime import datetime
from typing import Dict, Any, Optional

# Rich library for beautiful terminal UI
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich.live import Live
from rich import box

# Local imports
from core.config import Config
from core.logger import Logger
from core.auth import AuthManager
from core.module_loader import ModuleLoader

class SkyDashTerminal:
    """Main terminal interface for SkyDash admin system"""
    
    def __init__(self):
        self.console = Console()
        self.config = Config()
        self.logger = Logger()
        self.auth = AuthManager()
        self.module_loader = ModuleLoader()
        self.running = True
        
        # Module status tracking
        self.module_status = {
            'E': {'name': 'Email Management', 'status': 'ready', 'color': 'green'},
            'P': {'name': 'Portainer/Containers', 'status': 'ready', 'color': 'green'},
            'V': {'name': 'VHosts/SSL', 'status': 'ready', 'color': 'green'},
            'S': {'name': 'System Health', 'status': 'ready', 'color': 'green'},
            'F': {'name': 'Fix/Analyze', 'status': 'ready', 'color': 'green'}
        }
    
    def display_header(self):
        """Display the SkyDash header with system info"""
        header_text = Text()
        header_text.append("SkyDash ", style="bold cyan")
        header_text.append("Terminal Admin System", style="bold white")
        header_text.append(" v1.0", style="dim white")
        
        # System info
        hostname = os.uname().nodename
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        info_text = f"Host: {hostname} | Time: {timestamp} | Port: 8022"
        
        panel = Panel(
            f"{header_text}\n\n{info_text}",
            title="🚀 SkyDash Admin",
            border_style="cyan",
            box=box.DOUBLE
        )
        
        self.console.print(panel)
        self.console.print()
    
    def display_module_status(self):
        """Display current status of all modules"""
        table = Table(title="Module Status", box=box.ROUNDED)
        table.add_column("Key", style="bold")
        table.add_column("Module", style="bold")
        table.add_column("Status", style="bold")
        table.add_column("Description")
        
        for key, info in self.module_status.items():
            status_color = info['color']
            table.add_row(
                f"[bold cyan]({key})[/bold cyan]",
                info['name'],
                f"[{status_color}]●[/{status_color}] {info['status']}",
                self._get_module_description(key)
            )
        
        self.console.print(table)
        self.console.print()
    
    def _get_module_description(self, key: str) -> str:
        """Get description for each module"""
        descriptions = {
            'E': "Manage email accounts, test SMTP/DKIM, AI error analysis",
            'P': "Docker containers via Portainer API, resource monitoring",
            'V': "VHost validation, SSL checks, DNS verification",
            'S': "CPU/RAM/Disk monitoring, service health, fail2ban status",
            'F': "Scan and fix system configurations, auto-repair suggestions"
        }
        return descriptions.get(key, "")
    
    def display_main_menu(self):
        """Display the main navigation menu"""
        menu_panel = Panel(
            """[bold cyan](E)[/bold cyan] Email Management & Testing
[bold cyan](P)[/bold cyan] Portainer & Container Management  
[bold cyan](V)[/bold cyan] VHosts & SSL Validation
[bold cyan](S)[/bold cyan] System Health & Monitoring
[bold cyan](F)[/bold cyan] Fix & Analyze Systems

[bold yellow](H)[/bold yellow] Help & Documentation
[bold red](A)[/bold red] Exit SkyDash""",
            title="Main Menu",
            border_style="blue",
            box=box.ROUNDED
        )
        
        self.console.print(menu_panel)
        self.console.print()
    
    def get_user_choice(self) -> str:
        """Get user menu choice with validation"""
        valid_choices = ['E', 'P', 'V', 'S', 'F', 'H', 'A']
        
        while True:
            choice = Prompt.ask(
                "[bold green]Select option[/bold green]",
                choices=valid_choices,
                default="S",
                show_choices=False
            ).upper()
            
            if choice in valid_choices:
                return choice
            
            self.console.print("[red]Invalid choice. Please try again.[/red]")
    
    def handle_menu_choice(self, choice: str):
        """Handle user menu selection"""
        self.logger.log_action(f"User selected menu option: {choice}")
        
        if choice == 'E':
            self.launch_email_module()
        elif choice == 'P':
            self.launch_portainer_module()
        elif choice == 'V':
            self.launch_vhosts_module()
        elif choice == 'S':
            self.launch_system_module()
        elif choice == 'F':
            self.launch_fix_module()
        elif choice == 'H':
            self.show_help()
        elif choice == 'A':
            self.exit_application()
    
    def launch_email_module(self):
        """Launch email management module"""
        try:
            module = self.module_loader.load_module('email_manager')
            if module:
                module.run(self.console, self.logger, self.config)
            else:
                self.console.print("[yellow]Email module not yet implemented.[/yellow]")
                self.console.input("\nPress Enter to continue...")
        except Exception as e:
            self.logger.log_error(f"Error launching email module: {e}")
            self.console.print(f"[red]Error: {e}[/red]")
            self.console.input("\nPress Enter to continue...")
    
    def launch_portainer_module(self):
        """Launch Portainer/container module"""
        try:
            module = self.module_loader.load_module('portainer_manager')
            if module:
                module.run(self.console, self.logger, self.config)
            else:
                self.console.print("[yellow]Portainer module not yet implemented.[/yellow]")
                self.console.input("\nPress Enter to continue...")
        except Exception as e:
            self.logger.log_error(f"Error launching Portainer module: {e}")
            self.console.print(f"[red]Error: {e}[/red]")
            self.console.input("\nPress Enter to continue...")
    
    def launch_vhosts_module(self):
        """Launch VHosts/SSL module"""
        try:
            module = self.module_loader.load_module('vhosts_manager')
            if module:
                module.run(self.console, self.logger, self.config)
            else:
                self.console.print("[yellow]VHosts module not yet implemented.[/yellow]")
                self.console.input("\nPress Enter to continue...")
        except Exception as e:
            self.logger.log_error(f"Error launching VHosts module: {e}")
            self.console.print(f"[red]Error: {e}[/red]")
            self.console.input("\nPress Enter to continue...")
    
    def launch_system_module(self):
        """Launch system health module"""
        try:
            module = self.module_loader.load_module('system_health')
            if module:
                module.run(self.console, self.logger, self.config)
            else:
                self.console.print("[yellow]System Health module not yet implemented.[/yellow]")
                self.console.input("\nPress Enter to continue...")
        except Exception as e:
            self.logger.log_error(f"Error launching System Health module: {e}")
            self.console.print(f"[red]Error: {e}[/red]")
            self.console.input("\nPress Enter to continue...")
    
    def launch_fix_module(self):
        """Launch fix/analyze module"""
        try:
            module = self.module_loader.load_module('system_fixer')
            if module:
                module.run(self.console, self.logger, self.config)
            else:
                self.console.print("[yellow]Fix/Analyze module not yet implemented.[/yellow]")
                self.console.input("\nPress Enter to continue...")
        except Exception as e:
            self.logger.log_error(f"Error launching Fix module: {e}")
            self.console.print(f"[red]Error: {e}[/red]")
            self.console.input("\nPress Enter to continue...")
    
    def show_help(self):
        """Display help and documentation"""
        help_text = """[bold cyan]SkyDash Terminal Admin Help[/bold cyan]

[bold]Navigation:[/bold]
• Use letter keys to select menu options
• Each module has (H)elp and (A)back/exit options
• All actions are logged with timestamps

[bold]Modules:[/bold]
• [cyan]Email (E):[/cyan] Manage Mailu accounts, test SMTP, analyze delivery issues
• [cyan]Portainer (P):[/cyan] Monitor Docker containers, resource usage, start/stop services  
• [cyan]VHosts (V):[/cyan] Validate domains, SSL certificates, DNS configuration
• [cyan]System (S):[/cyan] CPU/RAM/disk monitoring, service status, fail2ban logs
• [cyan]Fix (F):[/cyan] Scan for configuration issues, auto-repair suggestions

[bold]AI Features:[/bold]
• Error analysis and plain-English explanations
• Predictive failure detection and resource warnings
• Auto-fix suggestions with rollback capabilities
• Learning from user feedback and system responses

[bold]Security:[/bold]
• SSH key authentication required
• All actions logged with audit trail
• Fail2ban integration for brute force protection

[bold]Logs:[/bold]
• JSON format logs in /var/log/skydash/
• Per-domain specific logging
• AI learning and feedback tracking
"""
        
        panel = Panel(
            help_text,
            title="Help & Documentation",
            border_style="cyan",
            box=box.ROUNDED
        )
        
        self.console.print(panel)
        self.console.input("\nPress Enter to continue...")
    
    def exit_application(self):
        """Exit the application with confirmation"""
        if Confirm.ask("[yellow]Are you sure you want to exit SkyDash?[/yellow]"):
            self.logger.log_action("User exited SkyDash Terminal")
            self.console.print("\n[cyan]Thank you for using SkyDash Terminal Admin![/cyan]")
            self.console.print("[dim]Stay in control. 🚀[/dim]\n")
            self.running = False
    
    def run(self):
        """Main application loop"""
        try:
            # Clear screen and show header
            self.console.clear()
            
            # Check authentication
            if not self.auth.authenticate():
                self.console.print("[red]Authentication failed. Access denied.[/red]")
                return
            
            self.logger.log_action("SkyDash Terminal started")
            
            # Main loop
            while self.running:
                self.console.clear()
                self.display_header()
                self.display_module_status()
                self.display_main_menu()
                
                choice = self.get_user_choice()
                self.handle_menu_choice(choice)
                
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Interrupted by user. Exiting...[/yellow]")
            self.logger.log_action("SkyDash interrupted by Ctrl+C")
        except Exception as e:
            self.logger.log_error(f"Fatal error in main loop: {e}")
            self.console.print(f"[red]Fatal error: {e}[/red]")
        finally:
            self.logger.log_action("SkyDash Terminal session ended")

def main():
    """Entry point for SkyDash Terminal"""
    app = SkyDashTerminal()
    app.run()

if __name__ == "__main__":
    main()

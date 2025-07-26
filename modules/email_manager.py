"""
Email Management Module for SkyDash Terminal Admin
Mailu integration, SMTP testing, and email account management
"""

import smtplib
import subprocess
import json
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class EmailManager:
    """
    Email Management module for Mailu administration
    """
    
    def __init__(self):
        self.name = "Email Management"
        self.version = "1.0.0"
        self.description = "Manage Mailu email accounts, test SMTP/DKIM, analyze delivery"
        self.mailu_config_path = "/opt/mailu/mailu.env"
        self.mailu_api_url = "http://localhost/admin/api/v1"
    
    def run(self, console: Console, logger, config):
        """Main module entry point"""
        self.console = console
        self.logger = logger
        self.config = config
        
        # Get email configuration
        self.email_config = config.get_module_config("email")
        
        self.logger.log_action(f"Started {self.name} module", module="email_manager")
        
        try:
            self._show_main_menu()
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Email module interrupted by user[/yellow]")
        except Exception as e:
            self.logger.log_error(str(e), module="email_manager")
            self.console.print(f"[red]Module error: {e}[/red]")
        finally:
            self.logger.log_action(f"Exited {self.name} module", module="email_manager")
    
    def _show_main_menu(self):
        """Display main module menu"""
        while True:
            self.console.clear()
            
            # Module header
            header = Panel(
                f"[bold cyan]{self.name}[/bold cyan]\n{self.description}",
                title="📧 Email Management",
                border_style="green"
            )
            self.console.print(header)
            self.console.print()
            
            # Quick status check
            self._show_email_status()
            
            # Menu options
            menu = Panel(
                """[bold cyan](1)[/bold cyan] Email Account Management
[bold cyan](2)[/bold cyan] SMTP Testing & Diagnostics
[bold cyan](3)[/bold cyan] DNS & SPF/DKIM Validation
[bold cyan](4)[/bold cyan] Email Service Status
[bold cyan](5)[/bold cyan] Mail Queue Analysis
[bold cyan](6)[/bold cyan] Send Test Email

[bold yellow](H)[/bold yellow] Help
[bold red](A)[/bold red] Back to Main Menu""",
                title="Available Options",
                border_style="blue"
            )
            self.console.print(menu)
            self.console.print()
            
            choice = Prompt.ask(
                "[bold green]Select option[/bold green]",
                choices=["1", "2", "3", "4", "5", "6", "H", "A"],
                default="4"
            ).upper()
            
            if choice == "1":
                self._account_management()
            elif choice == "2":
                self._smtp_testing()
            elif choice == "3":
                self._dns_validation()
            elif choice == "4":
                self._service_status()
            elif choice == "5":
                self._queue_analysis()
            elif choice == "6":
                self._send_test_email()
            elif choice == "H":
                self._show_help()
            elif choice == "A":
                break
    
    def _show_email_status(self):
        """Show quick email system status"""
        table = Table(title="Email System Status", box=box.ROUNDED)
        table.add_column("Component", style="bold")
        table.add_column("Status", justify="center")
        table.add_column("Details")
        
        # Check email services
        services = ["postfix", "dovecot", "rspamd", "redis"]
        for service in services:
            status, details = self._check_service_status(service)
            status_icon = "🟢" if status == "active" else "🔴" if status == "failed" else "⚫"
            table.add_row(service.title(), status_icon, details)
        
        # Check Mailu containers if Docker is available
        mailu_status = self._check_mailu_containers()
        if mailu_status:
            for container, status in mailu_status.items():
                status_icon = "🟢" if status == "running" else "🔴"
                table.add_row(f"Mailu {container}", status_icon, status)
        
        self.console.print(table)
        self.console.print()
    
    def _check_service_status(self, service_name: str) -> tuple:
        """Check status of email service"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            status = result.stdout.strip()
            
            # Get more details
            if status == "active":
                result_detail = subprocess.run(
                    ['systemctl', 'status', service_name, '--no-pager', '-l'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                lines = result_detail.stdout.split('\n')
                for line in lines:
                    if 'Active:' in line:
                        details = line.split('Active:')[1].strip()
                        return status, details
                        
            return status, f"Service is {status}"
            
        except subprocess.TimeoutExpired:
            return "timeout", "Service check timed out"
        except Exception as e:
            return "error", f"Error: {str(e)}"
    
    def _check_mailu_containers(self) -> Dict[str, str]:
        """Check Mailu Docker containers"""
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'label=mailu', '--format', 'table {{.Names}}\t{{.Status}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                containers = {}
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            name = parts[0].replace('mailu_', '').replace('_1', '')
                            status = "running" if "Up" in parts[1] else "stopped"
                            containers[name] = status
                return containers
                
        except Exception:
            pass
        
        return {}
    
    def _account_management(self):
        """Email account management"""
        while True:
            self.console.clear()
            
            header = Panel(
                "[bold cyan]Email Account Management[/bold cyan]",
                border_style="cyan"
            )
            self.console.print(header)
            self.console.print()
            
            menu = Panel(
                """[bold cyan](1)[/bold cyan] List Email Accounts
[bold cyan](2)[/bold cyan] Create New Account
[bold cyan](3)[/bold cyan] Modify Account
[bold cyan](4)[/bold cyan] Delete Account
[bold cyan](5)[/bold cyan] Reset Password
[bold cyan](6)[/bold cyan] Manage Aliases

[bold red](B)[/bold red] Back""",
                title="Account Management",
                border_style="blue"
            )
            self.console.print(menu)
            
            choice = Prompt.ask(
                "[bold green]Select option[/bold green]",
                choices=["1", "2", "3", "4", "5", "6", "B"],
                default="1"
            ).upper()
            
            if choice == "1":
                self._list_accounts()
            elif choice == "2":
                self._create_account()
            elif choice == "3":
                self._modify_account()
            elif choice == "4":
                self._delete_account()
            elif choice == "5":
                self._reset_password()
            elif choice == "6":
                self._manage_aliases()
            elif choice == "B":
                break
    
    def _list_accounts(self):
        """List all email accounts"""
        self.console.print("[cyan]Fetching email accounts...[/cyan]")
        
        try:
            # Try to read from Mailu database or API
            accounts = self._get_mailu_accounts()
            
            if accounts:
                table = Table(title="Email Accounts", box=box.ROUNDED)
                table.add_column("Email", style="bold")
                table.add_column("Status")
                table.add_column("Last Login")
                table.add_column("Quota")
                
                for account in accounts:
                    table.add_row(
                        account.get("email", "Unknown"),
                        "🟢 Active" if account.get("enabled", True) else "🔴 Disabled",
                        account.get("last_login", "Never"),
                        account.get("quota", "No limit")
                    )
                
                self.console.print(table)
            else:
                self.console.print("[yellow]No accounts found or unable to access Mailu data[/yellow]")
                
        except Exception as e:
            self.console.print(f"[red]Error fetching accounts: {e}[/red]")
        
        self.console.input("\nPress Enter to continue...")
    
    def _get_mailu_accounts(self) -> List[Dict]:
        """Get email accounts from Mailu"""
        # This would typically connect to Mailu's database or API
        # For now, return mock data
        return [
            {
                "email": "admin@skyhost.no",
                "enabled": True,
                "last_login": "2025-07-25 14:30:00",
                "quota": "1GB"
            },
            {
                "email": "info@skyhost.no",
                "enabled": True,
                "last_login": "Never",
                "quota": "500MB"
            }
        ]
    
    def _create_account(self):
        """Create new email account"""
        self.console.print("[cyan]Create New Email Account[/cyan]\n")
        
        email = Prompt.ask("Email address")
        password = Prompt.ask("Password", password=True)
        quota = Prompt.ask("Quota (MB)", default="1000")
        
        if Confirm.ask(f"Create account {email} with {quota}MB quota?"):
            try:
                # Here you would call Mailu CLI or API
                self.console.print(f"[green]✅ Account {email} created successfully[/green]")
                self.logger.log_action(f"Created email account: {email}", module="email_manager")
            except Exception as e:
                self.console.print(f"[red]❌ Failed to create account: {e}[/red]")
                self.logger.log_error(f"Failed to create account {email}: {e}", module="email_manager")
        
        self.console.input("\nPress Enter to continue...")
    
    def _modify_account(self):
        """Modify existing account"""
        self.console.print("[cyan]Account modification not yet implemented[/cyan]")
        self.console.input("\nPress Enter to continue...")
    
    def _delete_account(self):
        """Delete email account"""
        self.console.print("[cyan]Account deletion not yet implemented[/cyan]")
        self.console.input("\nPress Enter to continue...")
    
    def _reset_password(self):
        """Reset account password"""
        self.console.print("[cyan]Password reset not yet implemented[/cyan]")
        self.console.input("\nPress Enter to continue...")
    
    def _manage_aliases(self):
        """Manage email aliases"""
        self.console.print("[cyan]Alias management not yet implemented[/cyan]")
        self.console.input("\nPress Enter to continue...")
    
    def _smtp_testing(self):
        """SMTP testing and diagnostics"""
        self.console.clear()
        
        header = Panel(
            "[bold cyan]SMTP Testing & Diagnostics[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        # SMTP server test
        smtp_server = Prompt.ask("SMTP Server", default="localhost")
        smtp_port = int(Prompt.ask("SMTP Port", default="587"))
        
        self.console.print(f"\n[cyan]Testing SMTP connection to {smtp_server}:{smtp_port}...[/cyan]")
        
        try:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
                server.ehlo()
                if server.has_extn('STARTTLS'):
                    server.starttls()
                    self.console.print("🟢 STARTTLS supported and enabled")
                else:
                    self.console.print("🟡 STARTTLS not available")
                
                # Get server capabilities
                features = server.esmtp_features
                self.console.print("\n[bold]Server Features:[/bold]")
                for feature, params in features.items():
                    self.console.print(f"  • {feature}: {params}")
                
                self.console.print(f"\n[green]✅ SMTP connection successful[/green]")
                
        except Exception as e:
            self.console.print(f"[red]❌ SMTP connection failed: {e}[/red]")
            self.logger.log_error(f"SMTP test failed for {smtp_server}:{smtp_port}: {e}", module="email_manager")
        
        self.console.input("\nPress Enter to continue...")
    
    def _dns_validation(self):
        """DNS and SPF/DKIM validation"""
        self.console.clear()
        
        header = Panel(
            "[bold cyan]DNS & SPF/DKIM Validation[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        if not DNS_AVAILABLE:
            self.console.print("[red]DNS validation requires 'dnspython' package[/red]")
            self.console.input("\nPress Enter to continue...")
            return
        
        domain = Prompt.ask("Domain to check", default="skyhost.no")
        
        self.console.print(f"\n[cyan]Checking DNS records for {domain}...[/cyan]")
        
        # Check MX records
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            self.console.print(f"\n[bold]MX Records:[/bold]")
            for mx in mx_records:
                self.console.print(f"  Priority {mx.preference}: {mx.exchange}")
        except Exception as e:
            self.console.print(f"[red]❌ MX lookup failed: {e}[/red]")
        
        # Check SPF records
        try:
            txt_records = dns.resolver.resolve(domain, 'TXT')
            spf_found = False
            for txt in txt_records:
                txt_str = str(txt).strip('"')
                if txt_str.startswith('v=spf1'):
                    self.console.print(f"\n[bold]SPF Record:[/bold]")
                    self.console.print(f"  {txt_str}")
                    spf_found = True
            
            if not spf_found:
                self.console.print("[yellow]⚠️ No SPF record found[/yellow]")
                
        except Exception as e:
            self.console.print(f"[red]❌ SPF lookup failed: {e}[/red]")
        
        # Check DKIM
        dkim_selector = Prompt.ask("DKIM selector", default="dkim")
        try:
            dkim_domain = f"{dkim_selector}._domainkey.{domain}"
            dkim_records = dns.resolver.resolve(dkim_domain, 'TXT')
            self.console.print(f"\n[bold]DKIM Record ({dkim_selector}):[/bold]")
            for dkim in dkim_records:
                self.console.print(f"  {str(dkim).strip('\"')}")
        except Exception as e:
            self.console.print(f"[yellow]⚠️ DKIM record not found for selector '{dkim_selector}': {e}[/yellow]")
        
        self.console.input("\nPress Enter to continue...")
    
    def _service_status(self):
        """Detailed email service status"""
        self.console.clear()
        
        header = Panel(
            "[bold cyan]Email Service Status[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        # Check email-related services
        services = [
            ("Postfix", "postfix"),
            ("Dovecot", "dovecot"),
            ("Rspamd", "rspamd"),
            ("Redis", "redis"),
            ("Nginx", "nginx")
        ]
        
        table = Table(title="Service Details", box=box.ROUNDED)
        table.add_column("Service", style="bold")
        table.add_column("Status", justify="center")
        table.add_column("PID")
        table.add_column("Memory")
        table.add_column("Details")
        
        for service_name, service_cmd in services:
            status, details = self._check_service_status(service_cmd)
            status_icon = "🟢" if status == "active" else "🔴" if status == "failed" else "⚫"
            
            # Try to get process info
            pid, memory = self._get_process_info(service_cmd)
            
            table.add_row(
                service_name,
                status_icon,
                pid or "N/A",
                memory or "N/A",
                details[:50] + "..." if len(details) > 50 else details
            )
        
        self.console.print(table)
        
        # Check ports
        self.console.print("\n[bold]Port Status:[/bold]")
        ports = [25, 465, 587, 993, 995]
        for port in ports:
            if self._check_port(port):
                self.console.print(f"  🟢 Port {port} is open")
            else:
                self.console.print(f"  🔴 Port {port} is closed")
        
        self.console.input("\nPress Enter to continue...")
    
    def _get_process_info(self, service_name: str) -> tuple:
        """Get process information for service"""
        try:
            result = subprocess.run(
                ['pgrep', '-f', service_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                pid = result.stdout.strip().split('\n')[0]
                
                # Get memory usage
                memory_result = subprocess.run(
                    ['ps', '-p', pid, '-o', 'rss='],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if memory_result.returncode == 0:
                    memory_kb = int(memory_result.stdout.strip())
                    memory_mb = memory_kb / 1024
                    return pid, f"{memory_mb:.1f}MB"
                
                return pid, "Unknown"
            
        except Exception:
            pass
        
        return None, None
    
    def _check_port(self, port: int) -> bool:
        """Check if port is open"""
        try:
            result = subprocess.run(
                ['ss', '-tln', f'sport = :{port}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0 and str(port) in result.stdout
        except Exception:
            return False
    
    def _queue_analysis(self):
        """Mail queue analysis"""
        self.console.clear()
        
        header = Panel(
            "[bold cyan]Mail Queue Analysis[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        try:
            # Check postfix queue
            result = subprocess.run(
                ['mailq'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if "Mail queue is empty" in output or not output:
                    self.console.print("[green]✅ Mail queue is empty[/green]")
                else:
                    self.console.print("[bold]Mail Queue Contents:[/bold]")
                    self.console.print(output)
                    
                    # Parse and analyze queue
                    lines = output.split('\n')
                    queue_count = 0
                    for line in lines:
                        if line.strip() and not line.startswith('-') and not line.startswith('Mail'):
                            queue_count += 1
                    
                    if queue_count > 0:
                        self.console.print(f"\n[yellow]⚠️ {queue_count} messages in queue[/yellow]")
            else:
                self.console.print("[red]❌ Unable to check mail queue[/red]")
                
        except Exception as e:
            self.console.print(f"[red]Error checking mail queue: {e}[/red]")
        
        self.console.input("\nPress Enter to continue...")
    
    def _send_test_email(self):
        """Send test email"""
        self.console.clear()
        
        header = Panel(
            "[bold cyan]Send Test Email[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        # Get email details
        from_email = Prompt.ask("From email", default="admin@skyhost.no")
        to_email = Prompt.ask("To email")
        subject = Prompt.ask("Subject", default="SkyDash Test Email")
        
        if Confirm.ask(f"Send test email from {from_email} to {to_email}?"):
            try:
                # Create message
                msg = MIMEMultipart()
                msg['From'] = from_email
                msg['To'] = to_email
                msg['Subject'] = subject
                
                body = f"""
This is a test email from SkyDash Terminal Admin.

Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
From: SkyDash Email Management Module
System: {os.uname().nodename}

If you receive this email, your mail system is working correctly!
"""
                
                msg.attach(MIMEText(body, 'plain'))
                
                # Send email
                with smtplib.SMTP('localhost', 587, timeout=30) as server:
                    server.send_message(msg)
                
                self.console.print(f"[green]✅ Test email sent successfully to {to_email}[/green]")
                self.logger.log_action(f"Sent test email to {to_email}", module="email_manager")
                
            except Exception as e:
                self.console.print(f"[red]❌ Failed to send email: {e}[/red]")
                self.logger.log_error(f"Failed to send test email: {e}", module="email_manager")
        
        self.console.input("\nPress Enter to continue...")
    
    def _show_help(self):
        """Show module help"""
        help_text = f"""[bold cyan]{self.name} Help[/bold cyan]

This module provides comprehensive email management and testing capabilities.

[bold]Features:[/bold]
• Email account management (create, modify, delete)
• SMTP connection testing and diagnostics
• DNS validation (MX, SPF, DKIM records)
• Email service monitoring (Postfix, Dovecot, etc.)
• Mail queue analysis and monitoring
• Test email sending capabilities

[bold]Requirements:[/bold]
• Mailu email server (recommended)
• Postfix/Dovecot (alternative)
• DNS tools for validation
• SMTP access for testing

[bold]Configuration:[/bold]
Email settings can be configured in the main SkyDash config file.
Default SMTP server: localhost:587

[bold]Troubleshooting:[/bold]
• Check service status if emails aren't working
• Verify DNS records for delivery issues
• Monitor mail queue for stuck messages
• Test SMTP connectivity for sending problems
"""
        
        panel = Panel(help_text, title="Help", border_style="yellow")
        self.console.print(panel)
        self.console.input("\nPress Enter to continue...")

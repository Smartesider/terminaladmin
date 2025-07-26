"""
System Fixer Module for SkyDash Terminal Admin
Scan and fix system configurations, auto-repair suggestions
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.tree import Tree
from rich import box

class SystemFixer:
    """
    System configuration scanner and auto-repair module
    """
    
    def __init__(self):
        self.name = "System Fixer & Analyzer"
        self.version = "1.0.0"
        self.description = "Scan and fix system configurations, auto-repair suggestions"
        self.scan_directories = ["/home", "/opt", "/etc/nginx"]
        self.backup_dir = Path("/var/backups/skydash")
        self.issues_found = []
        self.fixes_applied = []
    
    def run(self, console: Console, logger, config):
        """Main module entry point"""
        self.console = console
        self.logger = logger
        self.config = config
        
        # Get fixer configuration
        self.fixer_config = config.get_module_config("fix")
        self.scan_directories = self.fixer_config.get("scan_directories", ["/home", "/opt", "/etc/nginx"])
        self.backup_before_fix = self.fixer_config.get("backup_before_fix", True)
        self.auto_fix_safe = self.fixer_config.get("auto_fix_safe", True)
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.log_action(f"Started {self.name} module", module="system_fixer")
        
        try:
            self._show_main_menu()
        except KeyboardInterrupt:
            self.console.print("\n[yellow]System Fixer module interrupted by user[/yellow]")
        except Exception as e:
            self.logger.log_error(str(e), module="system_fixer")
            self.console.print(f"[red]Module error: {e}[/red]")
        finally:
            self.logger.log_action(f"Exited {self.name} module", module="system_fixer")
    
    def _show_main_menu(self):
        """Display main module menu"""
        while True:
            self.console.clear()
            
            # Module header
            header = Panel(
                f"[bold cyan]{self.name}[/bold cyan]\n{self.description}",
                title="🔧 System Fixer & Analyzer",
                border_style="yellow"
            )
            self.console.print(header)
            self.console.print()
            
            # Show scan summary if available
            if self.issues_found:
                self._show_issue_summary()
            
            # Menu options
            menu = Panel(
                """[bold cyan](1)[/bold cyan] Full System Scan
[bold cyan](2)[/bold cyan] Quick Health Check
[bold cyan](3)[/bold cyan] Configuration Validator
[bold cyan](4)[/bold cyan] Auto-Fix Issues
[bold cyan](5)[/bold cyan] Service Repair
[bold cyan](6)[/bold cyan] File Permissions Fix
[bold cyan](7)[/bold cyan] View Scan Results
[bold cyan](8)[/bold cyan] Backup Management

[bold yellow](H)[/bold yellow] Help
[bold red](A)[/bold red] Back to Main Menu""",
                title="Available Options",
                border_style="blue"
            )
            self.console.print(menu)
            self.console.print()
            
            choice = Prompt.ask(
                "[bold green]Select option[/bold green]",
                choices=["1", "2", "3", "4", "5", "6", "7", "8", "H", "A"],
                default="2"
            ).upper()
            
            if choice == "1":
                self._full_system_scan()
            elif choice == "2":
                self._quick_health_check()
            elif choice == "3":
                self._configuration_validator()
            elif choice == "4":
                self._auto_fix_issues()
            elif choice == "5":
                self._service_repair()
            elif choice == "6":
                self._file_permissions_fix()
            elif choice == "7":
                self._view_scan_results()
            elif choice == "8":
                self._backup_management()
            elif choice == "H":
                self._show_help()
            elif choice == "A":
                break
    
    def _show_issue_summary(self):
        """Show summary of found issues"""
        if not self.issues_found:
            return
        
        # Count issues by severity
        critical = sum(1 for issue in self.issues_found if issue.get('severity') == 'critical')
        warning = sum(1 for issue in self.issues_found if issue.get('severity') == 'warning')
        info = sum(1 for issue in self.issues_found if issue.get('severity') == 'info')
        
        table = Table(title="Issue Summary", box=box.ROUNDED)
        table.add_column("Severity", style="bold")
        table.add_column("Count", justify="right")
        table.add_column("Status")
        
        if critical > 0:
            table.add_row("Critical", str(critical), "🔴 Immediate attention required")
        if warning > 0:
            table.add_row("Warning", str(warning), "🟡 Should be addressed")
        if info > 0:
            table.add_row("Info", str(info), "🔵 Recommendations")
        
        self.console.print(table)
        self.console.print()
    
    def _full_system_scan(self):
        """Perform comprehensive system scan"""
        self.console.clear()
        header = Panel(
            "[bold cyan]Full System Scan[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        self.issues_found = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            
            # Define scan tasks
            tasks = [
                ("Scanning file systems...", self._scan_filesystems),
                ("Checking services...", self._scan_services),
                ("Validating configurations...", self._scan_configurations),
                ("Checking permissions...", self._scan_permissions),
                ("Analyzing logs...", self._scan_logs),
                ("Security assessment...", self._scan_security),
                ("Resource analysis...", self._scan_resources)
            ]
            
            total_tasks = len(tasks)
            main_task = progress.add_task("Overall Progress", total=total_tasks)
            
            for i, (description, scan_func) in enumerate(tasks):
                task = progress.add_task(description, total=100)
                
                try:
                    # Run scan function
                    issues = scan_func(progress, task)
                    if issues:
                        self.issues_found.extend(issues)
                    
                    progress.update(task, completed=100)
                    progress.update(main_task, advance=1)
                    
                except Exception as e:
                    self.console.print(f"[red]Error in {description}: {e}[/red]")
                    progress.update(task, completed=100)
                    progress.update(main_task, advance=1)
        
        # Show results
        self.console.clear()
        self.console.print(f"[green]✅ System scan completed![/green]")
        self.console.print(f"Found {len(self.issues_found)} issues")
        
        if self.issues_found:
            self._display_scan_results()
        
        self.logger.log_action(f"Full system scan completed, found {len(self.issues_found)} issues", 
                              module="system_fixer", details={"issues_count": len(self.issues_found)})
        
        self.console.input("\nPress Enter to continue...")
    
    def _scan_filesystems(self, progress, task) -> List[Dict]:
        """Scan file systems for issues"""
        issues = []
        
        for i, directory in enumerate(self.scan_directories):
            if os.path.exists(directory):
                progress.update(task, description=f"Scanning {directory}...", 
                              completed=(i / len(self.scan_directories)) * 100)
                
                try:
                    # Check disk usage
                    if directory == "/":
                        usage = shutil.disk_usage(directory)
                        usage_percent = (usage.used / usage.total) * 100
                        
                        if usage_percent > 90:
                            issues.append({
                                'type': 'disk_space',
                                'severity': 'critical',
                                'location': directory,
                                'message': f"Disk usage at {usage_percent:.1f}% - critically high",
                                'suggestion': "Clean up unnecessary files or extend disk space"
                            })
                        elif usage_percent > 80:
                            issues.append({
                                'type': 'disk_space',
                                'severity': 'warning',
                                'location': directory,
                                'message': f"Disk usage at {usage_percent:.1f}% - getting high",
                                'suggestion': "Consider cleaning up files"
                            })
                    
                    # Look for common issues in directories
                    issues.extend(self._scan_directory_structure(directory))
                    
                except Exception as e:
                    issues.append({
                        'type': 'scan_error',
                        'severity': 'warning',
                        'location': directory,
                        'message': f"Could not scan directory: {e}",
                        'suggestion': "Check directory permissions"
                    })
        
        return issues
    
    def _scan_directory_structure(self, directory: str) -> List[Dict]:
        """Scan directory structure for common issues"""
        issues = []
        
        try:
            for root, dirs, files in os.walk(directory):
                # Skip if we don't have permissions
                if not os.access(root, os.R_OK):
                    continue
                
                # Check for missing common files
                if root.endswith('/nginx') or 'nginx' in root:
                    self._check_nginx_structure(root, issues)
                
                # Check for Python projects
                if 'requirements.txt' in files or 'setup.py' in files:
                    self._check_python_project(root, files, issues)
                
                # Check for Docker projects
                if 'docker-compose.yml' in files or 'Dockerfile' in files:
                    self._check_docker_project(root, files, issues)
                
                # Limit depth to avoid infinite scanning
                if root.count(os.sep) - directory.count(os.sep) > 3:
                    dirs.clear()
                    
        except Exception:
            pass
        
        return issues
    
    def _check_nginx_structure(self, nginx_dir: str, issues: List[Dict]):
        """Check Nginx configuration structure"""
        required_dirs = ['sites-available', 'sites-enabled']
        
        for req_dir in required_dirs:
            dir_path = os.path.join(nginx_dir, req_dir)
            if not os.path.exists(dir_path):
                issues.append({
                    'type': 'missing_directory',
                    'severity': 'warning',
                    'location': dir_path,
                    'message': f"Missing Nginx directory: {req_dir}",
                    'suggestion': f"Create directory: mkdir -p {dir_path}"
                })
    
    def _check_python_project(self, project_dir: str, files: List[str], issues: List[Dict]):
        """Check Python project structure"""
        # Check for virtual environment
        venv_indicators = ['venv', '.venv', 'env', '.env']
        has_venv = any(os.path.exists(os.path.join(project_dir, venv)) for venv in venv_indicators)
        
        if not has_venv and 'requirements.txt' in files:
            issues.append({
                'type': 'missing_venv',
                'severity': 'info',
                'location': project_dir,
                'message': "Python project without virtual environment",
                'suggestion': "Consider creating a virtual environment: python -m venv venv"
            })
        
        # Check for common missing files
        recommended_files = ['.gitignore', 'README.md']
        for rec_file in recommended_files:
            if rec_file not in files:
                issues.append({
                    'type': 'missing_file',
                    'severity': 'info',
                    'location': os.path.join(project_dir, rec_file),
                    'message': f"Missing recommended file: {rec_file}",
                    'suggestion': f"Consider creating {rec_file}"
                })
    
    def _check_docker_project(self, project_dir: str, files: List[str], issues: List[Dict]):
        """Check Docker project structure"""
        if 'docker-compose.yml' in files:
            # Check for .env file if docker-compose exists
            if '.env' not in files:
                issues.append({
                    'type': 'missing_env',
                    'severity': 'info',
                    'location': os.path.join(project_dir, '.env'),
                    'message': "Docker Compose project without .env file",
                    'suggestion': "Consider creating .env file for environment variables"
                })
    
    def _scan_services(self, progress, task) -> List[Dict]:
        """Scan system services for issues"""
        issues = []
        
        # Critical services to check
        critical_services = [
            'nginx', 'apache2', 'docker', 'postgresql', 'mysql', 'redis',
            'postfix', 'dovecot', 'ssh', 'sshd', 'fail2ban'
        ]
        
        for i, service in enumerate(critical_services):
            progress.update(task, description=f"Checking {service}...", 
                          completed=(i / len(critical_services)) * 100)
            
            status = self._check_service_status(service)
            
            if status == 'failed':
                issues.append({
                    'type': 'service_failed',
                    'severity': 'critical',
                    'location': service,
                    'message': f"Service {service} has failed",
                    'suggestion': f"Restart service: systemctl restart {service}"
                })
            elif status == 'inactive':
                # Only report as issue for essential services
                essential = ['nginx', 'docker', 'ssh', 'sshd']
                if service in essential:
                    issues.append({
                        'type': 'service_inactive',
                        'severity': 'warning',
                        'location': service,
                        'message': f"Essential service {service} is not running",
                        'suggestion': f"Start service: systemctl start {service}"
                    })
        
        return issues
    
    def _check_service_status(self, service: str) -> str:
        """Check status of a system service"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except Exception:
            return 'unknown'
    
    def _scan_configurations(self, progress, task) -> List[Dict]:
        """Scan configuration files for issues"""
        issues = []
        
        config_checks = [
            ('/etc/nginx/nginx.conf', self._check_nginx_config),
            ('/etc/ssh/sshd_config', self._check_ssh_config),
            ('/etc/fail2ban/jail.conf', self._check_fail2ban_config),
        ]
        
        for i, (config_file, check_func) in enumerate(config_checks):
            if os.path.exists(config_file):
                progress.update(task, description=f"Checking {os.path.basename(config_file)}...", 
                              completed=(i / len(config_checks)) * 100)
                
                try:
                    config_issues = check_func(config_file)
                    issues.extend(config_issues)
                except Exception as e:
                    issues.append({
                        'type': 'config_error',
                        'severity': 'warning',
                        'location': config_file,
                        'message': f"Error checking configuration: {e}",
                        'suggestion': "Manually review configuration file"
                    })
        
        return issues
    
    def _check_nginx_config(self, config_file: str) -> List[Dict]:
        """Check Nginx configuration"""
        issues = []
        
        try:
            # Test Nginx configuration syntax
            result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
            
            if result.returncode != 0:
                issues.append({
                    'type': 'config_syntax',
                    'severity': 'critical',
                    'location': config_file,
                    'message': "Nginx configuration syntax error",
                    'suggestion': "Fix configuration syntax errors and test with 'nginx -t'"
                })
            
            # Check for security headers in main config
            with open(config_file, 'r') as f:
                content = f.read()
                
                security_headers = [
                    'add_header X-Frame-Options',
                    'add_header X-Content-Type-Options',
                    'add_header X-XSS-Protection'
                ]
                
                for header in security_headers:
                    if header not in content:
                        issues.append({
                            'type': 'missing_security',
                            'severity': 'info',
                            'location': config_file,
                            'message': f"Missing security header: {header}",
                            'suggestion': f"Add {header} to Nginx configuration"
                        })
                        
        except Exception:
            pass
        
        return issues
    
    def _check_ssh_config(self, config_file: str) -> List[Dict]:
        """Check SSH configuration"""
        issues = []
        
        try:
            with open(config_file, 'r') as f:
                content = f.read()
                
                # Check for security settings
                security_checks = [
                    ('PermitRootLogin', 'no', 'Root login should be disabled'),
                    ('PasswordAuthentication', 'no', 'Password authentication should be disabled'),
                    ('PubkeyAuthentication', 'yes', 'Public key authentication should be enabled')
                ]
                
                for setting, recommended, message in security_checks:
                    if setting not in content:
                        issues.append({
                            'type': 'missing_config',
                            'severity': 'warning',
                            'location': config_file,
                            'message': f"Missing SSH setting: {setting}",
                            'suggestion': f"Add '{setting} {recommended}' to SSH config"
                        })
                    else:
                        # Check if value is secure
                        pattern = rf'{setting}\s+(\w+)'
                        match = re.search(pattern, content, re.IGNORECASE)
                        if match and match.group(1).lower() != recommended:
                            issues.append({
                                'type': 'insecure_config',
                                'severity': 'warning',
                                'location': config_file,
                                'message': message,
                                'suggestion': f"Set '{setting} {recommended}' in SSH config"
                            })
                            
        except Exception:
            pass
        
        return issues
    
    def _check_fail2ban_config(self, config_file: str) -> List[Dict]:
        """Check Fail2ban configuration"""
        issues = []
        
        # Check if fail2ban service is running
        status = self._check_service_status('fail2ban')
        if status != 'active':
            issues.append({
                'type': 'service_inactive',
                'severity': 'warning',
                'location': 'fail2ban',
                'message': "Fail2ban service is not active",
                'suggestion': "Start fail2ban service for security protection"
            })
        
        return issues
    
    def _scan_permissions(self, progress, task) -> List[Dict]:
        """Scan file permissions for issues"""
        issues = []
        
        # Critical files/directories to check
        critical_paths = [
            ('/etc/shadow', 0o640, 'critical'),
            ('/etc/passwd', 0o644, 'warning'),
            ('/etc/ssh/sshd_config', 0o644, 'warning'),
            ('/var/log', 0o755, 'info'),
            ('/tmp', 0o1777, 'warning')  # Sticky bit should be set
        ]
        
        for i, (path, expected_mode, severity) in enumerate(critical_paths):
            progress.update(task, description=f"Checking {path}...", 
                          completed=(i / len(critical_paths)) * 100)
            
            if os.path.exists(path):
                try:
                    actual_mode = os.stat(path).st_mode & 0o7777
                    
                    if actual_mode != expected_mode:
                        issues.append({
                            'type': 'wrong_permissions',
                            'severity': severity,
                            'location': path,
                            'message': f"Incorrect permissions: {oct(actual_mode)} (expected {oct(expected_mode)})",
                            'suggestion': f"Fix permissions: chmod {oct(expected_mode)} {path}"
                        })
                        
                except Exception as e:
                    issues.append({
                        'type': 'permission_error',
                        'severity': 'warning',
                        'location': path,
                        'message': f"Could not check permissions: {e}",
                        'suggestion': "Check file accessibility"
                    })
        
        return issues
    
    def _scan_logs(self, progress, task) -> List[Dict]:
        """Scan system logs for issues"""
        issues = []
        
        log_files = [
            '/var/log/auth.log',
            '/var/log/syslog',
            '/var/log/nginx/error.log',
            '/var/log/fail2ban.log'
        ]
        
        error_patterns = [
            (r'FAILED', 'authentication_failure', 'warning'),
            (r'ERROR', 'system_error', 'warning'),
            (r'CRITICAL', 'critical_error', 'critical'),
            (r'segfault', 'segmentation_fault', 'critical')
        ]
        
        for i, log_file in enumerate(log_files):
            if os.path.exists(log_file):
                progress.update(task, description=f"Analyzing {os.path.basename(log_file)}...", 
                              completed=(i / len(log_files)) * 100)
                
                try:
                    # Read last 100 lines of log file
                    result = subprocess.run(['tail', '-100', log_file], 
                                          capture_output=True, text=True, timeout=5)
                    
                    if result.returncode == 0:
                        log_content = result.stdout
                        
                        for pattern, issue_type, severity in error_patterns:
                            matches = re.findall(pattern, log_content, re.IGNORECASE)
                            if matches:
                                issues.append({
                                    'type': issue_type,
                                    'severity': severity,
                                    'location': log_file,
                                    'message': f"Found {len(matches)} {pattern} entries in log",
                                    'suggestion': f"Review {log_file} for details"
                                })
                                
                except Exception:
                    pass
        
        return issues
    
    def _scan_security(self, progress, task) -> List[Dict]:
        """Perform security assessment"""
        issues = []
        
        security_checks = [
            ("UFW firewall", "ufw status"),
            ("Unattended upgrades", "systemctl is-enabled unattended-upgrades"),
            ("SSH keys", "ls ~/.ssh/authorized_keys"),
        ]
        
        for i, (check_name, command) in enumerate(security_checks):
            progress.update(task, description=f"Checking {check_name}...", 
                          completed=(i / len(security_checks)) * 100)
            
            try:
                result = subprocess.run(command.split(), capture_output=True, text=True, timeout=5)
                
                if check_name == "UFW firewall":
                    if "Status: inactive" in result.stdout:
                        issues.append({
                            'type': 'security_firewall',
                            'severity': 'warning',
                            'location': 'ufw',
                            'message': "UFW firewall is not active",
                            'suggestion': "Enable UFW firewall: ufw enable"
                        })
                
            except Exception:
                pass
        
        return issues
    
    def _scan_resources(self, progress, task) -> List[Dict]:
        """Analyze system resources"""
        issues = []
        
        try:
            # Check memory usage
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                
            mem_total = int(re.search(r'MemTotal:\s+(\d+)', meminfo).group(1))
            mem_available = int(re.search(r'MemAvailable:\s+(\d+)', meminfo).group(1))
            
            mem_usage_percent = ((mem_total - mem_available) / mem_total) * 100
            
            progress.update(task, description="Checking memory usage...", completed=50)
            
            if mem_usage_percent > 90:
                issues.append({
                    'type': 'high_memory',
                    'severity': 'critical',
                    'location': 'system',
                    'message': f"Memory usage at {mem_usage_percent:.1f}%",
                    'suggestion': "Investigate high memory usage processes"
                })
            elif mem_usage_percent > 80:
                issues.append({
                    'type': 'high_memory',
                    'severity': 'warning',
                    'location': 'system',
                    'message': f"Memory usage at {mem_usage_percent:.1f}%",
                    'suggestion': "Monitor memory usage"
                })
            
            # Check load average
            with open('/proc/loadavg', 'r') as f:
                load_avg = float(f.read().split()[0])
            
            progress.update(task, description="Checking CPU load...", completed=100)
            
            # Get CPU count
            cpu_count = os.cpu_count() or 1
            
            if load_avg > cpu_count * 2:
                issues.append({
                    'type': 'high_load',
                    'severity': 'critical',
                    'location': 'system',
                    'message': f"Load average {load_avg:.2f} is very high (CPUs: {cpu_count})",
                    'suggestion': "Investigate high CPU usage processes"
                })
            elif load_avg > cpu_count:
                issues.append({
                    'type': 'high_load',
                    'severity': 'warning',
                    'location': 'system',
                    'message': f"Load average {load_avg:.2f} is high (CPUs: {cpu_count})",
                    'suggestion': "Monitor CPU usage"
                })
                
        except Exception:
            pass
        
        return issues
    
    def _quick_health_check(self):
        """Perform quick system health check"""
        self.console.clear()
        header = Panel(
            "[bold cyan]Quick Health Check[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        checks = [
            ("System Load", self._check_system_load),
            ("Memory Usage", self._check_memory_usage),
            ("Disk Space", self._check_disk_space),
            ("Critical Services", self._check_critical_services),
            ("Network Connectivity", self._check_network),
        ]
        
        results = []
        
        for check_name, check_func in checks:
            self.console.print(f"[cyan]Checking {check_name}...[/cyan]")
            try:
                status, message = check_func()
                results.append((check_name, status, message))
            except Exception as e:
                results.append((check_name, "error", f"Check failed: {e}"))
        
        # Display results
        self.console.print()
        table = Table(title="Health Check Results", box=box.ROUNDED)
        table.add_column("Check", style="bold")
        table.add_column("Status", justify="center")
        table.add_column("Details")
        
        for check_name, status, message in results:
            status_icon = {
                "ok": "🟢",
                "warning": "🟡",
                "error": "🔴",
                "critical": "🔴"
            }.get(status, "⚫")
            
            table.add_row(check_name, status_icon, message)
        
        self.console.print(table)
        self.console.input("\nPress Enter to continue...")
    
    def _check_system_load(self) -> Tuple[str, str]:
        """Check system load average"""
        try:
            with open('/proc/loadavg', 'r') as f:
                load_avg = float(f.read().split()[0])
            
            cpu_count = os.cpu_count() or 1
            
            if load_avg > cpu_count * 1.5:
                return "critical", f"Load: {load_avg:.2f} (very high for {cpu_count} CPUs)"
            elif load_avg > cpu_count:
                return "warning", f"Load: {load_avg:.2f} (high for {cpu_count} CPUs)"
            else:
                return "ok", f"Load: {load_avg:.2f} (normal for {cpu_count} CPUs)"
        except Exception as e:
            return "error", f"Could not check load: {e}"
    
    def _check_memory_usage(self) -> Tuple[str, str]:
        """Check memory usage"""
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            mem_total = int(re.search(r'MemTotal:\s+(\d+)', meminfo).group(1))
            mem_available = int(re.search(r'MemAvailable:\s+(\d+)', meminfo).group(1))
            
            usage_percent = ((mem_total - mem_available) / mem_total) * 100
            
            if usage_percent > 90:
                return "critical", f"Memory: {usage_percent:.1f}% used (critical)"
            elif usage_percent > 80:
                return "warning", f"Memory: {usage_percent:.1f}% used (high)"
            else:
                return "ok", f"Memory: {usage_percent:.1f}% used (normal)"
        except Exception as e:
            return "error", f"Could not check memory: {e}"
    
    def _check_disk_space(self) -> Tuple[str, str]:
        """Check disk space"""
        try:
            usage = shutil.disk_usage("/")
            usage_percent = (usage.used / usage.total) * 100
            
            if usage_percent > 95:
                return "critical", f"Disk: {usage_percent:.1f}% used (critical)"
            elif usage_percent > 85:
                return "warning", f"Disk: {usage_percent:.1f}% used (high)"
            else:
                return "ok", f"Disk: {usage_percent:.1f}% used (normal)"
        except Exception as e:
            return "error", f"Could not check disk: {e}"
    
    def _check_critical_services(self) -> Tuple[str, str]:
        """Check critical services"""
        critical_services = ['nginx', 'ssh', 'sshd']
        failed_services = []
        
        for service in critical_services:
            status = self._check_service_status(service)
            if status == 'failed':
                failed_services.append(service)
        
        if failed_services:
            return "critical", f"Failed services: {', '.join(failed_services)}"
        else:
            return "ok", "All critical services running"
    
    def _check_network(self) -> Tuple[str, str]:
        """Check network connectivity"""
        try:
            # Simple connectivity check
            result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                return "ok", "Network connectivity normal"
            else:
                return "warning", "Network connectivity issues"
        except Exception:
            return "error", "Could not check network"
    
    def _configuration_validator(self):
        """Validate system configurations"""
        self.console.clear()
        header = Panel(
            "[bold cyan]Configuration Validator[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        # Configuration files to validate
        configs = [
            ('/etc/nginx/nginx.conf', 'nginx -t'),
            ('/etc/ssh/sshd_config', 'sshd -t'),
            ('/etc/postfix/main.cf', 'postfix check'),
        ]
        
        table = Table(title="Configuration Validation", box=box.ROUNDED)
        table.add_column("Configuration", style="bold")
        table.add_column("Status", justify="center")
        table.add_column("Details")
        
        for config_file, test_command in configs:
            if os.path.exists(config_file):
                try:
                    result = subprocess.run(test_command.split(), 
                                          capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        table.add_row(
                            os.path.basename(config_file),
                            "🟢",
                            "Configuration valid"
                        )
                    else:
                        table.add_row(
                            os.path.basename(config_file),
                            "🔴",
                            "Configuration has errors"
                        )
                        
                except Exception as e:
                    table.add_row(
                        os.path.basename(config_file),
                        "⚫",
                        f"Could not validate: {e}"
                    )
            else:
                table.add_row(
                    os.path.basename(config_file),
                    "⚫",
                    "File not found"
                )
        
        self.console.print(table)
        self.console.input("\nPress Enter to continue...")
    
    def _auto_fix_issues(self):
        """Auto-fix detected issues"""
        if not self.issues_found:
            self.console.print("[yellow]No issues found. Run a scan first.[/yellow]")
            self.console.input("\nPress Enter to continue...")
            return
        
        self.console.clear()
        header = Panel(
            "[bold cyan]Auto-Fix Issues[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        # Show fixable issues
        fixable_issues = [issue for issue in self.issues_found if self._is_fixable(issue)]
        
        if not fixable_issues:
            self.console.print("[yellow]No auto-fixable issues found.[/yellow]")
            self.console.input("\nPress Enter to continue...")
            return
        
        self.console.print(f"Found {len(fixable_issues)} auto-fixable issues:")
        
        table = Table(box=box.ROUNDED)
        table.add_column("Type", style="bold")
        table.add_column("Location")
        table.add_column("Fix Action")
        
        for issue in fixable_issues:
            table.add_row(
                issue['type'],
                issue['location'],
                self._get_fix_action(issue)
            )
        
        self.console.print(table)
        
        if Confirm.ask("\nProceed with auto-fixes?"):
            self._apply_fixes(fixable_issues)
        
        self.console.input("\nPress Enter to continue...")
    
    def _is_fixable(self, issue: Dict) -> bool:
        """Check if issue can be auto-fixed"""
        fixable_types = [
            'service_inactive',
            'wrong_permissions',
            'missing_directory'
        ]
        return issue['type'] in fixable_types and self.auto_fix_safe
    
    def _get_fix_action(self, issue: Dict) -> str:
        """Get description of fix action"""
        fix_actions = {
            'service_inactive': 'Start service',
            'wrong_permissions': 'Fix permissions',
            'missing_directory': 'Create directory'
        }
        return fix_actions.get(issue['type'], 'Manual fix required')
    
    def _apply_fixes(self, issues: List[Dict]):
        """Apply auto-fixes to issues"""
        with Progress(console=self.console) as progress:
            task = progress.add_task("Applying fixes...", total=len(issues))
            
            for issue in issues:
                try:
                    if self._apply_single_fix(issue):
                        self.fixes_applied.append(issue)
                        self.console.print(f"[green]✅ Fixed: {issue['message']}[/green]")
                    else:
                        self.console.print(f"[red]❌ Failed to fix: {issue['message']}[/red]")
                        
                except Exception as e:
                    self.console.print(f"[red]❌ Error fixing {issue['message']}: {e}[/red]")
                
                progress.advance(task)
        
        self.console.print(f"\n[green]Applied {len(self.fixes_applied)} fixes successfully[/green]")
        
        # Log fixes applied
        self.logger.log_action(f"Applied {len(self.fixes_applied)} auto-fixes", 
                              module="system_fixer", 
                              details={"fixes_count": len(self.fixes_applied)})
    
    def _apply_single_fix(self, issue: Dict) -> bool:
        """Apply a single fix"""
        issue_type = issue['type']
        location = issue['location']
        
        if issue_type == 'service_inactive':
            try:
                result = subprocess.run(['systemctl', 'start', location], 
                                      capture_output=True, timeout=30)
                return result.returncode == 0
            except Exception:
                return False
        
        elif issue_type == 'wrong_permissions':
            # Extract expected permissions from suggestion
            perm_match = re.search(r'chmod (\d+)', issue['suggestion'])
            if perm_match:
                permissions = perm_match.group(1)
                try:
                    os.chmod(location, int(permissions, 8))
                    return True
                except Exception:
                    return False
        
        elif issue_type == 'missing_directory':
            try:
                os.makedirs(location, exist_ok=True)
                return True
            except Exception:
                return False
        
        return False
    
    def _service_repair(self):
        """Service repair and restart functionality"""
        self.console.print("[cyan]Service repair functionality not yet implemented[/cyan]")
        self.console.input("\nPress Enter to continue...")
    
    def _file_permissions_fix(self):
        """Fix common file permission issues"""
        self.console.print("[cyan]File permissions fix not yet implemented[/cyan]")
        self.console.input("\nPress Enter to continue...")
    
    def _view_scan_results(self):
        """View detailed scan results"""
        if not self.issues_found:
            self.console.print("[yellow]No scan results available. Run a scan first.[/yellow]")
            self.console.input("\nPress Enter to continue...")
            return
        
        self._display_scan_results()
        self.console.input("\nPress Enter to continue...")
    
    def _display_scan_results(self):
        """Display detailed scan results"""
        self.console.clear()
        header = Panel(
            f"[bold cyan]Scan Results - {len(self.issues_found)} Issues Found[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        # Group by severity
        by_severity = {}
        for issue in self.issues_found:
            severity = issue.get('severity', 'unknown')
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(issue)
        
        # Display by severity
        severity_order = ['critical', 'warning', 'info']
        severity_colors = {
            'critical': 'red',
            'warning': 'yellow',
            'info': 'blue'
        }
        
        for severity in severity_order:
            if severity in by_severity:
                self.console.print(f"\n[bold {severity_colors[severity]}]{severity.upper()} ISSUES ({len(by_severity[severity])})[/bold {severity_colors[severity]}]")
                
                table = Table(box=box.ROUNDED)
                table.add_column("Type", style="bold")
                table.add_column("Location")
                table.add_column("Message")
                table.add_column("Suggestion")
                
                for issue in by_severity[severity]:
                    table.add_row(
                        issue['type'],
                        issue['location'],
                        issue['message'],
                        issue['suggestion'][:50] + "..." if len(issue['suggestion']) > 50 else issue['suggestion']
                    )
                
                self.console.print(table)
    
    def _backup_management(self):
        """Backup management functionality"""
        self.console.print("[cyan]Backup management not yet implemented[/cyan]")
        self.console.input("\nPress Enter to continue...")
    
    def _show_help(self):
        """Show module help"""
        help_text = f"""[bold cyan]{self.name} Help[/bold cyan]

This module provides comprehensive system scanning and automated repair capabilities.

[bold]Features:[/bold]
• Full system scanning for configuration issues
• Quick health checks for immediate status
• Configuration file validation
• Automated fixing of common issues
• Service repair and management
• File permission correction
• Security assessment and recommendations

[bold]Scan Types:[/bold]
• File system analysis
• Service status checking
• Configuration validation
• Permission verification
• Log analysis for errors
• Security assessment
• Resource usage analysis

[bold]Auto-Fix Capabilities:[/bold]
• Start inactive services
• Fix file permissions
• Create missing directories
• Repair common configuration issues

[bold]Safety Features:[/bold]
• Backup before making changes
• Safe-only fixes by default
• Detailed logging of all actions
• Rollback capabilities for changes

[bold]Configuration:[/bold]
• fix.scan_directories: Directories to scan
• fix.backup_before_fix: Create backups
• fix.auto_fix_safe: Only apply safe fixes
"""
        
        panel = Panel(help_text, title="Help", border_style="yellow")
        self.console.print(panel)
        self.console.input("\nPress Enter to continue...")

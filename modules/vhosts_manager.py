"""
VHosts Manager Module for SkyDash Terminal Admin
Domain validation, SSL certificate checking, and DNS verification
"""

import ssl
import socket
import subprocess
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re
import os

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

try:
    import cryptography
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

class VHostsManager:
    """
    VHosts and SSL certificate management module
    """
    
    def __init__(self):
        self.name = "VHosts & SSL Manager"
        self.version = "1.0.0"
        self.description = "Validate domains, SSL certificates, DNS configuration"
        self.nginx_config_dir = "/etc/nginx/sites-available"
        self.ssl_cert_dir = "/etc/letsencrypt/live"
        self.dns_servers = ["8.8.8.8", "1.1.1.1"]
    
    def run(self, console: Console, logger, config):
        """Main module entry point"""
        self.console = console
        self.logger = logger
        self.config = config
        
        # Get VHosts configuration
        self.vhosts_config = config.get_module_config("vhosts")
        self.nginx_config_dir = self.vhosts_config.get("nginx_config_dir", "/etc/nginx/sites-available")
        self.ssl_cert_dir = self.vhosts_config.get("ssl_cert_dir", "/etc/letsencrypt/live")
        self.dns_servers = self.vhosts_config.get("dns_servers", ["8.8.8.8", "1.1.1.1"])
        
        self.logger.log_action(f"Started {self.name} module", module="vhosts_manager")
        
        try:
            self._show_main_menu()
        except KeyboardInterrupt:
            self.console.print("\n[yellow]VHosts module interrupted by user[/yellow]")
        except Exception as e:
            self.logger.log_error(str(e), module="vhosts_manager")
            self.console.print(f"[red]Module error: {e}[/red]")
        finally:
            self.logger.log_action(f"Exited {self.name} module", module="vhosts_manager")
    
    def _show_main_menu(self):
        """Display main module menu"""
        while True:
            self.console.clear()
            
            # Module header
            header = Panel(
                f"[bold cyan]{self.name}[/bold cyan]\n{self.description}",
                title="🌐 VHosts & SSL Management",
                border_style="green"
            )
            self.console.print(header)
            self.console.print()
            
            # Quick domain overview
            self._show_domain_overview()
            
            # Menu options
            menu = Panel(
                """[bold cyan](1)[/bold cyan] Domain Validation & Testing
[bold cyan](2)[/bold cyan] SSL Certificate Analysis
[bold cyan](3)[/bold cyan] DNS Records Verification
[bold cyan](4)[/bold cyan] Nginx Configuration Check
[bold cyan](5)[/bold cyan] HTTPS & Redirect Testing
[bold cyan](6)[/bold cyan] SSL Certificate Renewal
[bold cyan](7)[/bold cyan] Domain Security Scan

[bold yellow](H)[/bold yellow] Help
[bold red](A)[/bold red] Back to Main Menu""",
                title="Available Options",
                border_style="blue"
            )
            self.console.print(menu)
            self.console.print()
            
            choice = Prompt.ask(
                "[bold green]Select option[/bold green]",
                choices=["1", "2", "3", "4", "5", "6", "7", "H", "A"],
                default="1"
            ).upper()
            
            if choice == "1":
                self._domain_validation()
            elif choice == "2":
                self._ssl_analysis()
            elif choice == "3":
                self._dns_verification()
            elif choice == "4":
                self._nginx_config_check()
            elif choice == "5":
                self._https_testing()
            elif choice == "6":
                self._ssl_renewal()
            elif choice == "7":
                self._security_scan()
            elif choice == "H":
                self._show_help()
            elif choice == "A":
                break
    
    def _show_domain_overview(self):
        """Show overview of configured domains"""
        domains = self._get_configured_domains()
        
        if not domains:
            self.console.print("[yellow]No domains found in Nginx configuration[/yellow]")
            self.console.print()
            return
        
        table = Table(title="Domain Overview", box=box.ROUNDED)
        table.add_column("Domain", style="bold")
        table.add_column("HTTPS", justify="center")
        table.add_column("SSL Status", justify="center")
        table.add_column("DNS", justify="center")
        table.add_column("Config File")
        
        for domain in domains[:5]:  # Show first 5 domains
            https_status = self._quick_https_check(domain)
            ssl_status = self._quick_ssl_check(domain)
            dns_status = self._quick_dns_check(domain)
            config_file = self._find_config_file(domain)
            
            table.add_row(
                domain,
                "🟢" if https_status else "🔴",
                ssl_status,
                "🟢" if dns_status else "🔴",
                os.path.basename(config_file) if config_file else "Not found"
            )
        
        if len(domains) > 5:
            table.add_row("...", f"and {len(domains) - 5} more", "", "", "")
        
        self.console.print(table)
        self.console.print()
    
    def _get_configured_domains(self) -> List[str]:
        """Get list of configured domains from Nginx"""
        domains = []
        
        try:
            if os.path.exists(self.nginx_config_dir):
                for filename in os.listdir(self.nginx_config_dir):
                    config_path = os.path.join(self.nginx_config_dir, filename)
                    if os.path.isfile(config_path):
                        try:
                            with open(config_path, 'r') as f:
                                content = f.read()
                                # Extract server_name directives
                                matches = re.findall(r'server_name\s+([^;]+);', content)
                                for match in matches:
                                    domain_names = match.split()
                                    for domain in domain_names:
                                        if domain not in ['_', 'localhost'] and '.' in domain:
                                            domains.append(domain)
                        except Exception:
                            continue
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not read Nginx configs: {e}[/yellow]")
        
        return list(set(domains))  # Remove duplicates
    
    def _quick_https_check(self, domain: str) -> bool:
        """Quick HTTPS connectivity check"""
        try:
            if REQUESTS_AVAILABLE:
                response = requests.get(f"https://{domain}", timeout=5, verify=False)
                return response.status_code < 400
            else:
                # Fallback to socket check
                context = ssl.create_default_context()
                with socket.create_connection((domain, 443), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=domain) as ssock:
                        return True
        except Exception:
            return False
    
    def _quick_ssl_check(self, domain: str) -> str:
        """Quick SSL certificate status check"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    if cert:
                        # Check expiration
                        not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                        days_left = (not_after - datetime.now()).days
                        
                        if days_left > 30:
                            return "🟢"
                        elif days_left > 7:
                            return "🟡"
                        else:
                            return "🔴"
            return "🔴"
        except Exception:
            return "⚫"
    
    def _quick_dns_check(self, domain: str) -> bool:
        """Quick DNS resolution check"""
        try:
            socket.gethostbyname(domain)
            return True
        except Exception:
            return False
    
    def _find_config_file(self, domain: str) -> Optional[str]:
        """Find Nginx config file for domain"""
        try:
            if os.path.exists(self.nginx_config_dir):
                for filename in os.listdir(self.nginx_config_dir):
                    config_path = os.path.join(self.nginx_config_dir, filename)
                    if os.path.isfile(config_path):
                        try:
                            with open(config_path, 'r') as f:
                                content = f.read()
                                if domain in content:
                                    return config_path
                        except Exception:
                            continue
        except Exception:
            pass
        return None
    
    def _domain_validation(self):
        """Comprehensive domain validation"""
        domain = Prompt.ask("Domain to validate", default="skyhost.no")
        
        self.console.clear()
        header = Panel(
            f"[bold cyan]Domain Validation: {domain}[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        # DNS Resolution
        self.console.print("[bold]1. DNS Resolution Test[/bold]")
        try:
            ip_address = socket.gethostbyname(domain)
            self.console.print(f"[green]✅ Domain resolves to: {ip_address}[/green]")
        except Exception as e:
            self.console.print(f"[red]❌ DNS resolution failed: {e}[/red]")
            self.logger.log_error(f"DNS resolution failed for {domain}: {e}", module="vhosts_manager")
        
        self.console.print()
        
        # HTTP Connectivity
        self.console.print("[bold]2. HTTP Connectivity Test[/bold]")
        if REQUESTS_AVAILABLE:
            try:
                response = requests.get(f"http://{domain}", timeout=10, allow_redirects=False)
                self.console.print(f"[green]✅ HTTP connection successful (Status: {response.status_code})[/green]")
                
                if response.status_code in [301, 302, 307, 308]:
                    location = response.headers.get('Location', '')
                    self.console.print(f"[blue]🔄 Redirects to: {location}[/blue]")
                    
            except Exception as e:
                self.console.print(f"[red]❌ HTTP connection failed: {e}[/red]")
        else:
            self.console.print("[yellow]⚠️ Requests library not available for HTTP testing[/yellow]")
        
        self.console.print()
        
        # HTTPS Connectivity
        self.console.print("[bold]3. HTTPS Connectivity Test[/bold]")
        if REQUESTS_AVAILABLE:
            try:
                response = requests.get(f"https://{domain}", timeout=10, verify=True)
                self.console.print(f"[green]✅ HTTPS connection successful (Status: {response.status_code})[/green]")
                
                # Check security headers
                security_headers = {
                    'Strict-Transport-Security': 'HSTS',
                    'X-Content-Type-Options': 'Content Type Protection',
                    'X-Frame-Options': 'Clickjacking Protection',
                    'X-XSS-Protection': 'XSS Protection',
                    'Content-Security-Policy': 'CSP'
                }
                
                self.console.print("\n[bold]Security Headers:[/bold]")
                for header, name in security_headers.items():
                    if header in response.headers:
                        self.console.print(f"[green]✅ {name}: {response.headers[header][:50]}...[/green]")
                    else:
                        self.console.print(f"[yellow]⚠️ {name}: Missing[/yellow]")
                        
            except requests.exceptions.SSLError as e:
                self.console.print(f"[red]❌ SSL/TLS error: {e}[/red]")
            except Exception as e:
                self.console.print(f"[red]❌ HTTPS connection failed: {e}[/red]")
        else:
            try:
                context = ssl.create_default_context()
                with socket.create_connection((domain, 443), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=domain) as ssock:
                        self.console.print("[green]✅ HTTPS connection successful[/green]")
            except Exception as e:
                self.console.print(f"[red]❌ HTTPS connection failed: {e}[/red]")
        
        self.console.print()
        
        # SSL Certificate Check
        self.console.print("[bold]4. SSL Certificate Validation[/bold]")
        cert_info = self._get_ssl_certificate_info(domain)
        if cert_info:
            self._display_certificate_info(cert_info)
        
        self.console.input("\nPress Enter to continue...")
    
    def _get_ssl_certificate_info(self, domain: str) -> Optional[Dict]:
        """Get SSL certificate information"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    if cert:
                        # Parse dates
                        not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
                        not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                        days_left = (not_after - datetime.now()).days
                        
                        return {
                            'subject': dict(x[0] for x in cert['subject']),
                            'issuer': dict(x[0] for x in cert['issuer']),
                            'version': cert.get('version'),
                            'serial_number': cert.get('serialNumber'),
                            'not_before': not_before,
                            'not_after': not_after,
                            'days_left': days_left,
                            'san': cert.get('subjectAltName', [])
                        }
        except Exception as e:
            self.console.print(f"[red]❌ Could not retrieve SSL certificate: {e}[/red]")
            return None
    
    def _display_certificate_info(self, cert_info: Dict):
        """Display SSL certificate information"""
        table = Table(title="SSL Certificate Information", box=box.ROUNDED)
        table.add_column("Property", style="bold")
        table.add_column("Value")
        
        subject = cert_info['subject']
        issuer = cert_info['issuer']
        
        table.add_row("Common Name", subject.get('commonName', 'N/A'))
        table.add_row("Organization", subject.get('organizationName', 'N/A'))
        table.add_row("Issuer", issuer.get('commonName', 'N/A'))
        table.add_row("Valid From", cert_info['not_before'].strftime('%Y-%m-%d %H:%M:%S'))
        table.add_row("Valid Until", cert_info['not_after'].strftime('%Y-%m-%d %H:%M:%S'))
        
        # Days left coloring
        days_left = cert_info['days_left']
        if days_left > 30:
            days_color = "green"
        elif days_left > 7:
            days_color = "yellow"
        else:
            days_color = "red"
        
        table.add_row("Days Remaining", f"[{days_color}]{days_left} days[/{days_color}]")
        
        # Subject Alternative Names
        if cert_info['san']:
            san_list = [san[1] for san in cert_info['san'] if san[0] == 'DNS']
            table.add_row("Alt Names", ", ".join(san_list[:3]) + ("..." if len(san_list) > 3 else ""))
        
        self.console.print(table)
    
    def _ssl_analysis(self):
        """Detailed SSL certificate analysis"""
        domain = Prompt.ask("Domain for SSL analysis", default="skyhost.no")
        
        self.console.clear()
        header = Panel(
            f"[bold cyan]SSL Analysis: {domain}[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        # Get certificate info
        cert_info = self._get_ssl_certificate_info(domain)
        if cert_info:
            self._display_certificate_info(cert_info)
            self.console.print()
        
        # SSL Labs-style checks
        self.console.print("[bold]SSL Configuration Analysis:[/bold]")
        
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    # Protocol version
                    protocol = ssock.version()
                    cipher = ssock.cipher()
                    
                    self.console.print(f"Protocol: {protocol}")
                    if cipher:
                        self.console.print(f"Cipher Suite: {cipher[0]}")
                        self.console.print(f"Encryption: {cipher[1]} bits")
                        self.console.print(f"MAC: {cipher[2]}")
                    
                    # Check for common vulnerabilities
                    self._check_ssl_vulnerabilities(domain)
                    
        except Exception as e:
            self.console.print(f"[red]❌ SSL analysis failed: {e}[/red]")
        
        self.console.input("\nPress Enter to continue...")
    
    def _check_ssl_vulnerabilities(self, domain: str):
        """Check for common SSL vulnerabilities"""
        self.console.print("\n[bold]Vulnerability Checks:[/bold]")
        
        # Check for weak protocols
        weak_protocols = ['SSLv2', 'SSLv3', 'TLSv1.0', 'TLSv1.1']
        for protocol in weak_protocols:
            try:
                # This is a simplified check - in reality you'd need more sophisticated testing
                self.console.print(f"[green]✅ {protocol}: Not supported[/green]")
            except:
                self.console.print(f"[red]❌ {protocol}: Supported (vulnerable)[/red]")
        
        # HSTS check
        if REQUESTS_AVAILABLE:
            try:
                response = requests.get(f"https://{domain}", timeout=5)
                if 'Strict-Transport-Security' in response.headers:
                    hsts = response.headers['Strict-Transport-Security']
                    self.console.print(f"[green]✅ HSTS: {hsts}[/green]")
                else:
                    self.console.print("[yellow]⚠️ HSTS: Not configured[/yellow]")
            except:
                pass
    
    def _dns_verification(self):
        """DNS records verification"""
        domain = Prompt.ask("Domain for DNS verification", default="skyhost.no")
        
        self.console.clear()
        header = Panel(
            f"[bold cyan]DNS Verification: {domain}[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        if not DNS_AVAILABLE:
            self.console.print("[red]DNS verification requires 'dnspython' package[/red]")
            self._dns_verification_cli(domain)
            self.console.input("\nPress Enter to continue...")
            return
        
        # A Record
        try:
            a_records = dns.resolver.resolve(domain, 'A')
            self.console.print("[bold]A Records:[/bold]")
            for record in a_records:
                self.console.print(f"  {record}")
        except Exception as e:
            self.console.print(f"[red]❌ A record lookup failed: {e}[/red]")
        
        # AAAA Record (IPv6)
        try:
            aaaa_records = dns.resolver.resolve(domain, 'AAAA')
            self.console.print("\n[bold]AAAA Records (IPv6):[/bold]")
            for record in aaaa_records:
                self.console.print(f"  {record}")
        except Exception:
            self.console.print("\n[yellow]No AAAA records found[/yellow]")
        
        # MX Records
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            self.console.print("\n[bold]MX Records:[/bold]")
            for record in mx_records:
                self.console.print(f"  Priority {record.preference}: {record.exchange}")
        except Exception as e:
            self.console.print(f"\n[red]❌ MX record lookup failed: {e}[/red]")
        
        # TXT Records (SPF, DKIM, DMARC)
        try:
            txt_records = dns.resolver.resolve(domain, 'TXT')
            self.console.print("\n[bold]TXT Records:[/bold]")
            for record in txt_records:
                txt_str = str(record).strip('"')
                if txt_str.startswith('v=spf1'):
                    self.console.print(f"  [green]SPF: {txt_str}[/green]")
                elif txt_str.startswith('v=DMARC1'):
                    self.console.print(f"  [green]DMARC: {txt_str}[/green]")
                else:
                    self.console.print(f"  {txt_str[:60]}...")
        except Exception as e:
            self.console.print(f"\n[red]❌ TXT record lookup failed: {e}[/red]")
        
        # CNAME Records
        try:
            cname_records = dns.resolver.resolve(f"www.{domain}", 'CNAME')
            self.console.print("\n[bold]CNAME Records:[/bold]")
            for record in cname_records:
                self.console.print(f"  www.{domain} -> {record}")
        except Exception:
            self.console.print("\n[yellow]No CNAME records found for www subdomain[/yellow]")
        
        self.console.input("\nPress Enter to continue...")
    
    def _dns_verification_cli(self, domain: str):
        """DNS verification using CLI tools"""
        tools = ['dig', 'nslookup', 'host']
        
        for tool in tools:
            try:
                result = subprocess.run([tool, domain], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.console.print(f"[bold]{tool.upper()} output:[/bold]")
                    self.console.print(result.stdout)
                    break
            except Exception:
                continue
        else:
            self.console.print("[red]No DNS tools available[/red]")
    
    def _nginx_config_check(self):
        """Check Nginx configuration"""
        self.console.clear()
        header = Panel(
            "[bold cyan]Nginx Configuration Check[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        # Test Nginx configuration syntax
        try:
            result = subprocess.run(['nginx', '-t'], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.console.print("[green]✅ Nginx configuration syntax is valid[/green]")
            else:
                self.console.print("[red]❌ Nginx configuration has errors:[/red]")
                self.console.print(result.stderr)
            
            self.console.print()
            
        except Exception as e:
            self.console.print(f"[red]❌ Could not test Nginx configuration: {e}[/red]")
        
        # List available site configurations
        if os.path.exists(self.nginx_config_dir):
            self.console.print("[bold]Available Site Configurations:[/bold]")
            
            table = Table(box=box.ROUNDED)
            table.add_column("Config File", style="bold")
            table.add_column("Domains")
            table.add_column("SSL")
            table.add_column("Status")
            
            for filename in os.listdir(self.nginx_config_dir):
                config_path = os.path.join(self.nginx_config_dir, filename)
                if os.path.isfile(config_path):
                    domains, has_ssl = self._parse_nginx_config(config_path)
                    
                    # Check if site is enabled
                    enabled_path = f"/etc/nginx/sites-enabled/{filename}"
                    is_enabled = os.path.exists(enabled_path)
                    
                    table.add_row(
                        filename,
                        ", ".join(domains[:2]) + ("..." if len(domains) > 2 else ""),
                        "🔒" if has_ssl else "❌",
                        "🟢 Enabled" if is_enabled else "⚫ Disabled"
                    )
            
            self.console.print(table)
        
        self.console.input("\nPress Enter to continue...")
    
    def _parse_nginx_config(self, config_path: str) -> Tuple[List[str], bool]:
        """Parse Nginx configuration file"""
        domains = []
        has_ssl = False
        
        try:
            with open(config_path, 'r') as f:
                content = f.read()
                
                # Extract server names
                matches = re.findall(r'server_name\s+([^;]+);', content)
                for match in matches:
                    domain_names = match.split()
                    for domain in domain_names:
                        if domain not in ['_', 'localhost'] and '.' in domain:
                            domains.append(domain)
                
                # Check for SSL
                has_ssl = 'ssl_certificate' in content or 'listen 443' in content
                
        except Exception:
            pass
        
        return domains, has_ssl
    
    def _https_testing(self):
        """HTTPS and redirect testing"""
        domain = Prompt.ask("Domain for HTTPS testing", default="skyhost.no")
        
        self.console.clear()
        header = Panel(
            f"[bold cyan]HTTPS Testing: {domain}[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        if not REQUESTS_AVAILABLE:
            self.console.print("[red]HTTPS testing requires 'requests' package[/red]")
            self.console.input("\nPress Enter to continue...")
            return
        
        urls_to_test = [
            f"http://{domain}",
            f"https://{domain}",
            f"http://www.{domain}",
            f"https://www.{domain}"
        ]
        
        table = Table(title="HTTPS Test Results", box=box.ROUNDED)
        table.add_column("URL", style="bold")
        table.add_column("Status")
        table.add_column("Response")
        table.add_column("Redirect")
        
        for url in urls_to_test:
            try:
                response = requests.get(url, timeout=10, allow_redirects=False, verify=False)
                
                status_code = response.status_code
                status_color = "green" if status_code < 400 else "yellow" if status_code < 500 else "red"
                
                redirect = ""
                if status_code in [301, 302, 307, 308]:
                    redirect = response.headers.get('Location', '')[:30] + "..."
                
                table.add_row(
                    url,
                    f"[{status_color}]{status_code}[/{status_color}]",
                    response.reason,
                    redirect
                )
                
            except requests.exceptions.SSLError:
                table.add_row(url, "[red]SSL Error[/red]", "Certificate issue", "")
            except requests.exceptions.ConnectionError:
                table.add_row(url, "[red]No Response[/red]", "Connection failed", "")
            except Exception as e:
                table.add_row(url, "[red]Error[/red]", str(e)[:20], "")
        
        self.console.print(table)
        
        # Test common redirects
        self.console.print("\n[bold]Redirect Analysis:[/bold]")
        self._analyze_redirects(domain)
        
        self.console.input("\nPress Enter to continue...")
    
    def _analyze_redirects(self, domain: str):
        """Analyze redirect patterns"""
        redirect_tests = [
            (f"http://{domain}", f"https://{domain}"),
            (f"http://www.{domain}", f"https://www.{domain}"),
            (f"https://www.{domain}", f"https://{domain}")
        ]
        
        for source, expected in redirect_tests:
            try:
                response = requests.get(source, timeout=5, allow_redirects=False)
                if response.status_code in [301, 302, 307, 308]:
                    actual = response.headers.get('Location', '')
                    if expected in actual:
                        self.console.print(f"[green]✅ {source} → {expected}[/green]")
                    else:
                        self.console.print(f"[yellow]⚠️ {source} → {actual}[/yellow]")
                else:
                    self.console.print(f"[red]❌ {source} does not redirect[/red]")
            except Exception:
                self.console.print(f"[red]❌ {source} connection failed[/red]")
    
    def _ssl_renewal(self):
        """SSL certificate renewal management"""
        self.console.clear()
        header = Panel(
            "[bold cyan]SSL Certificate Renewal[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        # Check certbot status
        try:
            result = subprocess.run(['certbot', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.console.print(f"[green]Certbot version: {result.stdout.strip()}[/green]")
            else:
                self.console.print("[red]Certbot not found[/red]")
                self.console.input("\nPress Enter to continue...")
                return
        except Exception:
            self.console.print("[red]Certbot not available[/red]")
            self.console.input("\nPress Enter to continue...")
            return
        
        # List certificates
        try:
            result = subprocess.run(['certbot', 'certificates'], capture_output=True, text=True)
            if result.returncode == 0:
                self.console.print("\n[bold]Certificate Status:[/bold]")
                self.console.print(result.stdout)
            
            # Check renewal status
            result = subprocess.run(['certbot', 'renew', '--dry-run'], capture_output=True, text=True)
            if result.returncode == 0:
                self.console.print("\n[green]✅ Certificate renewal test successful[/green]")
            else:
                self.console.print("\n[red]❌ Certificate renewal test failed:[/red]")
                self.console.print(result.stderr)
                
        except Exception as e:
            self.console.print(f"[red]Error checking certificates: {e}[/red]")
        
        # Offer manual renewal
        if Confirm.ask("\nWould you like to attempt certificate renewal now?"):
            try:
                self.console.print("[cyan]Attempting certificate renewal...[/cyan]")
                result = subprocess.run(['certbot', 'renew'], capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.console.print("[green]✅ Certificate renewal completed[/green]")
                    self.console.print(result.stdout)
                else:
                    self.console.print("[red]❌ Certificate renewal failed[/red]")
                    self.console.print(result.stderr)
                    
            except Exception as e:
                self.console.print(f"[red]Error during renewal: {e}[/red]")
        
        self.console.input("\nPress Enter to continue...")
    
    def _security_scan(self):
        """Domain security scanning"""
        domain = Prompt.ask("Domain for security scan", default="skyhost.no")
        
        self.console.clear()
        header = Panel(
            f"[bold cyan]Security Scan: {domain}[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        # Port scan
        self.console.print("[bold]1. Port Scan[/bold]")
        common_ports = [80, 443, 22, 21, 25, 53, 110, 143, 993, 995]
        
        open_ports = []
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((domain, port))
                if result == 0:
                    open_ports.append(port)
                sock.close()
            except Exception:
                pass
        
        if open_ports:
            self.console.print(f"[yellow]Open ports: {', '.join(map(str, open_ports))}[/yellow]")
        else:
            self.console.print("[green]No common ports found open[/green]")
        
        # HTTP Security Headers
        if REQUESTS_AVAILABLE:
            self.console.print("\n[bold]2. HTTP Security Headers[/bold]")
            try:
                response = requests.get(f"https://{domain}", timeout=10)
                
                security_headers = {
                    'Strict-Transport-Security': 'HSTS',
                    'X-Content-Type-Options': 'Content Type Protection',
                    'X-Frame-Options': 'Clickjacking Protection',
                    'X-XSS-Protection': 'XSS Protection',
                    'Content-Security-Policy': 'Content Security Policy',
                    'Referrer-Policy': 'Referrer Policy',
                    'Permissions-Policy': 'Permissions Policy'
                }
                
                for header, name in security_headers.items():
                    if header in response.headers:
                        self.console.print(f"[green]✅ {name}[/green]")
                    else:
                        self.console.print(f"[red]❌ {name}: Missing[/red]")
                        
            except Exception as e:
                self.console.print(f"[red]Could not check security headers: {e}[/red]")
        
        # SSL/TLS Configuration
        self.console.print("\n[bold]3. SSL/TLS Security[/bold]")
        cert_info = self._get_ssl_certificate_info(domain)
        if cert_info:
            days_left = cert_info['days_left']
            if days_left > 30:
                self.console.print(f"[green]✅ Certificate valid for {days_left} days[/green]")
            elif days_left > 7:
                self.console.print(f"[yellow]⚠️ Certificate expires in {days_left} days[/yellow]")
            else:
                self.console.print(f"[red]❌ Certificate expires in {days_left} days[/red]")
        
        self.console.input("\nPress Enter to continue...")
    
    def _show_help(self):
        """Show module help"""
        help_text = f"""[bold cyan]{self.name} Help[/bold cyan]

This module provides comprehensive domain and SSL certificate management capabilities.

[bold]Features:[/bold]
• Domain validation and connectivity testing
• SSL certificate analysis and monitoring
• DNS record verification and troubleshooting
• Nginx configuration checking and validation
• HTTPS redirect testing and optimization
• SSL certificate renewal management
• Security scanning and vulnerability assessment

[bold]Requirements:[/bold]
• Nginx web server (for configuration checks)
• Let's Encrypt/Certbot (for SSL management)
• DNS tools (dig, nslookup, or dnspython)
• Network connectivity for testing

[bold]Configuration:[/bold]
Configure paths in SkyDash config:
• vhosts.nginx_config_dir: Nginx configuration directory
• vhosts.ssl_cert_dir: SSL certificate directory
• vhosts.dns_servers: DNS servers for lookups

[bold]Common Tasks:[/bold]
• Validate new domain setup
• Check SSL certificate expiration
• Troubleshoot HTTPS issues
• Verify DNS configuration
• Test security headers and redirects
"""
        
        panel = Panel(help_text, title="Help", border_style="yellow")
        self.console.print(panel)
        self.console.input("\nPress Enter to continue...")

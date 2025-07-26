"""
System Health Module for SkyDash Terminal Admin
Real-time monitoring of system resources and services
"""

import os
import time
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich import box

# Try to import psutil for system monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class SystemHealth:
    """
    System Health monitoring module
    Provides real-time system metrics and service status
    """
    
    def __init__(self):
        self.name = "System Health Monitor"
        self.version = "1.0.0"
        self.description = "Monitor CPU, RAM, disk usage, services, and system health"
        self.refresh_interval = 2  # seconds
        self.monitoring = False
    
    def run(self, console: Console, logger, config):
        """Main module entry point"""
        self.console = console
        self.logger = logger
        self.config = config
        
        self.logger.log_action(f"Started {self.name} module", module="system_health")
        
        try:
            self._show_main_menu()
        except KeyboardInterrupt:
            self.console.print("\n[yellow]System Health module interrupted by user[/yellow]")
        except Exception as e:
            self.logger.log_error(str(e), module="system_health")
            self.console.print(f"[red]Module error: {e}[/red]")
        finally:
            self.logger.log_action(f"Exited {self.name} module", module="system_health")
    
    def _show_main_menu(self):
        """Display main module menu"""
        while True:
            self.console.clear()
            
            # Module header
            header = Panel(
                f"[bold cyan]{self.name}[/bold cyan]\n{self.description}",
                title="System Health Monitor",
                border_style="green"
            )
            self.console.print(header)
            self.console.print()
            
            # Quick system overview
            self._show_quick_overview()
            
            # Menu options
            menu = Panel(
                """[bold cyan](1)[/bold cyan] Real-time System Monitor
[bold cyan](2)[/bold cyan] Detailed System Information
[bold cyan](3)[/bold cyan] Service Status Check
[bold cyan](4)[/bold cyan] Disk Usage Analysis
[bold cyan](5)[/bold cyan] Network Information
[bold cyan](6)[/bold cyan] Process Monitor

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
                default="1"
            ).upper()
            
            if choice == "1":
                self._real_time_monitor()
            elif choice == "2":
                self._detailed_system_info()
            elif choice == "3":
                self._service_status()
            elif choice == "4":
                self._disk_analysis()
            elif choice == "5":
                self._network_info()
            elif choice == "6":
                self._process_monitor()
            elif choice == "H":
                self._show_help()
            elif choice == "A":
                break
    
    def _show_quick_overview(self):
        """Show a quick system overview"""
        if not PSUTIL_AVAILABLE:
            self.console.print("[yellow]psutil not available - limited functionality[/yellow]")
            return
        
        try:
            # Get basic metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Create overview table
            table = Table(title="System Overview", box=box.ROUNDED)
            table.add_column("Metric", style="bold")
            table.add_column("Value", justify="right")
            table.add_column("Status", justify="center")
            
            # CPU status
            cpu_status = "🟢" if cpu_percent < 70 else "🟡" if cpu_percent < 90 else "🔴"
            table.add_row("CPU Usage", f"{cpu_percent:.1f}%", cpu_status)
            
            # Memory status
            mem_percent = memory.percent
            mem_status = "🟢" if mem_percent < 70 else "🟡" if mem_percent < 85 else "🔴"
            table.add_row("Memory Usage", f"{mem_percent:.1f}%", mem_status)
            
            # Disk status
            disk_percent = (disk.used / disk.total) * 100
            disk_status = "🟢" if disk_percent < 80 else "🟡" if disk_percent < 95 else "🔴"
            table.add_row("Disk Usage", f"{disk_percent:.1f}%", disk_status)
            
            # System uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            table.add_row("Uptime", str(uptime).split('.')[0], "🟢")
            
            self.console.print(table)
            self.console.print()
            
        except Exception as e:
            self.console.print(f"[red]Error getting system overview: {e}[/red]")
    
    def _real_time_monitor(self):
        """Real-time system monitoring with live updates"""
        if not PSUTIL_AVAILABLE:
            self.console.print("[red]psutil required for real-time monitoring[/red]")
            self.console.input("Press Enter to continue...")
            return
        
        self.console.print("[cyan]Starting real-time monitor... Press Ctrl+C to stop[/cyan]")
        time.sleep(1)
        
        try:
            with Live(self._generate_live_table(), refresh_per_second=1) as live:
                while True:
                    live.update(self._generate_live_table())
                    time.sleep(self.refresh_interval)
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Real-time monitoring stopped[/yellow]")
        
        self.console.input("Press Enter to continue...")
    
    def _generate_live_table(self) -> Table:
        """Generate table for live monitoring"""
        if not PSUTIL_AVAILABLE:
            return Table(title="Monitoring unavailable")
        
        try:
            table = Table(title=f"Live System Monitor - {datetime.now().strftime('%H:%M:%S')}")
            table.add_column("Resource", style="bold")
            table.add_column("Usage", justify="right")
            table.add_column("Details", justify="right")
            table.add_column("Status", justify="center")
            
            # CPU information
            cpu_percent = psutil.cpu_percent(interval=None)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            cpu_status = "🟢" if cpu_percent < 70 else "🟡" if cpu_percent < 90 else "🔴"
            cpu_details = f"{cpu_count} cores"
            if cpu_freq:
                cpu_details += f", {cpu_freq.current:.0f}MHz"
            
            table.add_row("CPU", f"{cpu_percent:.1f}%", cpu_details, cpu_status)
            
            # Memory information
            memory = psutil.virtual_memory()
            mem_status = "🟢" if memory.percent < 70 else "🟡" if memory.percent < 85 else "🔴"
            mem_details = f"{self._bytes_to_gb(memory.used):.1f}/{self._bytes_to_gb(memory.total):.1f} GB"
            
            table.add_row("Memory", f"{memory.percent:.1f}%", mem_details, mem_status)
            
            # Swap information
            swap = psutil.swap_memory()
            if swap.total > 0:
                swap_status = "🟢" if swap.percent < 50 else "🟡" if swap.percent < 80 else "🔴"
                swap_details = f"{self._bytes_to_gb(swap.used):.1f}/{self._bytes_to_gb(swap.total):.1f} GB"
                table.add_row("Swap", f"{swap.percent:.1f}%", swap_details, swap_status)
            
            # Disk information
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_status = "🟢" if disk_percent < 80 else "🟡" if disk_percent < 95 else "🔴"
            disk_details = f"{self._bytes_to_gb(disk.used):.1f}/{self._bytes_to_gb(disk.total):.1f} GB"
            
            table.add_row("Disk (/)", f"{disk_percent:.1f}%", disk_details, disk_status)
            
            # Network I/O
            net_io = psutil.net_io_counters()
            net_details = f"↓{self._bytes_to_mb(net_io.bytes_recv):.0f}MB ↑{self._bytes_to_mb(net_io.bytes_sent):.0f}MB"
            table.add_row("Network I/O", "Total", net_details, "🟢")
            
            # Load average (Linux/Unix)
            try:
                load_avg = os.getloadavg()
                load_status = "🟢" if load_avg[0] < cpu_count else "🟡" if load_avg[0] < cpu_count * 1.5 else "🔴"
                load_details = f"5min: {load_avg[1]:.2f}, 15min: {load_avg[2]:.2f}"
                table.add_row("Load Average", f"{load_avg[0]:.2f}", load_details, load_status)
            except (AttributeError, OSError):
                pass  # Not available on all systems
            
            return table
            
        except Exception as e:
            error_table = Table(title="Error")
            error_table.add_column("Error")
            error_table.add_row(f"Failed to get system info: {e}")
            return error_table
    
    def _detailed_system_info(self):
        """Show detailed system information"""
        self.console.clear()
        
        # System info header
        header = Panel(
            "[bold cyan]Detailed System Information[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        if PSUTIL_AVAILABLE:
            self._show_detailed_psutil_info()
        else:
            self._show_basic_system_info()
        
        self.console.input("\nPress Enter to continue...")
    
    def _show_detailed_psutil_info(self):
        """Show detailed system info using psutil"""
        try:
            # CPU information
            cpu_table = Table(title="CPU Information", box=box.ROUNDED)
            cpu_table.add_column("Property", style="bold")
            cpu_table.add_column("Value")
            
            cpu_table.add_row("Physical cores", str(psutil.cpu_count(logical=False)))
            cpu_table.add_row("Total cores", str(psutil.cpu_count(logical=True)))
            
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                cpu_table.add_row("Max Frequency", f"{cpu_freq.max:.2f}MHz")
                cpu_table.add_row("Min Frequency", f"{cpu_freq.min:.2f}MHz")
                cpu_table.add_row("Current Frequency", f"{cpu_freq.current:.2f}MHz")
            
            # Per-core usage
            cpu_percent_per_core = psutil.cpu_percent(percpu=True, interval=1)
            for i, percent in enumerate(cpu_percent_per_core):
                cpu_table.add_row(f"Core {i}", f"{percent}%")
            
            self.console.print(cpu_table)
            self.console.print()
            
            # Memory information
            memory = psutil.virtual_memory()
            mem_table = Table(title="Memory Information", box=box.ROUNDED)
            mem_table.add_column("Property", style="bold")
            mem_table.add_column("Value")
            
            mem_table.add_row("Total", f"{self._bytes_to_gb(memory.total):.2f} GB")
            mem_table.add_row("Available", f"{self._bytes_to_gb(memory.available):.2f} GB")
            mem_table.add_row("Used", f"{self._bytes_to_gb(memory.used):.2f} GB")
            mem_table.add_row("Percentage", f"{memory.percent}%")
            
            self.console.print(mem_table)
            self.console.print()
            
            # Boot time
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            misc_table = Table(title="System Information", box=box.ROUNDED)
            misc_table.add_column("Property", style="bold")
            misc_table.add_column("Value")
            
            misc_table.add_row("Boot time", boot_time.strftime("%Y-%m-%d %H:%M:%S"))
            misc_table.add_row("Uptime", str(uptime).split('.')[0])
            
            self.console.print(misc_table)
            
        except Exception as e:
            self.console.print(f"[red]Error getting detailed system info: {e}[/red]")
    
    def _show_basic_system_info(self):
        """Show basic system info without psutil"""
        try:
            # Try to get info using system commands
            self.console.print("[yellow]Using basic system commands (psutil not available)[/yellow]")
            self.console.print()
            
            # Uptime
            result = subprocess.run(['uptime'], capture_output=True, text=True)
            if result.returncode == 0:
                self.console.print(f"[cyan]Uptime:[/cyan] {result.stdout.strip()}")
            
            # Memory info
            result = subprocess.run(['free', '-h'], capture_output=True, text=True)
            if result.returncode == 0:
                self.console.print(f"[cyan]Memory:[/cyan]")
                self.console.print(result.stdout)
            
            # Disk usage
            result = subprocess.run(['df', '-h'], capture_output=True, text=True)
            if result.returncode == 0:
                self.console.print(f"[cyan]Disk Usage:[/cyan]")
                self.console.print(result.stdout)
            
        except Exception as e:
            self.console.print(f"[red]Error getting basic system info: {e}[/red]")
    
    def _service_status(self):
        """Check status of important services"""
        self.console.clear()
        
        header = Panel(
            "[bold cyan]Service Status Check[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        # Common services to check
        services = [
            "nginx", "apache2", "docker", "ssh", "sshd",
            "postgresql", "mysql", "redis", "fail2ban"
        ]
        
        table = Table(title="Service Status", box=box.ROUNDED)
        table.add_column("Service", style="bold")
        table.add_column("Status", justify="center")
        table.add_column("Details")
        
        for service in services:
            status, details = self._check_service_status(service)
            status_icon = "🟢" if status == "active" else "🔴" if status == "failed" else "⚫"
            table.add_row(service, status_icon, f"{status} - {details}")
        
        self.console.print(table)
        self.console.input("\nPress Enter to continue...")
    
    def _check_service_status(self, service_name: str) -> tuple:
        """Check status of a specific service"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            status = result.stdout.strip()
            
            # Get more details
            result_detail = subprocess.run(
                ['systemctl', 'status', service_name, '--no-pager', '-l'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Extract useful info from status
            lines = result_detail.stdout.split('\n')
            details = "Unknown"
            for line in lines:
                if 'Active:' in line:
                    details = line.split('Active:')[1].strip()
                    break
            
            return status, details
            
        except subprocess.TimeoutExpired:
            return "timeout", "Service check timed out"
        except Exception as e:
            return "error", f"Error checking service: {str(e)}"
    
    def _disk_analysis(self):
        """Analyze disk usage"""
        self.console.clear()
        
        header = Panel(
            "[bold cyan]Disk Usage Analysis[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        if PSUTIL_AVAILABLE:
            self._show_detailed_disk_info()
        else:
            self._show_basic_disk_info()
        
        self.console.input("\nPress Enter to continue...")
    
    def _show_detailed_disk_info(self):
        """Show detailed disk information using psutil"""
        try:
            # Disk partitions
            partitions = psutil.disk_partitions()
            
            table = Table(title="Disk Partitions", box=box.ROUNDED)
            table.add_column("Device", style="bold")
            table.add_column("Mountpoint")
            table.add_column("File System")
            table.add_column("Size")
            table.add_column("Used")
            table.add_column("Free")
            table.add_column("Usage %")
            table.add_column("Status")
            
            for partition in partitions:
                try:
                    partition_usage = psutil.disk_usage(partition.mountpoint)
                    
                    size_gb = self._bytes_to_gb(partition_usage.total)
                    used_gb = self._bytes_to_gb(partition_usage.used)
                    free_gb = self._bytes_to_gb(partition_usage.free)
                    usage_percent = (partition_usage.used / partition_usage.total) * 100
                    
                    status = "🟢" if usage_percent < 80 else "🟡" if usage_percent < 95 else "🔴"
                    
                    table.add_row(
                        partition.device,
                        partition.mountpoint,
                        partition.fstype,
                        f"{size_gb:.1f} GB",
                        f"{used_gb:.1f} GB",
                        f"{free_gb:.1f} GB",
                        f"{usage_percent:.1f}%",
                        status
                    )
                    
                except PermissionError:
                    table.add_row(
                        partition.device,
                        partition.mountpoint,
                        partition.fstype,
                        "Access denied",
                        "", "", "", "⚫"
                    )
            
            self.console.print(table)
            
        except Exception as e:
            self.console.print(f"[red]Error getting disk info: {e}[/red]")
    
    def _show_basic_disk_info(self):
        """Show basic disk info using df command"""
        try:
            result = subprocess.run(['df', '-h'], capture_output=True, text=True)
            if result.returncode == 0:
                self.console.print("Disk Usage:")
                self.console.print(result.stdout)
            else:
                self.console.print("[red]Failed to get disk information[/red]")
        except Exception as e:
            self.console.print(f"[red]Error running df command: {e}[/red]")
    
    def _network_info(self):
        """Show network information"""
        self.console.clear()
        
        header = Panel(
            "[bold cyan]Network Information[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        if PSUTIL_AVAILABLE:
            self._show_detailed_network_info()
        else:
            self._show_basic_network_info()
        
        self.console.input("\nPress Enter to continue...")
    
    def _show_detailed_network_info(self):
        """Show detailed network info using psutil"""
        try:
            # Network interfaces
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            
            table = Table(title="Network Interfaces", box=box.ROUNDED)
            table.add_column("Interface", style="bold")
            table.add_column("IP Address")
            table.add_column("Status")
            table.add_column("Speed")
            
            for interface_name, interface_addresses in net_if_addrs.items():
                for address in interface_addresses:
                    if str(address.family) == 'AddressFamily.AF_INET':
                        ip_address = address.address
                        
                        # Get interface stats
                        if interface_name in net_if_stats:
                            stats = net_if_stats[interface_name]
                            status = "🟢 Up" if stats.isup else "🔴 Down"
                            speed = f"{stats.speed} Mbps" if stats.speed > 0 else "Unknown"
                        else:
                            status = "Unknown"
                            speed = "Unknown"
                        
                        table.add_row(interface_name, ip_address, status, speed)
                        break
            
            self.console.print(table)
            self.console.print()
            
            # Network I/O statistics
            net_io = psutil.net_io_counters()
            
            io_table = Table(title="Network I/O Statistics", box=box.ROUNDED)
            io_table.add_column("Metric", style="bold")
            io_table.add_column("Value")
            
            io_table.add_row("Bytes Sent", f"{self._bytes_to_mb(net_io.bytes_sent):.2f} MB")
            io_table.add_row("Bytes Received", f"{self._bytes_to_mb(net_io.bytes_recv):.2f} MB")
            io_table.add_row("Packets Sent", str(net_io.packets_sent))
            io_table.add_row("Packets Received", str(net_io.packets_recv))
            io_table.add_row("Errors In", str(net_io.errin))
            io_table.add_row("Errors Out", str(net_io.errout))
            io_table.add_row("Dropped In", str(net_io.dropin))
            io_table.add_row("Dropped Out", str(net_io.dropout))
            
            self.console.print(io_table)
            
        except Exception as e:
            self.console.print(f"[red]Error getting network info: {e}[/red]")
    
    def _show_basic_network_info(self):
        """Show basic network info using system commands"""
        try:
            # Try ip command first, then ifconfig
            result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True)
            if result.returncode == 0:
                self.console.print("Network Interfaces (ip addr):")
                self.console.print(result.stdout)
            else:
                result = subprocess.run(['ifconfig'], capture_output=True, text=True)
                if result.returncode == 0:
                    self.console.print("Network Interfaces (ifconfig):")
                    self.console.print(result.stdout)
                else:
                    self.console.print("[red]Failed to get network information[/red]")
            
        except Exception as e:
            self.console.print(f"[red]Error getting network info: {e}[/red]")
    
    def _process_monitor(self):
        """Show running processes"""
        if not PSUTIL_AVAILABLE:
            self.console.print("[red]psutil required for process monitoring[/red]")
            self.console.input("Press Enter to continue...")
            return
        
        self.console.clear()
        
        header = Panel(
            "[bold cyan]Process Monitor[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        try:
            # Get processes sorted by CPU usage
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # Sort by CPU usage
            processes = sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            # Display top 20 processes
            table = Table(title="Top Processes (by CPU usage)", box=box.ROUNDED)
            table.add_column("PID", justify="right")
            table.add_column("Name", style="bold")
            table.add_column("User")
            table.add_column("CPU %", justify="right")
            table.add_column("Memory %", justify="right")
            
            for proc in processes[:20]:
                cpu_percent = proc['cpu_percent'] or 0
                mem_percent = proc['memory_percent'] or 0
                
                table.add_row(
                    str(proc['pid']),
                    proc['name'] or 'Unknown',
                    proc['username'] or 'Unknown',
                    f"{cpu_percent:.1f}%",
                    f"{mem_percent:.1f}%"
                )
            
            self.console.print(table)
            
        except Exception as e:
            self.console.print(f"[red]Error getting process info: {e}[/red]")
        
        self.console.input("\nPress Enter to continue...")
    
    def _show_help(self):
        """Show module help"""
        help_text = f"""[bold cyan]{self.name} Help[/bold cyan]

This module provides comprehensive system monitoring and health checking capabilities.

[bold]Available Options:[/bold]
• Real-time Monitor: Live updating system resource usage
• Detailed System Info: Complete system specifications and status
• Service Status: Check status of important system services
• Disk Analysis: Detailed disk usage and partition information
• Network Information: Network interfaces and traffic statistics
• Process Monitor: View running processes and resource usage

[bold]Usage Tips:[/bold]
• Real-time monitor updates every {self.refresh_interval} seconds
• Press Ctrl+C to exit real-time monitoring
• Service checks include common services like nginx, docker, ssh
• Disk analysis shows usage warnings at 80% and 95% capacity

[bold]Requirements:[/bold]
• psutil library recommended for full functionality
• systemctl access needed for service status
• Some features require root/sudo access

[bold]Status Indicators:[/bold]
• 🟢 Good/Normal (CPU <70%, Memory <70%, Disk <80%)
• 🟡 Warning (CPU 70-90%, Memory 70-85%, Disk 80-95%)
• 🔴 Critical (CPU >90%, Memory >85%, Disk >95%)
• ⚫ Unknown/Unavailable
"""
        
        panel = Panel(help_text, title="Help", border_style="yellow")
        self.console.print(panel)
        self.console.input("\nPress Enter to continue...")
    
    def _bytes_to_gb(self, bytes_value: int) -> float:
        """Convert bytes to gigabytes"""
        return bytes_value / (1024 ** 3)
    
    def _bytes_to_mb(self, bytes_value: int) -> float:
        """Convert bytes to megabytes"""
        return bytes_value / (1024 ** 2)

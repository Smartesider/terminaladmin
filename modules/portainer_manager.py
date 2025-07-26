"""
Portainer Manager Module for SkyDash Terminal Admin
Docker container management via Portainer API
"""

import json
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich import box

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

class PortainerManager:
    """
    Portainer and Docker container management module
    """
    
    def __init__(self):
        self.name = "Portainer & Containers"
        self.version = "1.0.0"
        self.description = "Monitor Docker containers via Portainer API, resource monitoring"
        self.portainer_url = "http://localhost:9000"
        self.api_token = None
        self.docker_client = None
    
    def run(self, console: Console, logger, config):
        """Main module entry point"""
        self.console = console
        self.logger = logger
        self.config = config
        
        # Get Portainer configuration
        self.portainer_config = config.get_module_config("portainer")
        self.portainer_url = self.portainer_config.get("api_url", "http://localhost:9000/api")
        self.api_token = self.portainer_config.get("api_token", "")
        
        # Initialize Docker client
        if DOCKER_AVAILABLE:
            try:
                self.docker_client = docker.from_env()
            except Exception as e:
                self.console.print(f"[yellow]Warning: Could not connect to Docker: {e}[/yellow]")
        
        self.logger.log_action(f"Started {self.name} module", module="portainer_manager")
        
        try:
            self._show_main_menu()
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Portainer module interrupted by user[/yellow]")
        except Exception as e:
            self.logger.log_error(str(e), module="portainer_manager")
            self.console.print(f"[red]Module error: {e}[/red]")
        finally:
            self.logger.log_action(f"Exited {self.name} module", module="portainer_manager")
    
    def _show_main_menu(self):
        """Display main module menu"""
        while True:
            self.console.clear()
            
            # Module header
            header = Panel(
                f"[bold cyan]{self.name}[/bold cyan]\n{self.description}",
                title="🐳 Container Management",
                border_style="blue"
            )
            self.console.print(header)
            self.console.print()
            
            # Quick container overview
            self._show_container_overview()
            
            # Menu options
            menu = Panel(
                """[bold cyan](1)[/bold cyan] Container Status & Management
[bold cyan](2)[/bold cyan] Real-time Container Monitoring
[bold cyan](3)[/bold cyan] Docker Images Management
[bold cyan](4)[/bold cyan] Docker Networks & Volumes
[bold cyan](5)[/bold cyan] Container Logs Viewer
[bold cyan](6)[/bold cyan] Portainer API Status
[bold cyan](7)[/bold cyan] Docker System Information

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
                self._container_management()
            elif choice == "2":
                self._real_time_monitoring()
            elif choice == "3":
                self._image_management()
            elif choice == "4":
                self._networks_volumes()
            elif choice == "5":
                self._container_logs()
            elif choice == "6":
                self._portainer_status()
            elif choice == "7":
                self._docker_system_info()
            elif choice == "H":
                self._show_help()
            elif choice == "A":
                break
    
    def _show_container_overview(self):
        """Show quick container overview"""
        if not DOCKER_AVAILABLE:
            self.console.print("[yellow]Docker Python client not available - using command line[/yellow]")
            self._show_container_overview_cli()
            return
        
        try:
            containers = self.docker_client.containers.list(all=True)
            
            table = Table(title="Container Overview", box=box.ROUNDED)
            table.add_column("Name", style="bold")
            table.add_column("Status", justify="center")
            table.add_column("Image")
            table.add_column("Ports")
            
            for container in containers[:10]:  # Show first 10
                status_color = "green" if container.status == "running" else "red" if container.status == "exited" else "yellow"
                status_icon = "🟢" if container.status == "running" else "🔴" if container.status == "exited" else "🟡"
                
                # Get port mappings
                ports = []
                if container.ports:
                    for port, bindings in container.ports.items():
                        if bindings:
                            for binding in bindings:
                                ports.append(f"{binding['HostPort']}:{port}")
                
                table.add_row(
                    container.name,
                    f"[{status_color}]{status_icon}[/{status_color}] {container.status}",
                    container.image.tags[0] if container.image.tags else container.image.id[:12],
                    ", ".join(ports) if ports else "None"
                )
            
            if len(containers) > 10:
                table.add_row("...", f"and {len(containers) - 10} more", "", "")
            
            self.console.print(table)
            
        except Exception as e:
            self.console.print(f"[red]Error getting container overview: {e}[/red]")
            self._show_container_overview_cli()
        
        self.console.print()
    
    def _show_container_overview_cli(self):
        """Show container overview using CLI"""
        try:
            result = subprocess.run(
                ['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.console.print("[bold]Running Containers:[/bold]")
                self.console.print(result.stdout)
            else:
                self.console.print("[red]Unable to get container information[/red]")
                
        except Exception as e:
            self.console.print(f"[red]Error running docker command: {e}[/red]")
    
    def _container_management(self):
        """Container management interface"""
        while True:
            self.console.clear()
            
            header = Panel(
                "[bold cyan]Container Management[/bold cyan]",
                border_style="cyan"
            )
            self.console.print(header)
            self.console.print()
            
            # List all containers
            self._list_all_containers()
            
            menu = Panel(
                """[bold cyan](1)[/bold cyan] Start Container
[bold cyan](2)[/bold cyan] Stop Container
[bold cyan](3)[/bold cyan] Restart Container
[bold cyan](4)[/bold cyan] Remove Container
[bold cyan](5)[/bold cyan] Container Details
[bold cyan](6)[/bold cyan] Container Stats

[bold red](B)[/bold red] Back""",
                title="Container Actions",
                border_style="blue"
            )
            self.console.print(menu)
            
            choice = Prompt.ask(
                "[bold green]Select action[/bold green]",
                choices=["1", "2", "3", "4", "5", "6", "B"],
                default="5"
            ).upper()
            
            if choice == "1":
                self._start_container()
            elif choice == "2":
                self._stop_container()
            elif choice == "3":
                self._restart_container()
            elif choice == "4":
                self._remove_container()
            elif choice == "5":
                self._container_details()
            elif choice == "6":
                self._container_stats()
            elif choice == "B":
                break
    
    def _list_all_containers(self):
        """List all containers with detailed info"""
        if DOCKER_AVAILABLE and self.docker_client:
            try:
                containers = self.docker_client.containers.list(all=True)
                
                table = Table(title="All Containers", box=box.ROUNDED)
                table.add_column("#", style="dim")
                table.add_column("Name", style="bold")
                table.add_column("Status", justify="center")
                table.add_column("Image")
                table.add_column("Created")
                table.add_column("CPU/Memory")
                
                for i, container in enumerate(containers, 1):
                    status_color = "green" if container.status == "running" else "red"
                    status_icon = "🟢" if container.status == "running" else "🔴"
                    
                    # Get basic stats if running
                    cpu_mem = "N/A"
                    if container.status == "running":
                        try:
                            stats = container.stats(stream=False)
                            # Calculate CPU percentage (simplified)
                            cpu_percent = 0.0
                            if 'cpu_stats' in stats and 'precpu_stats' in stats:
                                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                                system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                                if system_delta > 0:
                                    cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
                            
                            # Memory usage
                            memory_usage = stats['memory_stats'].get('usage', 0)
                            memory_limit = stats['memory_stats'].get('limit', 0)
                            if memory_limit > 0:
                                memory_percent = (memory_usage / memory_limit) * 100
                                cpu_mem = f"{cpu_percent:.1f}% / {memory_percent:.1f}%"
                        except:
                            cpu_mem = "Running"
                    
                    created = container.attrs['Created'][:19].replace('T', ' ')
                    
                    table.add_row(
                        str(i),
                        container.name,
                        f"[{status_color}]{status_icon}[/{status_color}] {container.status}",
                        container.image.tags[0] if container.image.tags else container.image.id[:12],
                        created,
                        cpu_mem
                    )
                
                self.console.print(table)
                
            except Exception as e:
                self.console.print(f"[red]Error listing containers: {e}[/red]")
        else:
            self._list_containers_cli()
        
        self.console.print()
    
    def _list_containers_cli(self):
        """List containers using CLI"""
        try:
            result = subprocess.run(
                ['docker', 'ps', '-a', '--format', 'table {{.Names}}\t{{.Status}}\t{{.Image}}\t{{.CreatedAt}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.console.print(result.stdout)
            else:
                self.console.print("[red]Unable to list containers[/red]")
                
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
    
    def _start_container(self):
        """Start a container"""
        container_name = Prompt.ask("Container name to start")
        
        try:
            if DOCKER_AVAILABLE and self.docker_client:
                container = self.docker_client.containers.get(container_name)
                container.start()
            else:
                result = subprocess.run(['docker', 'start', container_name], capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(result.stderr)
            
            self.console.print(f"[green]✅ Container '{container_name}' started successfully[/green]")
            self.logger.log_action(f"Started container: {container_name}", module="portainer_manager")
            
        except Exception as e:
            self.console.print(f"[red]❌ Failed to start container: {e}[/red]")
            self.logger.log_error(f"Failed to start container {container_name}: {e}", module="portainer_manager")
        
        self.console.input("\nPress Enter to continue...")
    
    def _stop_container(self):
        """Stop a container"""
        container_name = Prompt.ask("Container name to stop")
        
        if Confirm.ask(f"Stop container '{container_name}'?"):
            try:
                if DOCKER_AVAILABLE and self.docker_client:
                    container = self.docker_client.containers.get(container_name)
                    container.stop()
                else:
                    result = subprocess.run(['docker', 'stop', container_name], capture_output=True, text=True)
                    if result.returncode != 0:
                        raise Exception(result.stderr)
                
                self.console.print(f"[green]✅ Container '{container_name}' stopped successfully[/green]")
                self.logger.log_action(f"Stopped container: {container_name}", module="portainer_manager")
                
            except Exception as e:
                self.console.print(f"[red]❌ Failed to stop container: {e}[/red]")
                self.logger.log_error(f"Failed to stop container {container_name}: {e}", module="portainer_manager")
        
        self.console.input("\nPress Enter to continue...")
    
    def _restart_container(self):
        """Restart a container"""
        container_name = Prompt.ask("Container name to restart")
        
        if Confirm.ask(f"Restart container '{container_name}'?"):
            try:
                if DOCKER_AVAILABLE and self.docker_client:
                    container = self.docker_client.containers.get(container_name)
                    container.restart()
                else:
                    result = subprocess.run(['docker', 'restart', container_name], capture_output=True, text=True)
                    if result.returncode != 0:
                        raise Exception(result.stderr)
                
                self.console.print(f"[green]✅ Container '{container_name}' restarted successfully[/green]")
                self.logger.log_action(f"Restarted container: {container_name}", module="portainer_manager")
                
            except Exception as e:
                self.console.print(f"[red]❌ Failed to restart container: {e}[/red]")
                self.logger.log_error(f"Failed to restart container {container_name}: {e}", module="portainer_manager")
        
        self.console.input("\nPress Enter to continue...")
    
    def _remove_container(self):
        """Remove a container"""
        container_name = Prompt.ask("Container name to remove")
        
        force = Confirm.ask("Force remove (if running)?", default=False)
        
        if Confirm.ask(f"[red]Permanently remove container '{container_name}'?[/red]"):
            try:
                if DOCKER_AVAILABLE and self.docker_client:
                    container = self.docker_client.containers.get(container_name)
                    container.remove(force=force)
                else:
                    cmd = ['docker', 'rm']
                    if force:
                        cmd.append('-f')
                    cmd.append(container_name)
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        raise Exception(result.stderr)
                
                self.console.print(f"[green]✅ Container '{container_name}' removed successfully[/green]")
                self.logger.log_action(f"Removed container: {container_name}", module="portainer_manager")
                
            except Exception as e:
                self.console.print(f"[red]❌ Failed to remove container: {e}[/red]")
                self.logger.log_error(f"Failed to remove container {container_name}: {e}", module="portainer_manager")
        
        self.console.input("\nPress Enter to continue...")
    
    def _container_details(self):
        """Show detailed container information"""
        container_name = Prompt.ask("Container name for details")
        
        try:
            if DOCKER_AVAILABLE and self.docker_client:
                container = self.docker_client.containers.get(container_name)
                
                # Basic info
                info_table = Table(title=f"Container: {container_name}", box=box.ROUNDED)
                info_table.add_column("Property", style="bold")
                info_table.add_column("Value")
                
                info_table.add_row("ID", container.id[:12])
                info_table.add_row("Status", container.status)
                info_table.add_row("Image", container.image.tags[0] if container.image.tags else container.image.id[:12])
                info_table.add_row("Created", container.attrs['Created'][:19].replace('T', ' '))
                info_table.add_row("Platform", container.attrs.get('Platform', 'Unknown'))
                
                self.console.print(info_table)
                self.console.print()
                
                # Port mappings
                if container.ports:
                    port_table = Table(title="Port Mappings", box=box.ROUNDED)
                    port_table.add_column("Container Port")
                    port_table.add_column("Host Port")
                    port_table.add_column("Protocol")
                    
                    for port, bindings in container.ports.items():
                        if bindings:
                            for binding in bindings:
                                port_table.add_row(
                                    port,
                                    binding.get('HostPort', 'N/A'),
                                    binding.get('HostIp', '0.0.0.0')
                                )
                    
                    self.console.print(port_table)
                
                # Environment variables
                if container.attrs.get('Config', {}).get('Env'):
                    env_table = Table(title="Environment Variables", box=box.ROUNDED)
                    env_table.add_column("Variable", style="bold")
                    env_table.add_column("Value")
                    
                    for env_var in container.attrs['Config']['Env'][:10]:  # Show first 10
                        if '=' in env_var:
                            key, value = env_var.split('=', 1)
                            env_table.add_row(key, value[:50] + "..." if len(value) > 50 else value)
                    
                    self.console.print(env_table)
                
            else:
                # Use CLI
                result = subprocess.run(['docker', 'inspect', container_name], capture_output=True, text=True)
                if result.returncode == 0:
                    self.console.print(f"[bold]Container Details for {container_name}:[/bold]")
                    # Parse and display key information
                    data = json.loads(result.stdout)[0]
                    self.console.print(f"ID: {data['Id'][:12]}")
                    self.console.print(f"Status: {data['State']['Status']}")
                    self.console.print(f"Image: {data['Config']['Image']}")
                    self.console.print(f"Created: {data['Created'][:19]}")
                else:
                    raise Exception(result.stderr)
            
        except Exception as e:
            self.console.print(f"[red]❌ Failed to get container details: {e}[/red]")
        
        self.console.input("\nPress Enter to continue...")
    
    def _container_stats(self):
        """Show container resource statistics"""
        container_name = Prompt.ask("Container name for stats")
        
        try:
            if DOCKER_AVAILABLE and self.docker_client:
                container = self.docker_client.containers.get(container_name)
                
                if container.status != "running":
                    self.console.print(f"[yellow]Container '{container_name}' is not running[/yellow]")
                    self.console.input("\nPress Enter to continue...")
                    return
                
                self.console.print(f"[cyan]Getting stats for {container_name}... Press Ctrl+C to stop[/cyan]")
                
                try:
                    for i in range(10):  # Show 10 iterations
                        stats = container.stats(stream=False)
                        
                        # Calculate CPU percentage
                        cpu_percent = 0.0
                        if 'cpu_stats' in stats and 'precpu_stats' in stats:
                            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                            system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                            if system_delta > 0:
                                cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
                        
                        # Memory usage
                        memory_usage = stats['memory_stats'].get('usage', 0)
                        memory_limit = stats['memory_stats'].get('limit', 0)
                        memory_percent = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
                        
                        # Network I/O
                        net_rx = net_tx = 0
                        if 'networks' in stats:
                            for interface in stats['networks'].values():
                                net_rx += interface.get('rx_bytes', 0)
                                net_tx += interface.get('tx_bytes', 0)
                        
                        self.console.clear()
                        self.console.print(f"[bold]Stats for {container_name} (iteration {i+1}/10):[/bold]")
                        self.console.print(f"CPU: {cpu_percent:.2f}%")
                        self.console.print(f"Memory: {memory_usage / 1024 / 1024:.2f}MB ({memory_percent:.2f}%)")
                        self.console.print(f"Network RX: {net_rx / 1024 / 1024:.2f}MB")
                        self.console.print(f"Network TX: {net_tx / 1024 / 1024:.2f}MB")
                        
                        time.sleep(2)
                        
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Stats monitoring stopped[/yellow]")
                
            else:
                # Use CLI
                self.console.print(f"[cyan]Starting stats for {container_name}... Press Ctrl+C to stop[/cyan]")
                subprocess.run(['docker', 'stats', container_name], timeout=30)
            
        except Exception as e:
            self.console.print(f"[red]❌ Failed to get container stats: {e}[/red]")
        
        self.console.input("\nPress Enter to continue...")
    
    def _real_time_monitoring(self):
        """Real-time container monitoring"""
        self.console.print("[cyan]Starting real-time container monitoring... Press Ctrl+C to stop[/cyan]")
        
        try:
            if DOCKER_AVAILABLE and self.docker_client:
                with Live(self._generate_container_table(), refresh_per_second=1) as live:
                    while True:
                        live.update(self._generate_container_table())
                        time.sleep(2)
            else:
                # Fallback to CLI
                subprocess.run(['docker', 'stats'], timeout=60)
                
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Real-time monitoring stopped[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error in real-time monitoring: {e}[/red]")
        
        self.console.input("\nPress Enter to continue...")
    
    def _generate_container_table(self) -> Table:
        """Generate real-time container table"""
        table = Table(title=f"Container Monitor - {datetime.now().strftime('%H:%M:%S')}")
        table.add_column("Name", style="bold")
        table.add_column("Status", justify="center")
        table.add_column("CPU %", justify="right")
        table.add_column("Memory", justify="right")
        table.add_column("Network I/O", justify="right")
        
        try:
            containers = self.docker_client.containers.list()
            
            for container in containers:
                status_icon = "🟢" if container.status == "running" else "🔴"
                
                try:
                    stats = container.stats(stream=False)
                    
                    # CPU calculation
                    cpu_percent = 0.0
                    if 'cpu_stats' in stats and 'precpu_stats' in stats:
                        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                        system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                        if system_delta > 0:
                            cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
                    
                    # Memory
                    memory_usage = stats['memory_stats'].get('usage', 0)
                    memory_mb = memory_usage / 1024 / 1024
                    
                    # Network
                    net_rx = net_tx = 0
                    if 'networks' in stats:
                        for interface in stats['networks'].values():
                            net_rx += interface.get('rx_bytes', 0)
                            net_tx += interface.get('tx_bytes', 0)
                    
                    table.add_row(
                        container.name,
                        f"{status_icon} {container.status}",
                        f"{cpu_percent:.1f}%",
                        f"{memory_mb:.1f}MB",
                        f"↓{net_rx/1024/1024:.1f}MB ↑{net_tx/1024/1024:.1f}MB"
                    )
                    
                except:
                    table.add_row(
                        container.name,
                        f"{status_icon} {container.status}",
                        "N/A",
                        "N/A",
                        "N/A"
                    )
            
        except Exception:
            table.add_row("Error", "Failed to get container data", "", "", "")
        
        return table
    
    def _image_management(self):
        """Docker image management"""
        self.console.clear()
        
        header = Panel(
            "[bold cyan]Docker Image Management[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        try:
            if DOCKER_AVAILABLE and self.docker_client:
                images = self.docker_client.images.list()
                
                table = Table(title="Docker Images", box=box.ROUNDED)
                table.add_column("Repository", style="bold")
                table.add_column("Tag")
                table.add_column("Image ID")
                table.add_column("Size")
                table.add_column("Created")
                
                for image in images:
                    repo_tags = image.tags[0].split(':') if image.tags else ['<none>', '<none>']
                    repo = repo_tags[0] if len(repo_tags) > 0 else '<none>'
                    tag = repo_tags[1] if len(repo_tags) > 1 else '<none>'
                    
                    size_mb = image.attrs['Size'] / 1024 / 1024
                    created = image.attrs['Created'][:19].replace('T', ' ')
                    
                    table.add_row(
                        repo,
                        tag,
                        image.id[:12],
                        f"{size_mb:.1f}MB",
                        created
                    )
                
                self.console.print(table)
                
            else:
                result = subprocess.run(['docker', 'images'], capture_output=True, text=True)
                if result.returncode == 0:
                    self.console.print(result.stdout)
                else:
                    self.console.print("[red]Unable to list images[/red]")
                    
        except Exception as e:
            self.console.print(f"[red]Error listing images: {e}[/red]")
        
        self.console.input("\nPress Enter to continue...")
    
    def _networks_volumes(self):
        """Docker networks and volumes"""
        self.console.clear()
        
        header = Panel(
            "[bold cyan]Docker Networks & Volumes[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        # Networks
        try:
            result = subprocess.run(['docker', 'network', 'ls'], capture_output=True, text=True)
            if result.returncode == 0:
                self.console.print("[bold]Docker Networks:[/bold]")
                self.console.print(result.stdout)
                self.console.print()
        except Exception as e:
            self.console.print(f"[red]Error listing networks: {e}[/red]")
        
        # Volumes
        try:
            result = subprocess.run(['docker', 'volume', 'ls'], capture_output=True, text=True)
            if result.returncode == 0:
                self.console.print("[bold]Docker Volumes:[/bold]")
                self.console.print(result.stdout)
        except Exception as e:
            self.console.print(f"[red]Error listing volumes: {e}[/red]")
        
        self.console.input("\nPress Enter to continue...")
    
    def _container_logs(self):
        """View container logs"""
        container_name = Prompt.ask("Container name for logs")
        lines = Prompt.ask("Number of lines", default="50")
        
        try:
            if DOCKER_AVAILABLE and self.docker_client:
                container = self.docker_client.containers.get(container_name)
                logs = container.logs(tail=int(lines)).decode('utf-8')
                
                self.console.print(f"[bold]Last {lines} lines from {container_name}:[/bold]")
                self.console.print(logs)
            else:
                result = subprocess.run(['docker', 'logs', '--tail', lines, container_name], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    self.console.print(f"[bold]Last {lines} lines from {container_name}:[/bold]")
                    self.console.print(result.stdout)
                    if result.stderr:
                        self.console.print("[yellow]Stderr:[/yellow]")
                        self.console.print(result.stderr)
                else:
                    raise Exception(result.stderr)
            
        except Exception as e:
            self.console.print(f"[red]❌ Failed to get logs: {e}[/red]")
        
        self.console.input("\nPress Enter to continue...")
    
    def _portainer_status(self):
        """Check Portainer API status"""
        self.console.clear()
        
        header = Panel(
            "[bold cyan]Portainer API Status[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        if not REQUESTS_AVAILABLE:
            self.console.print("[red]Requests library not available for API testing[/red]")
            self.console.input("\nPress Enter to continue...")
            return
        
        try:
            # Test Portainer API
            self.console.print(f"Testing Portainer API at: {self.portainer_url}")
            
            response = requests.get(f"{self.portainer_url}/system/status", timeout=10)
            
            if response.status_code == 200:
                self.console.print("[green]✅ Portainer API is accessible[/green]")
                
                data = response.json()
                self.console.print(f"Version: {data.get('Version', 'Unknown')}")
                self.console.print(f"Edition: {data.get('Edition', 'Unknown')}")
                
                # Test authentication if token is provided
                if self.api_token:
                    headers = {'X-API-Key': self.api_token}
                    auth_response = requests.get(f"{self.portainer_url}/endpoints", 
                                               headers=headers, timeout=10)
                    
                    if auth_response.status_code == 200:
                        self.console.print("[green]✅ API token is valid[/green]")
                        endpoints = auth_response.json()
                        self.console.print(f"Available endpoints: {len(endpoints)}")
                    else:
                        self.console.print("[red]❌ API token is invalid[/red]")
                else:
                    self.console.print("[yellow]No API token configured[/yellow]")
                    
            else:
                self.console.print(f"[red]❌ Portainer API not accessible: {response.status_code}[/red]")
                
        except Exception as e:
            self.console.print(f"[red]❌ Failed to connect to Portainer: {e}[/red]")
        
        self.console.input("\nPress Enter to continue...")
    
    def _docker_system_info(self):
        """Show Docker system information"""
        self.console.clear()
        
        header = Panel(
            "[bold cyan]Docker System Information[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()
        
        try:
            if DOCKER_AVAILABLE and self.docker_client:
                info = self.docker_client.info()
                
                table = Table(title="Docker System Info", box=box.ROUNDED)
                table.add_column("Property", style="bold")
                table.add_column("Value")
                
                table.add_row("Docker Version", info.get('ServerVersion', 'Unknown'))
                table.add_row("Containers", str(info.get('Containers', 0)))
                table.add_row("Running", str(info.get('ContainersRunning', 0)))
                table.add_row("Paused", str(info.get('ContainersPaused', 0)))
                table.add_row("Stopped", str(info.get('ContainersStopped', 0)))
                table.add_row("Images", str(info.get('Images', 0)))
                table.add_row("Storage Driver", info.get('Driver', 'Unknown'))
                table.add_row("Kernel Version", info.get('KernelVersion', 'Unknown'))
                table.add_row("Operating System", info.get('OperatingSystem', 'Unknown'))
                table.add_row("Architecture", info.get('Architecture', 'Unknown'))
                table.add_row("CPUs", str(info.get('NCPU', 0)))
                table.add_row("Memory", f"{info.get('MemTotal', 0) / 1024 / 1024 / 1024:.1f}GB")
                
                self.console.print(table)
                
            else:
                result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
                if result.returncode == 0:
                    self.console.print(result.stdout)
                else:
                    self.console.print("[red]Unable to get Docker info[/red]")
                    
        except Exception as e:
            self.console.print(f"[red]Error getting Docker info: {e}[/red]")
        
        self.console.input("\nPress Enter to continue...")
    
    def _show_help(self):
        """Show module help"""
        help_text = f"""[bold cyan]{self.name} Help[/bold cyan]

This module provides comprehensive Docker container management via Portainer API and direct Docker commands.

[bold]Features:[/bold]
• Container lifecycle management (start, stop, restart, remove)
• Real-time container monitoring and statistics
• Docker image and volume management
• Container log viewing and analysis
• Portainer API integration and status checking
• Docker system information and diagnostics

[bold]Requirements:[/bold]
• Docker installed and running
• Portainer (optional, for API features)
• Python docker library (recommended)
• Network access to containers

[bold]Configuration:[/bold]
Configure Portainer API URL and token in SkyDash config:
• portainer.api_url: Portainer API endpoint
• portainer.api_token: API authentication token

[bold]Troubleshooting:[/bold]
• Ensure Docker daemon is running
• Check user permissions for Docker access
• Verify Portainer is accessible if using API features
• Use CLI fallback if Python libraries unavailable
"""
        
        panel = Panel(help_text, title="Help", border_style="yellow")
        self.console.print(panel)
        self.console.input("\nPress Enter to continue...")

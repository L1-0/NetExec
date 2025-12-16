"""Main dashboard application."""

import os
import sys
import time
import subprocess
from datetime import datetime

from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout


def copy_to_clipboard(text: str) -> bool:
    """Copy text to clipboard using native system tools."""
    try:
        # Check for WSL first
        is_wsl = False
        try:
            with open("/proc/version", "r") as f:
                is_wsl = "microsoft" in f.read().lower() or "wsl" in f.read().lower()
        except (FileNotFoundError, PermissionError):
            pass

        if sys.platform == "win32":
            # Windows - use clip.exe (always available)
            process = subprocess.Popen(["clip"], stdin=subprocess.PIPE, shell=True)
            process.communicate(text.encode("utf-16le"))
            return process.returncode == 0
        elif is_wsl:
            # WSL - use clip.exe from Windows
            try:
                process = subprocess.Popen(
                    ["clip.exe"], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL
                )
                process.communicate(text.encode("utf-8"))
                return process.returncode == 0
            except FileNotFoundError:
                pass
            # Fallback to Linux tools
        elif sys.platform == "darwin":
            # macOS - use pbcopy
            process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            process.communicate(text.encode("utf-8"))
            return process.returncode == 0

        # Linux/Unix - try various clipboard tools
        for cmd in [
            ["xclip", "-selection", "clipboard"],
            ["xsel", "--clipboard", "--input"],
            ["wl-copy"],  # Wayland
        ]:
            try:
                process = subprocess.Popen(
                    cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL
                )
                process.communicate(text.encode("utf-8"))
                if process.returncode == 0:
                    return True
            except FileNotFoundError:
                continue
        return False
    except Exception:
        return False


from nxc.dashboard.db import DashboardDB
from nxc.dashboard.pages import (
    OverviewPage,
    HostsPage,
    CredsPage,
    SharesPage,
    GroupsPage,
    DPAPIPage,
    WCCPage,
    LogsPage,
    PassPolPage,
)
from nxc.dashboard.components.header import Header, Footer, HelpPanel
from nxc.dashboard.components.command_builder import CommandBuilder

# Platform-specific key handling
if sys.platform == "win32":
    import msvcrt

    def get_key():
        """Get a single keypress on Windows."""
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b"\xe0":  # Special key prefix
                key = msvcrt.getch()
                key_map = {
                    b"H": "up",
                    b"P": "down",
                    b"K": "left",
                    b"M": "right",
                }
                return key_map.get(key, "")
            elif key == b"\x00":  # Another special key prefix
                key = msvcrt.getch()
                return ""
            try:
                return key.decode("utf-8")
            except:
                return ""
        return None
else:
    import tty
    import termios
    import select

    # Store terminal settings globally for Unix
    _unix_old_settings = None
    _unix_fd = None

    def _setup_terminal():
        """Set terminal to cbreak mode without echo."""
        global _unix_old_settings, _unix_fd
        _unix_fd = sys.stdin.fileno()
        _unix_old_settings = termios.tcgetattr(_unix_fd)
        # Use cbreak mode (not raw) to preserve output formatting
        tty.setcbreak(_unix_fd)

    def _restore_terminal():
        """Restore terminal to original settings."""
        global _unix_old_settings, _unix_fd
        if _unix_old_settings is not None and _unix_fd is not None:
            termios.tcsetattr(_unix_fd, termios.TCSADRAIN, _unix_old_settings)
            _unix_old_settings = None

    def get_key():
        """Get a single keypress on Unix (handles tmux/WSL/screen)."""
        fd = sys.stdin.fileno()

        rlist, _, _ = select.select([fd], [], [], 0.1)
        if rlist:
            # Use os.read for more reliable reading in WSL
            # Read up to 32 bytes to capture full escape sequences
            data = os.read(fd, 32)
            if not data:
                return None

            # Decode bytes to string
            try:
                key = data.decode("utf-8")
            except UnicodeDecodeError:
                return None

            # Extended key map for various terminal emulators
            key_map = {
                # Standard ANSI (CSI sequences)
                "\x1b[A": "up",
                "\x1b[B": "down",
                "\x1b[C": "right",
                "\x1b[D": "left",
                # Application mode / SS3 sequences (some terminals)
                "\x1bOA": "up",
                "\x1bOB": "down",
                "\x1bOC": "right",
                "\x1bOD": "left",
                # Home/End
                "\x1b[H": "home",
                "\x1b[F": "end",
                "\x1b[1~": "home",
                "\x1b[4~": "end",
                "\x1bOH": "home",
                "\x1bOF": "end",
                # Page Up/Down
                "\x1b[5~": "pageup",
                "\x1b[6~": "pagedown",
                # Delete/Insert
                "\x1b[3~": "delete",
                "\x1b[2~": "insert",
            }

            # Check if it's a known escape sequence
            if key in key_map:
                return key_map[key]

            # Handle single escape key
            if key == "\x1b":
                return "escape"

            # Handle enter key
            if key == "\r" or key == "\n":
                return "\r"

            # Return first character for normal keys
            return key[0] if key else None
        return None


class DashboardApp:
    """Main dashboard application."""

    def __init__(self, args):
        self.workspace = getattr(args, "workspace", "default")
        self.page_size = getattr(args, "page_size", 20)
        self.refresh_interval = getattr(args, "refresh", 0)
        self.log_file = getattr(args, "log_file", None)
        self.unmask = getattr(args, "unmask", False)
        self.start_page = getattr(args, "start_page", 1)

        self.console = Console()
        self.db = DashboardDB(self.workspace)

        # Config for pages
        self.config = {
            "page_size": self.page_size,
            "unmask": self.unmask,
            "log_file": self.log_file,
        }

        # Initialize pages
        # Order: 1=Overview, 2=Hosts, 3=Creds, 4=Groups, 5=Shares, 6=DPAPI, 7=WCC, 8=PassPol, 0=Logs
        self.pages = [
            OverviewPage(self.db, self.config),  # Key 1 (index 0)
            HostsPage(self.db, self.config),  # Key 2 (index 1)
            CredsPage(self.db, self.config),  # Key 3 (index 2)
            GroupsPage(self.db, self.config),  # Key 4 (index 3)
            SharesPage(self.db, self.config),  # Key 5 (index 4)
            DPAPIPage(self.db, self.config),  # Key 6 (index 5)
            WCCPage(self.db, self.config),  # Key 7 (index 6)
            PassPolPage(self.db, self.config),  # Key 8 (index 7)
            LogsPage(self.db, self.config),  # Key 0 (index 8)
        ]

        self.current_page_idx = min(self.start_page - 1, len(self.pages) - 1)
        self.show_help = False
        self.running = True
        self.needs_redraw = True  # Track when to redraw
        self.last_width = 0  # Track terminal width changes

        # Components
        self.header = Header(self.workspace)
        self.footer = Footer()

        # Command builder for host/user selection
        self.command_builder = CommandBuilder()
        self.generated_command = None
        self.show_command_result = False  # Show command result panel
        self.execute_command = None  # Command to execute after exit

        # Load domains for header
        self._update_domains()

    @property
    def current_page(self):
        """Get current page object."""
        return self.pages[self.current_page_idx]

    @property
    def hosts_page(self):
        """Get the hosts page."""
        return self.pages[1]  # Index 1 = HostsPage

    @property
    def creds_page(self):
        """Get the creds page."""
        return self.pages[2]  # Index 2 = CredsPage

    def _update_domains(self):
        """Update domains from database for header display."""
        domains = self.db.get_unique_domains()
        self.header.set_domains(domains)

    def _cancel_selection(self):
        """Cancel any active selection mode."""
        self.command_builder.reset()
        self.hosts_page.exit_selection_mode()
        self.creds_page.exit_selection_mode()
        self.generated_command = None
        self.show_command_result = False

    def handle_input(self, key: str) -> bool:
        """Handle keyboard input. Returns False to quit."""
        if key is None:
            return True

        # Handle command result panel
        if self.show_command_result and self.generated_command:
            if key == "c":
                # Copy to clipboard
                if copy_to_clipboard(self.generated_command):
                    self.generated_command = None
                    self.show_command_result = False
                    self.needs_redraw = True
                return True
            elif key == "x" or key == "\r":
                # Execute - close dashboard and return command
                self.execute_command = self.generated_command
                return False  # Exit dashboard
            elif key == "q" or key == "escape":
                # Cancel
                self.generated_command = None
                self.show_command_result = False
                self.needs_redraw = True
                return True
            return True

        # Handle protocol selection popup
        if self.command_builder.needs_protocol_selection:
            if key == "q":
                self._cancel_selection()
                self.needs_redraw = True
                return True
            if self.command_builder.handle_protocol_key(key):
                # Protocol selected, generate command and show result panel
                self.generated_command = self.command_builder.build_command()
                self.show_command_result = True
                # Reset selection state but keep the generated command
                self.command_builder.reset()
                self.hosts_page.exit_selection_mode()
                self.creds_page.exit_selection_mode()
            self.needs_redraw = True
            return True

        # Handle selection mode
        if self.command_builder.is_active:
            if key == "q":
                self._cancel_selection()
                self.needs_redraw = True
                return True

            # Pass key to current page
            result = self.current_page.handle_key(key, self.console)
            if result == "selected":
                # Selection made
                if self.command_builder.state == "select_host":
                    host = self.hosts_page.get_selected_host()
                    if host:
                        self.command_builder.set_host(host)
                        self.hosts_page.exit_selection_mode()
                        # Now select credential
                        if self.command_builder.state == "select_user":
                            self.current_page_idx = 2  # Switch to creds page (index 2)
                            self.creds_page.enter_selection_mode("Select Credential")
                        elif self.command_builder.state == "select_protocol":
                            pass  # Will show protocol popup
                elif self.command_builder.state == "select_user":
                    # Get credential from creds page
                    if self.current_page_idx == 2:  # Creds page
                        user_data = self.creds_page.get_selected_cred()
                        self.creds_page.exit_selection_mode()

                        if user_data:
                            self.command_builder.set_user(user_data)
                            # Now select host or protocol
                            if self.command_builder.state == "select_host":
                                self.current_page_idx = (
                                    1  # Switch to hosts page (index 1)
                                )
                                self.hosts_page.enter_selection_mode("Select Host")
                            elif self.command_builder.state == "select_protocol":
                                pass  # Will show protocol popup
            elif result:
                pass  # Normal navigation within page

            self.needs_redraw = True
            return True

        # Global shortcuts
        if key == "q":
            return False
        elif key == "?":
            self.show_help = not self.show_help
            self.needs_redraw = True
            return True
        elif key == "r":
            # Refresh - trigger redraw and update domains
            self._update_domains()
            self.needs_redraw = True
            return True
        elif key in "123456789":
            # Map keys to page indices: 1-9 -> 0-8
            page_num = int(key) - 1
            if page_num < len(self.pages):
                self.current_page_idx = page_num
                self.show_help = False
                self.needs_redraw = True
            return True
        elif key == "\t" or key == "l" or key == "right":
            # Tab/l/Right arrow - next page
            self.current_page_idx = (self.current_page_idx + 1) % len(self.pages)
            self.show_help = False
            self.needs_redraw = True
            return True
        elif key == "h" or key == "left":
            # h/Left arrow - previous page
            self.current_page_idx = (self.current_page_idx - 1) % len(self.pages)
            self.show_help = False
            self.needs_redraw = True
            return True
        elif key == "\r":
            # Enter key - start selection mode on hosts or creds page
            if self.current_page_idx == 1:  # Hosts page (index 1)
                self.command_builder.start_selection("hosts")
                self.hosts_page.enter_selection_mode("Select Host")
                self.needs_redraw = True
                return True
            elif self.current_page_idx == 2:  # Creds page (index 2)
                self.command_builder.start_selection("users")
                self.creds_page.enter_selection_mode("Select Credential")
                self.needs_redraw = True
                return True
        elif key in ("up", "down"):
            # Up/Down arrow - enter selection mode on hosts or creds page
            if self.current_page_idx == 1:  # Hosts page
                result = self.hosts_page.handle_key(key, self.console)
                if result == "enter_selection":
                    self.command_builder.start_selection("hosts")
                    self.hosts_page.enter_selection_mode("Select Host")
                self.needs_redraw = True
                return True
            elif self.current_page_idx == 2:  # Creds page
                result = self.creds_page.handle_key(key, self.console)
                if result == "enter_selection":
                    self.command_builder.start_selection("users")
                    self.creds_page.enter_selection_mode("Select Credential")
                self.needs_redraw = True
                return True

        # Pass to current page if help not shown
        if not self.show_help:
            if self.current_page.handle_key(key, self.console):
                self.needs_redraw = True

        return True

    def draw(self):
        """Draw the dashboard to screen."""
        # Get current terminal size
        width = self.console.size.width

        # Check if terminal was resized
        if width != self.last_width:
            self.last_width = width

        # Move cursor to home position and clear
        self.console.clear()

        # Render content
        self.header.set_page(self.current_page_idx + 1)
        self.footer.set_help(self.current_page.get_help())

        # Print header with terminal width
        self.console.print(self.header.render(width))

        # Show command result panel if available
        if self.show_command_result and self.generated_command:
            # Build command result content
            content = Text()
            content.append("Generated Command:\n\n", style="bold white")
            content.append(self.generated_command, style="bold green")
            content.append("\n\n")
            content.append("[x] ", style="bold yellow")
            content.append("Execute & Exit", style="white")
            content.append("  │  ", style="dim")
            content.append("[c] ", style="bold cyan")
            content.append("Copy to Clipboard", style="white")
            content.append("  │  ", style="dim")
            content.append("[q] ", style="bold red")
            content.append("Cancel", style="white")

            cmd_panel = Panel(
                content,
                title="[bold white]🕷 Command Builder[/]",
                border_style="green",
                padding=(1, 2),
            )
            self.console.print(cmd_panel)
        # Show protocol selector popup if needed
        elif self.command_builder.needs_protocol_selection:
            # Show selection status
            self.console.print(self.command_builder.render_status())
            self.console.print()
            self.console.print(
                self.command_builder.render_protocol_selector(self.console)
            )
        elif self.show_help:
            self.console.print(HelpPanel.render())
        else:
            # Show selection status bar if building command
            if self.command_builder.is_active:
                status = self.command_builder.render_status()
                if status.plain:
                    self.console.print(Panel(status, border_style="yellow", height=3))

            self.console.print(self.current_page.render(self.console))

        # Print footer
        self.console.print(self.footer.render())

    def run(self):
        """Run the dashboard main loop."""
        # Setup terminal for non-blocking input on Unix FIRST
        # (before any Rich operations that might affect terminal state)
        if sys.platform != "win32":
            _setup_terminal()

        # Hide cursor
        self.console.show_cursor(False)

        try:
            while self.running:
                # Check if terminal was resized
                current_width = self.console.size.width
                current_height = self.console.size.height
                if current_width != self.last_width:
                    self.last_width = current_width
                    self.needs_redraw = True

                # Check minimum terminal size
                if current_width < 60 or current_height < 15:
                    self.console.clear()
                    self.console.print("[yellow]Terminal too small. Please resize.[/]")
                    time.sleep(0.5)
                    self.needs_redraw = True
                    continue

                # Only redraw when needed
                if self.needs_redraw:
                    try:
                        self.draw()
                    except Exception as e:
                        # Handle rendering errors gracefully
                        self.console.clear()
                        self.console.print(f"[red]Render error:[/] {e}")
                        self.console.print("Press 'r' to retry, 'q' to quit.")
                    self.needs_redraw = False

                # Get keyboard input (non-blocking)
                key = get_key()
                if not self.handle_input(key):
                    break

                # Small sleep when no input to reduce CPU usage
                if key is None:
                    time.sleep(0.05)

        except KeyboardInterrupt:
            pass
        finally:
            # Restore terminal settings on Unix
            if sys.platform != "win32":
                _restore_terminal()
            self.db.close()
            self.console.show_cursor(True)
            self.console.clear()

            # If we have a command to execute, print it for the user
            if self.execute_command:
                self.console.print("[bold green]Command ready to execute:[/]")
                self.console.print(f"[bold cyan]{self.execute_command}[/]")
                self.console.print()
                # Copy to clipboard
                if copy_to_clipboard(self.execute_command):
                    self.console.print(
                        "[dim]✓ Copied to clipboard - press Ctrl+Shift+V or middle-click to paste[/]"
                    )
                else:
                    self.console.print(
                        "[dim yellow]Could not copy to clipboard. Copy the command above manually.[/]"
                    )
            else:
                self.console.print("[green]Dashboard closed.[/]")


def run_dashboard(args):
    """Entry point for dashboard."""
    console = Console()

    # Check if we're running in a TTY
    if not sys.stdin.isatty():
        console.print(
            "[red]Error:[/] Dashboard requires an interactive terminal (TTY)."
        )
        console.print("Cannot run in a pipe or non-interactive environment.")
        sys.exit(1)

    # Check minimum terminal size
    MIN_WIDTH = 60
    MIN_HEIGHT = 15
    if console.size.width < MIN_WIDTH or console.size.height < MIN_HEIGHT:
        console.print(
            f"[red]Error:[/] Terminal too small ({console.size.width}x{console.size.height})."
        )
        console.print(f"Minimum required: {MIN_WIDTH}x{MIN_HEIGHT}")
        sys.exit(1)

    # Handle demo data flags
    if getattr(args, "demo_clear", False):
        from nxc.dashboard.demo_data import clear_demo_data

        workspace = getattr(args, "workspace", "default")
        clear_demo_data(workspace)
        return

    if getattr(args, "demo", False):
        from nxc.dashboard.demo_data import populate_demo_data

        workspace = getattr(args, "workspace", "default")
        try:
            populate_demo_data(workspace)
        except PermissionError:
            console.print(
                f"[red]Error:[/] No write permission for workspace directory."
            )
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]Error creating demo data:[/] {e}")
            sys.exit(1)
        print()  # Empty line before starting dashboard

    # Check workspace exists and has databases
    workspace = getattr(args, "workspace", "default")
    workspace_path = os.path.join(
        os.path.expanduser("~"), ".nxc", "workspaces", workspace
    )
    if not os.path.exists(workspace_path):
        console.print(f"[yellow]Warning:[/] Workspace '{workspace}' does not exist.")
        console.print(
            "Run with [cyan]--demo[/] to create demo data, or run nxc against targets first."
        )
        sys.exit(0)

    # Check if any database files exist
    db_files = [f for f in os.listdir(workspace_path) if f.endswith(".db")]
    if not db_files:
        console.print(
            f"[yellow]Warning:[/] No database files in workspace '{workspace}'."
        )
        console.print(
            "Run with [cyan]--demo[/] to create demo data, or run nxc against targets first."
        )
        sys.exit(0)

    try:
        app = DashboardApp(args)
        app.run()
    except Exception as e:
        console.print(f"[red]Dashboard error:[/] {e}")
        sys.exit(1)

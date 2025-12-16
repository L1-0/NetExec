"""Command builder component for generating NetExec commands."""

from rich.panel import Panel
from rich.text import Text


class CommandBuilder:
    """Builds NetExec commands from selected host and credential."""

    # Available protocols with their requirements
    PROTOCOLS = {
        "smb": {"port": 445, "needs_cred": True},
        "ldap": {"port": 389, "needs_cred": True},
        "winrm": {"port": 5985, "needs_cred": True},
        "ssh": {"port": 22, "needs_cred": True},
        "mssql": {"port": 1433, "needs_cred": True},
        "rdp": {"port": 3389, "needs_cred": True},
        "ftp": {"port": 21, "needs_cred": True},
        "wmi": {"port": 135, "needs_cred": True},
        "vnc": {"port": 5900, "needs_cred": False},
        "nfs": {"port": 2049, "needs_cred": False},
    }

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset the command builder state."""
        self.state = "idle"  # idle, select_host, select_user, select_protocol, done
        self.selected_host = None
        self.selected_user = None
        self.selected_protocol = None
        self.protocol_index = 0
        self.available_protocols = list(self.PROTOCOLS.keys())
        self.start_from = None  # "hosts" or "users"

    def start_selection(self, start_from: str):
        """Start the selection process from hosts or users page."""
        self.reset()
        self.start_from = start_from
        if start_from == "hosts":
            self.state = "select_host"
        else:
            self.state = "select_user"

    def set_host(self, host_data: dict):
        """Set the selected host."""
        self.selected_host = host_data
        if self.start_from == "hosts":
            self.state = "select_user"
        else:
            self.state = "select_protocol"

    def set_user(self, user_data: dict):
        """Set the selected user/credential."""
        self.selected_user = user_data
        if self.start_from == "users":
            self.state = "select_host"
        else:
            self.state = "select_protocol"

    def get_available_protocols(self) -> list:
        """Get protocols based on host's available protocols."""
        if not self.selected_host:
            return self.available_protocols

        host_protos = self.selected_host.get("protocols", "")
        available = []

        # Map protocol letters to full names
        proto_map = {
            "S": "smb",
            "L": "ldap",
            "W": "winrm",
            "M": "mssql",
            "R": "rdp",
            "F": "ftp",
            "V": "vnc",
            "N": "nfs",
        }

        for letter in host_protos:
            if letter.upper() in proto_map:
                available.append(proto_map[letter.upper()])

        # If no protocols detected, show all
        return available if available else self.available_protocols

    def select_protocol(self, protocol: str):
        """Set the selected protocol."""
        self.selected_protocol = protocol
        self.state = "done"

    def handle_protocol_key(self, key: str) -> bool:
        """Handle key input in protocol selection. Returns True if selection made."""
        available = self.get_available_protocols()
        if not available:
            return False

        if key in ("up", "w"):
            self.protocol_index = (self.protocol_index - 1) % len(available)
            return False
        elif key in ("down", "s"):
            self.protocol_index = (self.protocol_index + 1) % len(available)
            return False
        elif key == "\r":  # Enter key
            self.select_protocol(available[self.protocol_index])
            return True
        return False

    def build_command(self) -> str:
        """Build the NetExec command from selections."""
        if not all([self.selected_host, self.selected_protocol]):
            return ""

        parts = ["nxc", self.selected_protocol]

        # Add target
        target = self.selected_host.get("ip", "")
        if target:
            parts.append(target)

        # Add credentials if we have them
        if self.selected_user:
            domain = self.selected_user.get("domain", "")
            username = self.selected_user.get("username", "")
            password = self.selected_user.get("password", "")
            credtype = self.selected_user.get("credtype", "plaintext")

            if domain and username:
                parts.extend(["-u", f"{domain}\\{username}"])
            elif username:
                parts.extend(["-u", username])

            if password:
                if credtype == "hash":
                    parts.extend(["-H", password])
                else:
                    parts.extend(["-p", f'"{password}"'])

        return " ".join(parts)

    def render_protocol_selector(self, console) -> Panel:
        """Render the protocol selection popup."""
        available = self.get_available_protocols()

        content = Text()
        content.append("Select Protocol\n\n", style="bold cyan")

        for i, proto in enumerate(available):
            prefix = "▶ " if i == self.protocol_index else "  "
            style = "reverse" if i == self.protocol_index else ""
            info = self.PROTOCOLS.get(proto, {})
            port = info.get("port", "")
            content.append(f"{prefix}{proto.upper():8}", style=style)
            content.append(f"  (port {port})\n", style="dim")

        content.append("\n[↑/↓] Navigate  [Enter] Select  [q] Cancel", style="dim")

        return Panel(
            content,
            title="[bold white]PROTOCOL[/]",
            border_style="yellow",
            width=40,
        )

    def render_status(self) -> Text:
        """Render current selection status."""
        status = Text()

        if self.selected_host:
            ip = self.selected_host.get("ip", "?")
            hostname = self.selected_host.get("hostname", "")
            status.append("Host: ", style="dim")
            status.append(f"{ip}", style="cyan")
            if hostname:
                status.append(f" ({hostname})", style="dim")

        if self.selected_user:
            if self.selected_host:
                status.append("  │  ", style="dim")
            domain = self.selected_user.get("domain", "")
            username = self.selected_user.get("username", "?")
            status.append("User: ", style="dim")
            if domain:
                status.append(f"{domain}\\", style="dim")
            status.append(username, style="green")

        return status

    def get_title_for_state(self) -> str:
        """Get the title based on current state."""
        if self.state == "select_host":
            if self.selected_user:
                return "Use with Host"
            return "Select Host"
        elif self.state == "select_user":
            if self.selected_host:
                return "Use with User"
            return "Select User"
        elif self.state == "select_protocol":
            return "Select Protocol"
        return ""

    @property
    def is_active(self) -> bool:
        """Check if command builder is active."""
        return self.state != "idle" and self.state != "done"

    @property
    def needs_protocol_selection(self) -> bool:
        """Check if we're in protocol selection state."""
        return self.state == "select_protocol"

    @property
    def is_complete(self) -> bool:
        """Check if command building is complete."""
        return self.state == "done"

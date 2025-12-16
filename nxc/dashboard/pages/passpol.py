"""Password Policy page - Domain password policy display."""

from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.console import Group


class PassPolPage:
    """Page 9: Password Policy - Domain password policy information."""

    name = "PassPol"
    key = "9"

    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.current_domain_idx = 0
        self.policies = []
        self.total = 0

    def _get_page_size(self, console) -> int:
        """Calculate page size based on terminal height."""
        available = console.size.height - 11
        return max(5, available)

    def render(self, console) -> Panel:
        """Render the password policy page."""
        terminal_width = console.size.width

        # Try to get password policies from database
        self.policies = self.db.get_password_policies()
        self.total = len(self.policies)

        if not self.policies:
            # No policies in DB - show info message
            content = Text()
            content.append(
                "\n  No password policies stored in database.\n\n", style="yellow"
            )
            content.append(
                "  Password policies are retrieved live and not stored by default.\n",
                style="dim",
            )
            content.append(
                "  To retrieve the domain password policy, run:\n\n", style="dim"
            )
            content.append(
                "    nxc smb <target> -u <user> -p <pass> --pass-pol\n", style="cyan"
            )
            content.append(
                "    nxc ldap <target> -u <user> -p <pass> --pass-pol\n\n", style="cyan"
            )
            content.append(
                "  For Fine Grained Password Policies (PSOs):\n\n", style="dim"
            )
            content.append(
                "    nxc ldap <target> -u <user> -p <pass> --pso\n", style="cyan"
            )

            return Panel(
                content,
                title="[bold white]PASSWORD POLICY[/]",
                subtitle="No data",
                border_style="blue",
            )

        # Ensure index is valid
        if self.current_domain_idx >= len(self.policies):
            self.current_domain_idx = 0

        policy = self.policies[self.current_domain_idx]
        domain = policy.get("domain", "Unknown")

        # Build policy display
        table = Table(show_header=False, box=None, expand=False, padding=(0, 2))
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")

        # Password settings
        table.add_row("", "")
        table.add_row(Text("PASSWORD SETTINGS", style="bold magenta"), "")
        table.add_row("Minimum Password Length", str(policy.get("min_length", "N/A")))
        table.add_row(
            "Password History Length", str(policy.get("history_length", "N/A"))
        )
        table.add_row(
            "Password Complexity", self._format_bool(policy.get("complexity", None))
        )
        table.add_row(
            "Minimum Password Age", self._format_duration(policy.get("min_age", None))
        )
        table.add_row(
            "Maximum Password Age", self._format_duration(policy.get("max_age", None))
        )

        # Lockout settings
        table.add_row("", "")
        table.add_row(Text("LOCKOUT SETTINGS", style="bold magenta"), "")
        table.add_row("Lockout Threshold", str(policy.get("lockout_threshold", "N/A")))
        table.add_row(
            "Lockout Duration",
            self._format_duration(policy.get("lockout_duration", None)),
        )
        table.add_row(
            "Lockout Observation Window",
            self._format_duration(policy.get("lockout_window", None)),
        )

        # Additional info
        if policy.get("pso_name"):
            table.add_row("", "")
            table.add_row(Text("FINE GRAINED POLICY (PSO)", style="bold magenta"), "")
            table.add_row("PSO Name", str(policy.get("pso_name", "")))
            table.add_row("Applies To", str(policy.get("applies_to", "")))

        # Navigation hint if multiple domains
        nav_hint = ""
        if len(self.policies) > 1:
            nav_hint = f" | [↑/↓] Switch domain ({self.current_domain_idx + 1}/{len(self.policies)})"

        if terminal_width < 100:
            subtitle = f"[{self.total} policies]{nav_hint}"
        else:
            subtitle = f"[{self.total} policies stored]{nav_hint}"

        return Panel(
            table,
            title=f"[bold white]PASSWORD POLICY - {domain}[/]",
            subtitle=subtitle,
            border_style="blue",
        )

    def _format_bool(self, value) -> str:
        """Format boolean value."""
        if value is None:
            return "N/A"
        return "Enabled" if value else "Disabled"

    def _format_duration(self, minutes) -> str:
        """Format duration in minutes to human readable."""
        if minutes is None:
            return "N/A"
        if minutes == 0:
            return "None"
        if minutes < 0:
            return "Never"

        days = minutes // (60 * 24)
        hours = (minutes % (60 * 24)) // 60
        mins = minutes % 60

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if mins > 0:
            parts.append(f"{mins}m")

        return " ".join(parts) if parts else "0m"

    def handle_key(self, key: str, console=None) -> bool:
        """Handle page-specific key presses."""
        if len(self.policies) <= 1:
            return False

        if key in ("down", "l"):
            self.current_domain_idx = (self.current_domain_idx + 1) % len(self.policies)
            return True
        elif key in ("up", "h"):
            self.current_domain_idx = (self.current_domain_idx - 1) % len(self.policies)
            return True
        return False

    def get_help(self) -> str:
        """Return help text for this page."""
        if len(self.policies) > 1:
            return "[↑/↓] Switch domain"
        return "Password policy info"

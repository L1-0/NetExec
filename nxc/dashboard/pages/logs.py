"""Logs page - log tailing and event history."""

from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import re


class LogsPage:
    """Page 8: Logs - Real-time log tailing and event history."""

    name = "Logs"
    key = "8"

    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.log_file = config.get("log_file")
        self.filters = {}
        self.paused = False
        self.line_count = None  # Will be calculated dynamically

    def _get_line_count(self, console) -> int:
        """Calculate line count based on terminal height."""
        # Reserve: header(3) + footer(2) + panel border(2) + padding(3) = 10
        available = console.size.height - 10
        return max(10, available)  # Minimum 10 lines

    def render(self, console) -> Panel:
        """Render the logs page."""
        line_count = self._get_line_count(console)

        if not self.log_file:
            content = Text(
                "\n  No log file specified.\n  Use --log-file or -l to specify a log file.\n",
                style="dim",
            )
            return Panel(
                content,
                title="[bold white]LOGS[/]",
                subtitle="No log file",
                border_style="blue",
            )

        lines = self.db.get_log_entries(self.log_file, line_count)

        content = Text()
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Apply filters
            if self.filters.get("success") and "[+]" not in line:
                continue
            if self.filters.get("fail") and "[-]" not in line:
                continue
            if self.filters.get("info") and "[*]" not in line:
                continue

            # Color based on log type
            if "[+]" in line:
                style = "green"
            elif "[-]" in line:
                style = "red"
            elif "[*]" in line:
                style = "cyan"
            elif "[!]" in line:
                style = "yellow"
            else:
                style = "white"

            content.append(f"  {line}\n", style=style)

        if not content.plain:
            content.append("\n  No log entries found.\n", style="dim")

        # Status
        pause_status = " [PAUSED]" if self.paused else ""
        filter_status = []
        if self.filters.get("success"):
            filter_status.append("[+]")
        if self.filters.get("fail"):
            filter_status.append("[-]")
        if self.filters.get("info"):
            filter_status.append("[*]")
        filter_text = f" | Filter: {', '.join(filter_status)}" if filter_status else ""

        subtitle = f"Last {line_count} entries{pause_status}{filter_text}"

        return Panel(
            content,
            title=f"[bold white]LOGS[/] - {self.log_file}",
            subtitle=subtitle,
            border_style="blue",
        )

    def handle_key(self, key: str, console=None) -> bool:
        """Handle page-specific key presses."""
        if key == "P":  # Shift+P to pause
            self.paused = not self.paused
            return True
        elif key == "+":
            self.filters = {"success": True}
            return True
        elif key == "-":
            self.filters = {"fail": True}
            return True
        elif key == "*":
            self.filters = {"info": True}
            return True
        elif key == "x":
            self.filters = {}
            return True
        return False

    def get_help(self) -> str:
        """Return help text for this page."""
        return "[P] Pause | [+] Success | [-] Fail | [*] Info | [x] Clear"

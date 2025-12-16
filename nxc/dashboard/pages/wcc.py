"""WCC page - Windows Configuration Checks."""

from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.console import Group
from nxc.dashboard.components.responsive import (
    ResponsiveTable,
    ResponsiveColumn,
    PRIORITY_CRITICAL,
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
    PRIORITY_LOW,
)


class WCCPage:
    """Page 7: WCC - Windows Configuration Check results."""

    name = "WCC"
    key = "7"

    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.current_page = 1
        self.page_size = config.get("page_size", 20)
        self.filters = {}
        self.total = 0
        self.summary = {"pass": 0, "fail": 0, "warn": 0}

        # Define responsive columns - Check Name, Host, Result are critical
        # Use None for width to let Rich auto-size based on content
        self.columns = [
            ResponsiveColumn("ID", "id", None, PRIORITY_MEDIUM, style="dim"),
            ResponsiveColumn("Check Name", "check_name", None, PRIORITY_CRITICAL),
            ResponsiveColumn("Host", "host", None, PRIORITY_CRITICAL, style="cyan"),
            ResponsiveColumn("Result", "result", None, PRIORITY_CRITICAL),
            ResponsiveColumn("Details", "details", None, PRIORITY_HIGH),
        ]
        self.responsive_table = ResponsiveTable(self.columns)

    def _get_page_size(self, console) -> int:
        """Calculate page size based on terminal height."""
        # Reserve extra for summary line: header(3) + footer(2) + panel(2) + table header(2) + summary(2) + padding(2) = 13
        available = console.size.height - 13
        return max(5, available)  # Minimum 5 rows

    def render(self, console) -> Panel:
        """Render the WCC page."""
        page_size = self._get_page_size(console)
        result = self.db.get_wcc_checks(self.current_page, page_size, self.filters)
        if len(result) == 3:
            checks, self.total, self.summary = result
        else:
            checks, self.total = result
            self.summary = {"pass": 0, "fail": 0, "warn": 0}

        total_pages = max(1, (self.total + page_size - 1) // page_size)
        terminal_width = console.size.width
        visible_cols = self.responsive_table.get_visible_columns(terminal_width)

        # Summary line - compact on narrow screens
        summary_text = Text()
        if terminal_width >= 80:
            summary_text.append("  Summary: ", style="bold")
            summary_text.append(
                f"✓ {self.summary.get('pass', 0)} Pass  ", style="green"
            )
            summary_text.append(f"✗ {self.summary.get('fail', 0)} Fail  ", style="red")
            summary_text.append(
                f"⚠  {self.summary.get('warn', 0)} Warn", style="yellow"
            )
        else:
            summary_text.append(f"  ✓ {self.summary.get('pass', 0)} ", style="green")
            summary_text.append(f"✗ {self.summary.get('fail', 0)} ", style="red")
            summary_text.append(f"⚠  {self.summary.get('warn', 0)}", style="yellow")
        summary_text.append("\n\n")

        # Results table
        table = Table(
            show_header=True,
            header_style="bold magenta",
            box=None,
            expand=True,
            padding=(0, 1),
        )

        for col in visible_cols:
            table.add_column(
                col.name, style=col.style, width=col.width, justify=col.justify
            )

        for check in checks:
            row_values = []
            for col in visible_cols:
                value = check.get(col.key, "")

                # Special handling for host - show IP (hostname) if available
                if col.key == "host":
                    ip = check.get("host", "")
                    hostname = check.get("hostname", "")
                    if hostname and hostname != ip:
                        value = f"{ip} ({hostname})"
                    else:
                        value = ip
                # Special handling for result with icon
                elif col.key == "result":
                    result_val = str(value or "")
                    if result_val == "PASS":
                        value = Text("✓ PASS", style="green bold")
                    elif result_val == "FAIL":
                        value = Text("✗ FAIL", style="red bold")
                    else:
                        value = Text(f"⚠  {result_val}", style="yellow")
                else:
                    formatted = (
                        col.formatter(value) if col.formatter else str(value or "")
                    )
                    value = formatted

                row_values.append(value)

            table.add_row(*row_values)

        content = Group(summary_text, table)

        # Filter status
        filter_status = []
        if self.filters.get("pass"):
            filter_status.append("pass")
        if self.filters.get("fail"):
            filter_status.append("fail")
        if self.filters.get("warn"):
            filter_status.append("warn")
        filter_text = f" | Filter: {', '.join(filter_status)}" if filter_status else ""

        if terminal_width < 100:
            subtitle = f"{self.current_page}/{total_pages} [{self.total}]{filter_text}"
        else:
            subtitle = f"Page {self.current_page}/{total_pages} [{self.total} total]{filter_text}"

        return Panel(
            content,
            title="[bold white]WCC - Security Checks[/]",
            subtitle=subtitle,
            border_style="blue",
        )

    def handle_key(self, key: str, console=None) -> bool:
        """Handle page-specific key presses."""
        page_size = self._get_page_size(console) if console else self.page_size
        total_pages = max(1, (self.total + page_size - 1) // page_size)

        if key in ("down", "l"):
            if self.current_page < total_pages:
                self.current_page += 1
            return True
        elif key in ("up", "h"):
            if self.current_page > 1:
                self.current_page -= 1
            return True
        elif key == "g":
            self.current_page = 1
            return True
        elif key == "G":
            self.current_page = total_pages
            return True
        elif key == "p":
            self.filters = {"pass": True}
            self.current_page = 1
            return True
        elif key == "f":
            self.filters = {"fail": True}
            self.current_page = 1
            return True
        elif key == "W":  # Shift+W for warnings
            self.filters = {"warn": True}
            self.current_page = 1
            return True
        elif key == "x":
            self.filters = {}
            self.current_page = 1
            return True
        return False

    def get_help(self) -> str:
        """Return help text for this page."""
        return "[↑/↓] Data Page | [p] Pass | [f] Fail | [W] Warn | [x] Clear"

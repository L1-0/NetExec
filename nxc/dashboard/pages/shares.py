"""Shares page - SMB share discovery results."""

from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from nxc.dashboard.components.responsive import (
    ResponsiveTable,
    ResponsiveColumn,
    PRIORITY_CRITICAL,
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
    PRIORITY_LOW,
)


class SharesPage:
    """Page 4: Shares - SMB share discovery results."""

    name = "Shares"
    key = "4"

    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.current_page = 1
        self.page_size = config.get("page_size", 20)
        self.filters = {}
        self.total = 0

        # Define responsive columns - Host and Share Name are critical
        self.columns = [
            ResponsiveColumn("ID", "id", 4, PRIORITY_MEDIUM, style="dim"),
            ResponsiveColumn("Host", "host", 15, PRIORITY_CRITICAL, style="cyan"),
            ResponsiveColumn("Share Name", "name", 15, PRIORITY_CRITICAL),
            ResponsiveColumn("Access", "access", 12, PRIORITY_HIGH),
            ResponsiveColumn("Remark", "remark", 30, PRIORITY_LOW),
        ]
        self.responsive_table = ResponsiveTable(self.columns)

    def _get_page_size(self, console) -> int:
        """Calculate page size based on terminal height."""
        # Reserve: header(3) + footer(2) + panel border(2) + table header(2) + padding(2) = 11
        available = console.size.height - 11
        return max(5, available)  # Minimum 5 rows

    def render(self, console) -> Panel:
        """Render the shares page."""
        page_size = self._get_page_size(console)
        shares, self.total = self.db.get_shares(
            self.current_page, page_size, self.filters
        )
        total_pages = max(1, (self.total + page_size - 1) // page_size)

        # Get terminal width
        terminal_width = console.size.width
        visible_cols = self.responsive_table.get_visible_columns(terminal_width)

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

        for share in shares:
            row_values = []
            for col in visible_cols:
                value = share.get(col.key, "")

                # Special handling for access with color
                if col.key == "access":
                    access = str(value or "")
                    if "WRITE" in access:
                        value = Text(access, style="green bold")
                    elif "READ" in access:
                        value = Text(access, style="yellow")
                    else:
                        value = Text(access, style="red")
                else:
                    formatted = (
                        col.formatter(value) if col.formatter else str(value or "")
                    )
                    if isinstance(formatted, str) and len(formatted) > col.max_width:
                        formatted = formatted[: col.max_width - 1] + "…"
                    value = formatted

                row_values.append(value)

            table.add_row(*row_values)

        # Filter status
        filter_status = []
        if self.filters.get("write"):
            filter_status.append("write")
        if self.filters.get("read_only"):
            filter_status.append("read")
        if self.filters.get("no_access"):
            filter_status.append("no-access")
        filter_text = f" | Filter: {', '.join(filter_status)}" if filter_status else ""

        if terminal_width < 100:
            subtitle = f"{self.current_page}/{total_pages} [{self.total}]{filter_text}"
        else:
            subtitle = f"Page {self.current_page}/{total_pages} [{self.total} total]{filter_text}"

        return Panel(
            table,
            title="[bold white]SHARES[/]",
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
        elif key == "w":
            self.filters = {"write": True}
            self.current_page = 1
            return True
        elif key == "r":
            self.filters = {"read_only": True}
            self.current_page = 1
            return True
        elif key == "n":
            self.filters = {"no_access": True}
            self.current_page = 1
            return True
        elif key == "x":
            self.filters = {}
            self.current_page = 1
            return True
        return False

    def get_help(self) -> str:
        """Return help text for this page."""
        return "[↑/↓] Data Page | [w] Write | [r] Read | [n] No access | [x] Clear"

"""DPAPI page - DPAPI secrets inventory."""

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


class DPAPIPage:
    """Page 6: DPAPI - DPAPI secrets inventory (masked by default)."""

    name = "DPAPI"
    key = "6"

    TYPE_COLORS = {
        "browser": "cyan",
        "credential": "green",
        "vault": "yellow",
        "certificate": "magenta",
    }

    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.current_page = 1
        self.page_size = config.get("page_size", 20)
        self.filters = {}
        self.total = 0
        self.unmask = config.get("unmask", False)

        # Define responsive columns - Type, Host, Username are critical
        # Use None for width to let Rich auto-size based on content
        self.columns = [
            ResponsiveColumn("ID", "id", None, PRIORITY_MEDIUM, style="dim"),
            ResponsiveColumn("Type", "type", None, PRIORITY_CRITICAL, style="yellow"),
            ResponsiveColumn("Host", "host", None, PRIORITY_CRITICAL, style="cyan"),
            ResponsiveColumn("Win User", "user", None, PRIORITY_HIGH),
            ResponsiveColumn("Username", "username", None, PRIORITY_HIGH),
            ResponsiveColumn("Password", "password", None, PRIORITY_MEDIUM),
            ResponsiveColumn("URL", "url", None, PRIORITY_LOW),
        ]
        self.responsive_table = ResponsiveTable(self.columns)

    def _mask_secret(self, secret: str) -> str:
        """Mask a secret unless unmasked."""
        if self.unmask or not secret:
            return secret or ""
        # Uniform 6-star masking for security
        return "******" if secret else ""

    def _get_page_size(self, console) -> int:
        """Calculate page size based on terminal height."""
        # Reserve: header(3) + footer(2) + panel border(2) + table header(2) + padding(2) = 11
        available = console.size.height - 11
        return max(5, available)  # Minimum 5 rows

    def render(self, console) -> Panel:
        """Render the DPAPI page."""
        page_size = self._get_page_size(console)
        dpapi_items, self.total = self.db.get_dpapi(
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

        for item in dpapi_items:
            row_values = []
            for col in visible_cols:
                value = item.get(col.key, "")

                # Special handling for type with color
                if col.key == "type":
                    dtype = str(value or "")
                    style = self.TYPE_COLORS.get(dtype.lower(), "white")
                    value = Text(dtype, style=style)
                elif col.key == "password":
                    value = self._mask_secret(value)
                else:
                    formatted = (
                        col.formatter(value) if col.formatter else str(value or "")
                    )
                    value = formatted

                row_values.append(value)

            table.add_row(*row_values)

        mask_status = "[unmasked]" if self.unmask else "[masked]"
        if terminal_width < 100:
            subtitle = f"{self.current_page}/{total_pages} [{self.total}] {mask_status}"
        else:
            subtitle = f"Page {self.current_page}/{total_pages} [{self.total} total] {mask_status}"

        return Panel(
            table,
            title="[bold white]DPAPI SECRETS[/]",
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
        elif key == "u":
            self.unmask = not self.unmask
            return True
        elif key == "x":
            self.filters = {}
            self.current_page = 1
            return True
        return False

    def get_help(self) -> str:
        """Return help text for this page."""
        return "[↑/↓] Data Page | [u] Unmask | [x] Clear"

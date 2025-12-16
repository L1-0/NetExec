"""Hosts page - unified view of all discovered hosts."""

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


class HostsPage:
    """Page 2: Hosts - All discovered hosts across protocols."""

    name = "Hosts"
    key = "2"

    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.current_page = 1
        self.page_size = config.get("page_size", 20)
        self.filters = {}
        self.total = 0

        # Selection mode
        self.selection_mode = False
        self.selected_row = 0
        self.custom_title = None
        self._cached_hosts = []

        # Define responsive columns - IP and Hostname are critical
        # Use None for width to let Rich auto-size columns
        self.columns = [
            ResponsiveColumn("ID", "id", None, PRIORITY_MEDIUM, style="dim"),
            ResponsiveColumn("IP", "ip", None, PRIORITY_CRITICAL, style="cyan"),
            ResponsiveColumn("Hostname", "hostname", None, PRIORITY_CRITICAL),
            ResponsiveColumn("Domain", "domain", None, PRIORITY_LOW),
            ResponsiveColumn("OS", "os", None, PRIORITY_MEDIUM),
            ResponsiveColumn(
                "DC", "dc", 3, PRIORITY_HIGH, formatter=lambda x: "✓" if x else ""
            ),
            ResponsiveColumn(
                "Protocols", "protocols", None, PRIORITY_HIGH, style="yellow"
            ),
        ]
        self.responsive_table = ResponsiveTable(self.columns)

        # Protocol legend
        self.proto_legend = "F=FTP L=LDAP M=MSSQL N=NFS R=RDP S=SMB V=VNC W=WMI/WINRM"

    def _get_page_size(self, console) -> int:
        """Calculate page size based on terminal height."""
        # Reserve: header(3) + footer(2) + panel border(2) + table header(2) + padding(2) = 11
        available = console.size.height - 11
        return max(5, available)  # Minimum 5 rows

    def enter_selection_mode(self, title: str = None):
        """Enter row selection mode."""
        self.selection_mode = True
        self.selected_row = 0
        self.custom_title = title

    def exit_selection_mode(self):
        """Exit row selection mode."""
        self.selection_mode = False
        self.selected_row = 0
        self.custom_title = None

    def get_selected_host(self) -> dict:
        """Get the currently selected host data."""
        if self._cached_hosts and 0 <= self.selected_row < len(self._cached_hosts):
            return self._cached_hosts[self.selected_row]
        return None

    def render(self, console) -> Panel:
        """Render the hosts page."""
        page_size = self._get_page_size(console)
        hosts, self.total = self.db.get_hosts(
            self.current_page, page_size, self.filters
        )
        self._cached_hosts = hosts  # Cache for selection
        total_pages = max(1, (self.total + page_size - 1) // page_size)

        # Get terminal width for responsive columns
        terminal_width = console.size.width
        visible_cols = self.responsive_table.get_visible_columns(terminal_width)

        table = Table(
            show_header=True,
            header_style="bold magenta",
            box=None,
            expand=True,
            padding=(0, 1),
        )

        # Add only visible columns
        for col in visible_cols:
            table.add_column(
                col.name, style=col.style, width=col.width, justify=col.justify
            )

        for idx, host in enumerate(hosts):
            row_values = []
            is_selected = self.selection_mode and idx == self.selected_row

            for col in visible_cols:
                value = host.get(col.key, "")
                formatted = col.formatter(value) if col.formatter else str(value or "")

                # Highlight selected row
                if is_selected:
                    formatted = Text(str(formatted), style="reverse bold")

                row_values.append(formatted)

            table.add_row(*row_values)

        # Build filter status
        filter_status = []
        if self.filters.get("has_shares"):
            filter_status.append("[s]hares")
        if self.filters.get("has_creds"):
            filter_status.append("[c]reds")
        filter_text = f" | Filters: {', '.join(filter_status)}" if filter_status else ""

        # Build subtitle with pagination and legend
        if terminal_width < 100:
            subtitle = f"{self.current_page}/{total_pages} [{self.total}]{filter_text}"
        elif terminal_width < 140:
            subtitle = f"Page {self.current_page}/{total_pages} [{self.total} total]{filter_text}"
        else:
            subtitle = f"Page {self.current_page}/{total_pages} [{self.total} total]{filter_text}  [dim]│[/]  [yellow]{self.proto_legend}[/]"

        # Custom title for selection mode
        title = (
            f"[bold white]{self.custom_title}[/]"
            if self.custom_title
            else "[bold white]HOSTS[/]"
        )
        border_style = "yellow" if self.selection_mode else "blue"

        return Panel(
            table,
            title=title,
            subtitle=subtitle,
            border_style=border_style,
        )

    def handle_key(self, key: str, console=None) -> bool:
        """Handle page-specific key presses."""
        page_size = self._get_page_size(console) if console else self.page_size
        total_pages = max(1, (self.total + page_size - 1) // page_size)
        num_rows = len(self._cached_hosts)

        # Selection mode navigation
        if self.selection_mode:
            if key in ("up", "w"):
                self.selected_row = max(0, self.selected_row - 1)
                return True
            elif key in ("down", "s"):
                self.selected_row = min(num_rows - 1, self.selected_row + 1)
                return True
            elif key == "\r":  # Enter - signal selection made
                return "selected"
        else:
            # Up/Down arrow enters selection mode from top or bottom
            if key == "down" and num_rows > 0:
                self.selected_row = 0  # Start from top
                return "enter_selection"
            elif key == "up" and num_rows > 0:
                self.selected_row = num_rows - 1  # Start from bottom
                return "enter_selection"

        # Left/Right for data page navigation
        if key in ("right", "l"):
            if self.current_page < total_pages:
                self.current_page += 1
                self.selected_row = 0
            return True
        elif key in ("left", "h"):
            if self.current_page > 1:
                self.current_page -= 1
                self.selected_row = 0
            return True
        elif key == "g":
            self.current_page = 1
            self.selected_row = 0
            return True
        elif key == "G":
            self.current_page = total_pages
            self.selected_row = 0
            return True
        elif key == "s" and not self.selection_mode:
            self.filters["has_shares"] = not self.filters.get("has_shares", False)
            self.current_page = 1
            return True
        elif key == "c" and not self.selection_mode:
            self.filters["has_creds"] = not self.filters.get("has_creds", False)
            self.current_page = 1
            return True
        elif key == "x" and not self.selection_mode:
            self.filters = {}
            self.current_page = 1
            return True
        return False

    def get_help(self) -> str:
        """Return help text for this page."""
        if self.selection_mode:
            return "[↑/↓] Select | [Enter] Confirm | [q] Cancel"
        return "[←/→] Page | [↑/↓] Select | [s] Shares | [c] Creds | [x] Clear"

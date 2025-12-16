"""Groups page - discovered group memberships."""

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


class GroupsPage:
    """Page 5: Groups - Discovered group memberships."""

    name = "Groups"
    key = "5"

    # Privileged groups for highlighting
    PRIVILEGED_GROUPS = [
        "domain admins",
        "enterprise admins",
        "administrators",
        "backup operators",
        "schema admins",
        "account operators",
        "server operators",
        "print operators",
    ]

    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.current_page = 1
        self.page_size = config.get("page_size", 20)
        self.filters = {}
        self.total = 0

        # Define responsive columns - Group Name is critical
        # Use None for width to let Rich auto-size based on content
        self.columns = [
            ResponsiveColumn("ID", "id", None, PRIORITY_MEDIUM, style="dim"),
            ResponsiveColumn(
                "Group Name", "name", None, PRIORITY_CRITICAL, style="cyan"
            ),
            ResponsiveColumn("Domain", "domain", None, PRIORITY_HIGH),
            ResponsiveColumn("Type", "type", None, PRIORITY_HIGH),
            ResponsiveColumn(
                "Members", "members", None, PRIORITY_HIGH, justify="right"
            ),
            ResponsiveColumn("Proto", "protocol", None, PRIORITY_MEDIUM),
        ]
        self.responsive_table = ResponsiveTable(self.columns)

    def _get_page_size(self, console) -> int:
        """Calculate page size based on terminal height."""
        # Reserve: header(3) + footer(2) + panel border(2) + table header(2) + padding(2) = 11
        available = console.size.height - 11
        return max(5, available)  # Minimum 5 rows

    def render(self, console) -> Panel:
        """Render the groups page."""
        page_size = self._get_page_size(console)
        groups, self.total = self.db.get_groups(
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

        for group in groups:
            row_values = []
            for col in visible_cols:
                value = group.get(col.key, "")

                # Special handling for group name with privilege highlighting
                if col.key == "name":
                    name = str(value or "")
                    is_privileged = name.lower() in self.PRIVILEGED_GROUPS
                    value = Text(name, style="red bold" if is_privileged else "cyan")
                elif col.key == "type":
                    gtype = str(value or "")
                    value = Text(
                        gtype, style="green" if gtype == "domain" else "yellow"
                    )
                else:
                    formatted = (
                        col.formatter(value) if col.formatter else str(value or "")
                    )
                    value = formatted

                row_values.append(value)

            table.add_row(*row_values)

        # Filter status
        filter_status = []
        if self.filters.get("domain"):
            filter_status.append("domain")
        if self.filters.get("local"):
            filter_status.append("local")
        filter_text = f" | Filter: {', '.join(filter_status)}" if filter_status else ""

        if terminal_width < 100:
            subtitle = f"{self.current_page}/{total_pages} [{self.total}]{filter_text}"
        else:
            subtitle = f"Page {self.current_page}/{total_pages} [{self.total} total]{filter_text}"

        return Panel(
            table,
            title="[bold white]GROUPS[/]",
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
        elif key == "d":
            self.filters = {"domain": True}
            self.current_page = 1
            return True
        elif key == "L":  # Shift+L for local
            self.filters = {"local": True}
            self.current_page = 1
            return True
        elif key == "x":
            self.filters = {}
            self.current_page = 1
            return True
        return False

    def get_help(self) -> str:
        """Return help text for this page."""
        return "[↑/↓] Data Page | [d] Domain | [L] Local | [x] Clear"

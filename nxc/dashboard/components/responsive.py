"""Responsive table utilities for adaptive column display."""

from rich.table import Table
from rich.text import Text
from typing import List, Dict, Any, Callable, Optional


# Column priority levels - lower number = higher priority (always shown)
PRIORITY_CRITICAL = 1  # Always shown (IP, Username)
PRIORITY_HIGH = 2  # Shown on medium+ screens (Hostname, Access)
PRIORITY_MEDIUM = 3  # Shown on large screens (Domain, OS)
PRIORITY_LOW = 4  # Only on wide screens (Remarks, Last Seen)


class ResponsiveColumn:
    """Definition of a responsive table column."""

    def __init__(
        self,
        name: str,
        key: str,
        width: int,
        priority: int = PRIORITY_MEDIUM,
        style: str = "",
        justify: str = "left",
        formatter: Optional[Callable[[Any], Any]] = None,
        max_width: Optional[int] = None,
        no_wrap: bool = False,
        overflow: str = "ellipsis",
    ):
        self.name = name
        self.key = key
        self.width = width
        self.priority = priority
        self.style = style
        self.justify = justify
        self.formatter = formatter or (lambda x: str(x) if x else "")
        self.max_width = max_width or width
        self.no_wrap = no_wrap
        self.overflow = overflow  # "ellipsis", "fold", "crop"


class ResponsiveTable:
    """A table that adapts columns based on terminal width."""

    # Terminal width thresholds
    WIDTH_NARROW = 80
    WIDTH_MEDIUM = 120
    WIDTH_WIDE = 160

    def __init__(self, columns: List[ResponsiveColumn], title: str = ""):
        self.columns = columns
        self.title = title

    def get_visible_columns(self, terminal_width: int) -> List[ResponsiveColumn]:
        """Get columns that fit within the terminal width."""
        # Determine max priority based on width
        if terminal_width < self.WIDTH_NARROW:
            max_priority = PRIORITY_CRITICAL
        elif terminal_width < self.WIDTH_MEDIUM:
            max_priority = PRIORITY_HIGH
        elif terminal_width < self.WIDTH_WIDE:
            max_priority = PRIORITY_MEDIUM
        else:
            max_priority = PRIORITY_LOW

        # Filter columns by priority
        visible = [c for c in self.columns if c.priority <= max_priority]

        # Calculate total width needed (treat None as 10 for estimation)
        # Use 1 space between columns for tighter layout
        total_width = sum(c.width or 10 for c in visible) + len(visible)

        # If still too wide, remove lowest priority columns
        while total_width > terminal_width - 6 and len(visible) > 1:
            # Remove lowest priority (highest number) column
            visible = sorted(visible, key=lambda c: c.priority)
            visible = visible[:-1]
            total_width = sum(c.width or 10 for c in visible) + len(visible)

        return visible

    def build_table(self, data: List[Dict], terminal_width: int) -> Table:
        """Build a Rich table with responsive columns."""
        visible_columns = self.get_visible_columns(terminal_width)

        table = Table(
            show_header=True,
            header_style="bold magenta",
            box=None,
            expand=True,
        )

        for col in visible_columns:
            table.add_column(
                col.name,
                style=col.style,
                width=col.width,
                justify=col.justify,
            )

        for row in data:
            row_values = []
            for col in visible_columns:
                value = row.get(col.key, "")
                formatted = col.formatter(value)

                # Truncate if needed
                if isinstance(formatted, str) and len(formatted) > col.max_width:
                    formatted = formatted[: col.max_width - 1] + "…"

                row_values.append(formatted)

            table.add_row(*row_values)

        return table


# Pre-defined column sets for each page

HOSTS_COLUMNS = [
    ResponsiveColumn("ID", "id", 4, PRIORITY_HIGH, style="dim"),
    ResponsiveColumn("IP", "ip", 15, PRIORITY_CRITICAL, style="cyan"),
    ResponsiveColumn("Hostname", "hostname", 15, PRIORITY_CRITICAL),
    ResponsiveColumn("Domain", "domain", 15, PRIORITY_LOW),
    ResponsiveColumn("OS", "os", 20, PRIORITY_MEDIUM),
    ResponsiveColumn(
        "DC", "dc", 3, PRIORITY_HIGH, formatter=lambda x: "✓" if x else ""
    ),
    ResponsiveColumn("Proto", "protocols", 8, PRIORITY_HIGH, style="yellow"),
]

CREDS_COLUMNS = [
    ResponsiveColumn("ID", "id", 4, PRIORITY_HIGH, style="dim"),
    ResponsiveColumn("Domain", "domain", 12, PRIORITY_LOW),
    ResponsiveColumn("Username", "username", 15, PRIORITY_CRITICAL, style="cyan"),
    ResponsiveColumn("Secret", "password", 20, PRIORITY_CRITICAL),
    ResponsiveColumn("Type", "credtype", 8, PRIORITY_HIGH),
    ResponsiveColumn("Source", "source", 8, PRIORITY_MEDIUM),
    ResponsiveColumn("Reuse", "reuse_count", 5, PRIORITY_LOW, justify="right"),
]

SHARES_COLUMNS = [
    ResponsiveColumn("ID", "id", 4, PRIORITY_HIGH, style="dim"),
    ResponsiveColumn("Host", "host", 15, PRIORITY_CRITICAL, style="cyan"),
    ResponsiveColumn("Share Name", "name", 15, PRIORITY_CRITICAL),
    ResponsiveColumn("Access", "access", 12, PRIORITY_HIGH),
    ResponsiveColumn("Remark", "remark", 30, PRIORITY_LOW),
]

USERS_COLUMNS = [
    ResponsiveColumn("Domain", "domain", 12, PRIORITY_LOW),
    ResponsiveColumn("Username", "username", 18, PRIORITY_CRITICAL, style="cyan"),
    ResponsiveColumn("Host IP", "host", 15, PRIORITY_CRITICAL),
    ResponsiveColumn("Hostname", "hostname", 15, PRIORITY_HIGH),
    ResponsiveColumn("Access", "access_level", 12, PRIORITY_CRITICAL),
]

GROUPS_COLUMNS = [
    ResponsiveColumn("ID", "id", 4, PRIORITY_HIGH, style="dim"),
    ResponsiveColumn("Group Name", "name", 20, PRIORITY_CRITICAL),
    ResponsiveColumn("Type", "type", 8, PRIORITY_HIGH),
    ResponsiveColumn("Members", "members", 8, PRIORITY_MEDIUM, justify="right"),
    ResponsiveColumn("Source Host", "source_host", 15, PRIORITY_HIGH),
    ResponsiveColumn("Proto", "protocol", 8, PRIORITY_LOW, style="yellow"),
]

DPAPI_COLUMNS = [
    ResponsiveColumn("ID", "id", 4, PRIORITY_HIGH, style="dim"),
    ResponsiveColumn("Type", "type", 12, PRIORITY_CRITICAL),
    ResponsiveColumn("Host", "host", 15, PRIORITY_CRITICAL, style="cyan"),
    ResponsiveColumn("User", "user", 15, PRIORITY_HIGH),
    ResponsiveColumn("Module", "module", 12, PRIORITY_MEDIUM),
    ResponsiveColumn("Collected", "collected", 10, PRIORITY_LOW),
]

WCC_COLUMNS = [
    ResponsiveColumn("ID", "id", 4, PRIORITY_HIGH, style="dim"),
    ResponsiveColumn("Check Name", "name", 20, PRIORITY_CRITICAL),
    ResponsiveColumn("Host", "host", 15, PRIORITY_CRITICAL, style="cyan"),
    ResponsiveColumn("Result", "result", 8, PRIORITY_CRITICAL),
    ResponsiveColumn("Details", "details", 25, PRIORITY_LOW),
]

"""Users page - Host user access levels (admin vs regular user)."""

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


class UsersPage:
    """Page 9: Users - Users with their access levels on hosts."""

    name = "Users"
    key = "9"

    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.current_page = 1
        self.page_size = config.get("page_size", 20)
        self.filters = {}
        self.total = 0
        self.host_filter = ""

        # Selection mode
        self.selection_mode = False
        self.selected_row = 0
        self.custom_title = None
        self._cached_users = []

        # Define responsive columns - Username, Host IP, and Access are critical
        self.columns = [
            ResponsiveColumn("Domain", "domain", None, PRIORITY_LOW),
            ResponsiveColumn(
                "Username", "username", None, PRIORITY_CRITICAL, style="cyan"
            ),
            ResponsiveColumn("Host IP", "host", None, PRIORITY_CRITICAL),
            ResponsiveColumn("Hostname", "hostname", None, PRIORITY_HIGH),
            ResponsiveColumn("Access", "access_level", None, PRIORITY_CRITICAL),
        ]
        self.responsive_table = ResponsiveTable(self.columns)

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

    def get_selected_user(self) -> dict:
        """Get the currently selected user data."""
        if self._cached_users and 0 <= self.selected_row < len(self._cached_users):
            return self._cached_users[self.selected_row]
        return None

    def render(self, console) -> Panel:
        """Render the users page."""
        filters = self.filters.copy()
        if self.host_filter:
            filters["host"] = self.host_filter

        page_size = self._get_page_size(console)
        users, self.total = self.db.get_host_users(
            self.current_page, page_size, filters
        )
        self._cached_users = users  # Cache for selection
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

        for idx, user in enumerate(users):
            row_values = []
            is_selected = self.selection_mode and idx == self.selected_row

            for col in visible_cols:
                value = user.get(col.key, "")

                # Special handling for access level with icons
                if col.key == "access_level":
                    access = str(value or "user")
                    if access == "admin":
                        text = Text("👑 ADMIN", style="red bold")
                    else:
                        text = Text("👤 USER", style="green")
                    if is_selected:
                        text.stylize("reverse")
                    value = text
                else:
                    formatted = (
                        col.formatter(value) if col.formatter else str(value or "")
                    )
                    if is_selected:
                        value = Text(str(formatted), style="reverse bold")
                    else:
                        value = formatted

                row_values.append(value)

            table.add_row(*row_values)

        # Filter status
        filter_status = []
        if self.filters.get("admin_only"):
            filter_status.append("admins only")
        if self.filters.get("user_only"):
            filter_status.append("users only")
        if self.host_filter:
            filter_status.append(f"host: {self.host_filter}")
        filter_text = f" | Filter: {', '.join(filter_status)}" if filter_status else ""

        if terminal_width < 100:
            subtitle = f"{self.current_page}/{total_pages} [{self.total}]{filter_text}"
        else:
            subtitle = f"Page {self.current_page}/{total_pages} [{self.total} total]{filter_text}"

        # Custom title for selection mode
        title = (
            f"[bold white]{self.custom_title}[/]"
            if self.custom_title
            else "[bold white]HOST USERS[/] - Admin vs Regular Access"
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
        num_rows = len(self._cached_users)

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
        elif key == "a" and not self.selection_mode:
            self.filters = {"admin_only": True}
            self.current_page = 1
            return True
        elif key == "U" and not self.selection_mode:  # Shift+U for user only
            self.filters = {"user_only": True}
            self.current_page = 1
            return True
        elif key == "x" and not self.selection_mode:
            self.filters = {}
            self.host_filter = ""
            self.current_page = 1
            return True
        return False

    def get_help(self) -> str:
        """Return help text for this page."""
        if self.selection_mode:
            return "[↑/↓] Select | [Enter] Confirm | [q] Cancel"
        return "[←/→] Page | [↑/↓] Select | [a] Admins | [U] Users | [x] Clear"

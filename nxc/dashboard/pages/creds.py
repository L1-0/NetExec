"""Credentials page - credential inventory."""

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


class CredsPage:
    """Page 3: Credentials - Credential inventory with deduplication."""

    name = "Creds"
    key = "3"

    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.current_page = 1
        self.page_size = config.get("page_size", 20)
        self.filters = {}
        self.total = 0
        self.unmask = config.get("unmask", False)

        # Selection mode
        self.selection_mode = False
        self.selected_row = 0
        self.custom_title = None
        self._cached_creds = []

        # Define responsive columns - Username and Secret are critical
        # For hashes, we need enough space (65 chars for full NTLM)
        # At narrow widths, hide Domain/Source/Type to fit the hash
        self.columns = [
            ResponsiveColumn("ID", "id", 4, PRIORITY_LOW, style="dim"),
            ResponsiveColumn("Domain", "domain", 12, PRIORITY_LOW, overflow="crop"),
            ResponsiveColumn(
                "Username",
                "username",
                16,
                PRIORITY_CRITICAL,
                style="cyan",
                overflow="crop",
            ),
            ResponsiveColumn(
                "Secret", "password", None, PRIORITY_CRITICAL, no_wrap=True
            ),
            ResponsiveColumn("Type", "credtype", 9, PRIORITY_MEDIUM),
            ResponsiveColumn("Source", "source", 6, PRIORITY_LOW),
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

    def get_selected_cred(self) -> dict:
        """Get the currently selected credential data."""
        if self._cached_creds and 0 <= self.selected_row < len(self._cached_creds):
            return self._cached_creds[self.selected_row]
        return None

    def render(self, console) -> Panel:
        """Render the credentials page."""
        page_size = self._get_page_size(console)
        creds, self.total = self.db.get_credentials(
            self.current_page, page_size, self.filters
        )
        self._cached_creds = creds  # Cache for selection
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
                col.name,
                style=col.style,
                width=col.width,
                justify=col.justify,
                no_wrap=getattr(col, "no_wrap", False),
                overflow=getattr(col, "overflow", "ellipsis"),
            )

        for idx, cred in enumerate(creds):
            row_values = []
            is_selected = self.selection_mode and idx == self.selected_row

            for col in visible_cols:
                value = cred.get(col.key, "")

                # Special handling for secret masking
                if col.key == "password":
                    value = self._mask_secret(value)

                # Special styling for type/source
                if col.key == "credtype":
                    cred_type = str(value) if value else ""
                    if is_selected:
                        value = Text(cred_type, style="reverse")
                    else:
                        style = "green" if cred_type == "plaintext" else "yellow"
                        value = Text(cred_type, style=style)
                elif col.key == "source":
                    source = str(value) if value else ""
                    if is_selected:
                        value = Text(source, style="reverse")
                    else:
                        style = "cyan" if source == "used" else "magenta"
                        value = Text(source, style=style)
                else:
                    formatted = (
                        col.formatter(value) if col.formatter else str(value or "")
                    )
                    if is_selected:
                        value = Text(formatted, style="reverse")
                    else:
                        value = formatted

                row_values.append(value)

            table.add_row(*row_values)

        # Filter status
        filter_status = []
        if self.filters.get("plaintext"):
            filter_status.append("plaintext")
        if self.filters.get("hash"):
            filter_status.append("hash")
        filter_text = f" | Filter: {', '.join(filter_status)}" if filter_status else ""
        mask_status = "[unmasked]" if self.unmask else "[masked]"

        if terminal_width < 100:
            subtitle = f"{self.current_page}/{total_pages} [{self.total}] {mask_status}{filter_text}"
        else:
            subtitle = f"Page {self.current_page}/{total_pages} [{self.total} total] {mask_status}{filter_text}"

        # Custom title for selection mode
        title = (
            f"[bold yellow]{self.custom_title}[/]"
            if self.custom_title
            else "[bold white]CREDENTIALS[/]"
        )
        border = "yellow" if self.selection_mode else "blue"

        return Panel(
            table,
            title=title,
            subtitle=subtitle,
            border_style=border,
        )

    def handle_key(self, key: str, console=None) -> bool:
        """Handle page-specific key presses."""
        page_size = self._get_page_size(console) if console else self.page_size
        total_pages = max(1, (self.total + page_size - 1) // page_size)

        # Selection mode navigation
        if self.selection_mode:
            max_row = len(self._cached_creds) - 1
            if key in ("up", "w"):
                if self.selected_row > 0:
                    self.selected_row -= 1
                return True
            elif key in ("down", "s"):
                if self.selected_row < max_row:
                    self.selected_row += 1
                return True
            elif key == "\r":  # Enter - signal selection made
                return "selected"
            elif key in ("q", "escape"):
                self.exit_selection_mode()
                return "cancelled"
        else:
            # Up/Down arrow enters selection mode from top or bottom
            max_row = len(self._cached_creds) - 1
            if key == "down" and max_row >= 0:
                self.selected_row = 0  # Start from top
                return "enter_selection"
            elif key == "up" and max_row >= 0:
                self.selected_row = max_row  # Start from bottom
                return "enter_selection"

        # Left/Right for data page navigation
        if key in ("right", "l"):
            if self.current_page < total_pages:
                self.current_page += 1
            return True
        elif key in ("left", "h"):
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
        elif key == "p":
            self.filters = {"plaintext": True}
            self.current_page = 1
            return True
        elif key == "H":  # Shift+H for hash filter
            self.filters = {"hash": True}
            self.current_page = 1
            return True
        elif key == "x":
            self.filters = {}
            self.current_page = 1
            return True
        return False

    def get_help(self) -> str:
        """Return help text for this page."""
        if self.selection_mode:
            return "[↑/↓] Select | [Enter] Confirm | [q] Cancel"
        return (
            "[←/→] Page | [↑/↓] Select | [u] Unmask | [p] Plain | [H] Hash | [x] Clear"
        )

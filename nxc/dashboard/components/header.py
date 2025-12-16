"""Header and Footer components for dashboard."""

from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.console import RenderableType
from datetime import datetime


class Header:
    """Dashboard header component."""

    def __init__(self, workspace: str = "default"):
        self.workspace = workspace
        self.current_page = 1
        self.domains = []  # Discovered domains
        self.terminal_width = 120  # Default, updated on render
        # Page names in order: 1-9
        self.page_names = [
            "Overview",  # 1
            "Hosts",  # 2
            "Creds",  # 3
            "Groups",  # 4
            "Shares",  # 5
            "DPAPI",  # 6
            "WCC",  # 7
            "PassPol",  # 8
            "Logs",  # 9
        ]
        # Short names for narrow terminals
        self.page_names_short = [
            "Ovw",  # 1
            "Hst",  # 2
            "Crd",  # 3
            "Grp",  # 4
            "Shr",  # 5
            "DPA",  # 6
            "WCC",  # 7
            "Pol",  # 8
            "Log",  # 9
        ]
        # Key labels for tabs (1-9)
        self.page_keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]

    def render(self, terminal_width: int = 120) -> Text:
        """Render the header with page tabs."""
        self.terminal_width = terminal_width
        header = Text()

        # Title line - adaptive based on width
        header.append(" 🕷 NetExec Dashboard ", style="bold cyan")

        # On wide screens show workspace, on narrow show domains instead
        if terminal_width >= 100:
            header.append(" | ", style="dim")
            # Use full "Workspace" on wide screens, "WS" on medium
            ws_label = "Workspace" if terminal_width >= 120 else "WS"
            header.append(f"{ws_label}: {self.workspace}", style="yellow")

            # Show domains on same line if space permits
            if self.domains and terminal_width >= 140:
                header.append(" | ", style="dim")
                header.append("Domains: ", style="white")
                self._append_domains(header, self.domains[:3])
                if len(self.domains) > 3:
                    header.append(f" (+{len(self.domains) - 3})", style="dim")

        header.append("\n")

        # Show domains on second line for medium width or if many domains
        if self.domains and 80 <= terminal_width < 140:
            header.append("  ")
            header.append("Domains: ", style="dim")
            self._append_domains(header, self.domains[:5], style="magenta dim")
            if len(self.domains) > 5:
                header.append(f" (+{len(self.domains) - 5})", style="dim")
            header.append("\n")

        header.append("\n  ")

        # Page tabs - use short names on narrow screens
        use_short = terminal_width < 100
        names = self.page_names_short if use_short else self.page_names

        for i, name in enumerate(names):
            key = self.page_keys[i]
            page_num = i + 1  # 1-based page number
            if page_num == self.current_page:
                header.append(f"[{key}]{name}", style="bold white on blue")
            else:
                header.append(f"[{key}]{name}", style="dim")
            header.append(" ", style="")

        header.append("\n")

        return header

    def _append_domains(self, text: Text, domains: list, style: str = "magenta"):
        """Append domains with grey comma separators."""
        for i, domain in enumerate(domains):
            if i > 0:
                text.append(", ", style="dim")  # Grey comma
            text.append(domain, style=style)

    def set_page(self, page: int):
        """Set the current page."""
        self.current_page = page

    def set_domains(self, domains: list):
        """Set the discovered domains."""
        self.domains = domains if domains else []


class Footer:
    """Dashboard footer component."""

    def __init__(self):
        self.help_text = ""
        self.status = ""

    def render(self) -> Text:
        """Render the footer with navigation help."""
        footer = Text()
        footer.append("\n  ")

        # Page-specific help
        if self.help_text:
            footer.append(self.help_text, style="dim")
            footer.append(" | ", style="dim")

        # Global shortcuts
        footer.append("[1-9] Tab", style="cyan")
        footer.append(" | ", style="dim")
        footer.append("[←/→] Tab", style="cyan")
        footer.append(" | ", style="dim")
        footer.append("[r] Refresh", style="cyan")
        footer.append(" | ", style="dim")
        footer.append("[?] Help", style="cyan")
        footer.append(" | ", style="dim")
        footer.append("[q] Quit", style="red")

        # Status
        if self.status:
            footer.append(f"\n  {self.status}", style="yellow")

        return footer

    def set_help(self, text: str):
        """Set page-specific help text."""
        self.help_text = text

    def set_status(self, text: str):
        """Set status message."""
        self.status = text


class HelpPanel:
    """Help panel overlay."""

    @staticmethod
    def render() -> Panel:
        """Render the help panel."""
        help_text = Text()
        help_text.append("  KEYBOARD SHORTCUTS\n\n", style="bold cyan")

        shortcuts = [
            ("1-9", "Jump to page"),
            ("←/→ or h/l", "Previous/Next tab"),
            ("↑/↓", "Previous/Next data page"),
            ("Enter", "Start selection mode"),
            ("g", "Go to first page"),
            ("G", "Go to last page"),
            ("r", "Refresh data"),
            ("u", "Toggle unmask secrets"),
            ("/", "Search (where available)"),
            ("f", "Filter menu"),
            ("x", "Clear filters"),
            ("e", "Export current view"),
            ("?", "Toggle this help"),
            ("q", "Quit dashboard"),
        ]

        for key, desc in shortcuts:
            help_text.append(f"  {key:15}", style="yellow")
            help_text.append(f" {desc}\n", style="white")

        help_text.append("\n  PAGE INDICATORS\n\n", style="bold cyan")
        help_text.append("  S=SMB  L=LDAP  W=WINRM  M=MSSQL  R=RDP\n", style="dim")
        help_text.append("  H=SSH  F=FTP   V=VNC    N=NFS    I=WMI\n", style="dim")

        return Panel(
            help_text,
            title="[bold white]Help[/]",
            border_style="green",
        )

"""Overview page - workspace status and counts."""

from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.console import Group
from rich.align import Align
from rich import box
from datetime import datetime
import importlib.metadata


def get_version_info() -> dict:
    """Get NetExec version info."""
    try:
        full_version = importlib.metadata.version("netexec")
        try:
            version, commit_info = full_version.split("+")
            distance, commit = commit_info.split(".")
        except ValueError:
            version = full_version
            commit = ""
            distance = ""
        return {
            "version": version,
            "codename": "SmoothOperator",
            "commit": commit,
            "distance": distance,
        }
    except Exception:
        return {
            "version": "dev",
            "codename": "SmoothOperator",
            "commit": "",
            "distance": "",
        }


class OverviewPage:
    """Page 1: Overview - Quick status snapshot."""

    name = "Overview"
    key = "1"

    def __init__(self, db, config):
        self.db = db
        self.config = config
        self._last_refresh = None

    def _render_stats_content(self, counts, diff, protocols) -> Text:
        """Render the left content with basic stats."""
        content = Text()
        content.append("Active Protocols: ", style="bold")
        content.append(
            ", ".join([p.upper() for p in protocols]) if protocols else "None",
            style="cyan",
        )
        content.append("\n\n")

        # Stats table as text
        content.append("Category       Count  New\n", style="bold magenta")
        content.append("─" * 27 + "\n", style="dim")

        categories = [
            ("Hosts", "hosts"),
            ("Pwned Hosts", "pwned_hosts"),
            ("Credentials", "creds"),
            ("Shares", "shares"),
            ("Groups", "groups"),
            ("DPAPI", "dpapi"),
            ("WCC Checks", "wcc"),
            ("Admin Users", "users_admin"),
        ]

        for label, key in categories:
            count = counts.get(key, 0)
            delta = diff.get(key, 0)
            delta_style = "green" if delta > 0 else ("red" if delta < 0 else "dim")
            delta_text = f"+{delta}" if delta > 0 else str(delta)
            content.append(f"{label:<13}", style="white")
            content.append(f"{count:>5}", style="cyan")
            content.append(f"  ")
            content.append(f"{delta_text:>4}\n", style=delta_style)

        return content

    def _render_analytics_content(
        self, analytics, max_name_len: int = 30, available_lines: int = 30
    ) -> Text:
        """Render the right content with advanced analytics (dynamic based on height)."""
        content = Text()
        lines_used = 0

        # === Security Posture ===
        content.append("SECURITY POSTURE\n", style="bold yellow")
        lines_used += 1

        total_hosts = analytics.get("total_hosts", 0)
        total_wcc = analytics.get("total_wcc_checks", 0)

        pwn_rate = analytics.get("pwn_rate", 0)
        pwn_color = "red" if pwn_rate > 50 else ("yellow" if pwn_rate > 20 else "green")
        content.append("  Compromised: ", style="dim")
        content.append(f"{pwn_rate:.1f}%", style=f"bold {pwn_color}")
        content.append(f" of {total_hosts} Hosts\n", style="dim")
        lines_used += 1

        wcc = analytics.get("wcc_compliance", 0)
        wcc_color = "green" if wcc > 80 else ("yellow" if wcc > 50 else "red")
        content.append("  WCC Compliance: ", style="dim")
        content.append(f"{wcc:.1f}%", style=f"bold {wcc_color}")
        content.append(f" of {total_wcc} checks\n", style="dim")
        lines_used += 1

        signing = analytics.get("signing_disabled", 0)
        content.append("  Hosts without SMB signing: ", style="dim")
        if signing > 0:
            content.append(f"{signing}\n", style="bold red")
        else:
            content.append("0\n", style="green")
        lines_used += 1
        content.append("\n")

        # === Credential Intelligence ===
        content.append("CREDENTIAL INTEL\n", style="bold yellow")
        lines_used += 2

        cred_types = analytics.get("cred_types", {})
        content.append("  Plaintext: ", style="dim")
        content.append(f"{cred_types.get('plaintext', 0)}", style="green")
        content.append("  Hash: ", style="dim")
        content.append(f"{cred_types.get('hash', 0)}", style="cyan")
        content.append("  Ticket: ", style="dim")
        content.append(f"{cred_types.get('ticket', 0)}", style="magenta")

        reuse = analytics.get("cred_reuse_rate", 0)
        if reuse > 0:
            content.append("   Reuse: ", style="dim")
            content.append(f"{reuse:.1f}%", style="yellow")

        unique_pw = analytics.get("unique_passwords", 0)
        if unique_pw > 0:
            content.append("   Unique: ", style="dim")
            content.append(f"{unique_pw}", style="cyan")
        content.append("\n")
        lines_used += 1

        # Password spraying candidates (if space)
        spray = analytics.get("password_spraying_candidates", [])
        if spray and lines_used < available_lines - 8:
            content.append("  Spray Candidates: ", style="dim")
            for i, p in enumerate(spray[:3]):
                if i > 0:
                    content.append(", ", style="dim")
                content.append(f"{p[0]}", style="red")
                content.append(f" ({p[1]})", style="yellow")
            content.append("\n")
            lines_used += 1

        content.append("\n")

        # === Attack Surface ===
        content.append("ATTACK SURFACE\n", style="bold yellow")
        lines_used += 2

        dc_count = analytics.get("dc_count", 0)
        content.append("  DCs: ", style="dim")
        content.append(f"{dc_count}", style="bold cyan")

        attack_paths = analytics.get("attack_paths", 0)
        content.append("   Attack Paths: ", style="dim")
        content.append(f"{attack_paths}", style="bold magenta")

        avg_admin = analytics.get("avg_admins_per_host", 0)
        content.append("   Avg Admins/Host: ", style="dim")
        content.append(f"{avg_admin:.1f}\n", style="cyan")
        lines_used += 1

        content.append("\n")

        # === Top Admin Users (dynamic count based on space) ===
        top_admins = analytics.get("top_admin_users", [])
        if top_admins:
            content.append("TOP ADMINS\n", style="bold yellow")
            lines_used += 2
            # Dynamic: show more if we have space
            max_admins = min(
                len(top_admins), max(2, (available_lines - lines_used) // 3)
            )
            for admin in top_admins[:max_admins]:
                if lines_used >= available_lines - 6:
                    break
                user = admin.get("user", "")
                domain = admin.get("domain", "")
                hosts = admin.get("hosts", 0)
                display = f"{domain}\\{user}" if domain else user
                if len(display) > max_name_len:
                    display = display[: max_name_len - 3] + "..."
                content.append(f"  {display}: ", style="white")
                content.append(f"{hosts}\n", style="green")
                lines_used += 1
            content.append("\n")

        # === High Value Targets (dynamic) ===
        hvt = analytics.get("high_value_targets", [])
        if hvt and lines_used < available_lines - 5:
            content.append("HIGH VALUE TARGETS\n", style="bold yellow")
            lines_used += 2
            max_hvt = min(len(hvt), max(2, (available_lines - lines_used) // 3))
            for target in hvt[:max_hvt]:
                if lines_used >= available_lines - 4:
                    break
                host = target.get("host", "")
                admins = target.get("admins", 0)
                content.append(f"  {host}: ", style="white")
                content.append(f"{admins}\n", style="red")
                lines_used += 1
            content.append("\n")

        # === Share Analysis (if space) ===
        shares = analytics.get("share_access", {})
        total_shares = sum(shares.values())
        if total_shares > 0 and lines_used < available_lines - 3:
            content.append("SHARE ACCESS\n", style="bold yellow")
            content.append("  Write: ", style="white")
            content.append(f"{shares.get('write', 0)}", style="red bold")
            content.append("  Read: ", style="white")
            content.append(f"{shares.get('read', 0)}", style="yellow")
            content.append("  None: ", style="white")
            content.append(f"{shares.get('none', 0)}\n", style="dim")
            lines_used += 2

        # === Domain Coverage (if space) ===
        domains = analytics.get("domain_coverage", {})
        if domains and lines_used < available_lines - 3:
            content.append("\n")
            content.append("DOMAIN COVERAGE\n", style="bold yellow")
            for i, (d, c) in enumerate(list(domains.items())[:4]):
                if i > 0:
                    content.append(", ", style="white")
                content.append(f"{d}", style="cyan")
                content.append(": ", style="white")
                content.append(f"{c}", style="white")
            content.append("\n")
            lines_used += 3

        # === WCC Vulnerabilities (dynamic count) ===
        wcc_vulns = analytics.get("wcc_vulnerabilities", {})
        if wcc_vulns and lines_used < available_lines - 2:
            content.append("\n")
            content.append("SECURITY ISSUES (WCC)\n", style="bold red")
            lines_used += 2
            sorted_vulns = sorted(wcc_vulns.items(), key=lambda x: x[1], reverse=True)
            # Dynamic: show more vulns if we have space
            max_vulns = min(len(sorted_vulns), max(3, available_lines - lines_used))
            for vuln_name, count in sorted_vulns[:max_vulns]:
                if lines_used >= available_lines:
                    break
                if "ADCS" in vuln_name or "ESC" in vuln_name:
                    style = "bold red"
                elif "Signing" in vuln_name or "NTLMv1" in vuln_name:
                    style = "red"
                elif "Spooler" in vuln_name or "WebClient" in vuln_name:
                    style = "yellow"
                elif "LLMNR" in vuln_name or "NBT-NS" in vuln_name:
                    style = "yellow"
                else:
                    style = "white"
                content.append(f"  {vuln_name}: ", style="dim")
                content.append(f"{count}\n", style=style)
                lines_used += 1
        elif not wcc_vulns:
            # Fallback to protocol detection if no WCC data
            vuln = analytics.get("vulnerable_protocols", [])
            if vuln and lines_used < available_lines - 2:
                content.append("\n")
                content.append("RISKS  ", style="bold red")
                content.append(" | ".join(vuln[:5]) + "\n", style="yellow")

        return content

    def _render_info_panel(self, width: int) -> Panel:
        """Render the NetExec info panel."""
        ver = get_version_info()
        info = Text(justify="center")
        info.append("NetExec", style="bold cyan")
        info.append(f" v{ver['version']}", style="yellow")
        if ver["codename"]:
            info.append(f" - {ver['codename']}", style="magenta")
        info.append("\n")
        if ver["commit"] and ver["distance"]:
            info.append(f"{ver['commit']} - {ver['distance']}\n", style="dim")
        info.append("github.com/Pennyw0rth/NetExec", style="dim")

        return Panel(
            Align.center(info),
            title="[bold white]Info[/]",
            border_style="dim",
            padding=(0, 1),
            width=width,
        )

    def render(self, console) -> Panel:
        """Render the overview page with two columns."""
        counts = self.db.get_counts()
        diff = self.db.get_diff_counts()
        protocols = self.db.get_active_protocols()
        analytics = self.db.get_analytics()
        self._last_refresh = datetime.now()

        # Get terminal dimensions for responsive layout
        width = console.size.width if hasattr(console, "size") else 120
        height = console.size.height if hasattr(console, "size") else 24

        # Calculate available lines for analytics panel content
        # Header(4) + Footer(2) + Panel borders(4) + padding + extra = ~13 lines overhead
        available_lines = max(10, height - 13)

        # Dynamic split: stats panel is wider (35%), analysis gets rest
        # Gap between panels = 1
        left_width = max(38, int((width - 4) * 0.35))
        right_width = max(50, width - left_width - 4)

        # Calculate max name length for truncation based on right panel width
        max_name_len = right_width - 15

        # Create content for both sides
        left_content = self._render_stats_content(counts, diff, protocols)
        right_content = self._render_analytics_content(
            analytics, max_name_len, available_lines
        )

        # Create panels
        stats_panel = Panel(
            left_content,
            title="[bold cyan]Statistics[/]",
            border_style="cyan",
            padding=(0, 1),
            width=left_width,
        )

        # Info panel below stats
        info_panel = self._render_info_panel(left_width)

        # Stack stats and info vertically
        left_stack = Group(stats_panel, info_panel)

        right_panel = Panel(
            right_content,
            title="[bold magenta]Analysis[/]",
            border_style="magenta",
            padding=(0, 1),
            width=right_width,
        )

        # Use Columns for side-by-side layout with minimal gap
        columns = Columns([left_stack, right_panel], expand=False, padding=(0, 0))

        return Panel(
            columns,
            title=f"[bold white]OVERVIEW[/] - Workspace: [cyan]{self.db.workspace}[/]",
            subtitle=f"Last Refresh: {self._last_refresh.strftime('%Y-%m-%d %H:%M:%S')}"
            if self._last_refresh
            else "",
            border_style="blue",
        )

    def handle_key(self, key: str, console=None) -> bool:
        """Handle page-specific key presses. Returns True if handled."""
        return False

    def get_help(self) -> str:
        """Return help text for this page."""
        return "[r] Refresh data"

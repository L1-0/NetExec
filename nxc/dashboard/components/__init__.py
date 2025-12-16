"""Dashboard components package."""

from nxc.dashboard.components.paginator import Paginator
from nxc.dashboard.components.header import Header, Footer
from nxc.dashboard.components.responsive import (
    ResponsiveTable,
    ResponsiveColumn,
    PRIORITY_CRITICAL,
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
    PRIORITY_LOW,
)

__all__ = [
    "Paginator",
    "Header",
    "Footer",
    "ResponsiveTable",
    "ResponsiveColumn",
    "PRIORITY_CRITICAL",
    "PRIORITY_HIGH",
    "PRIORITY_MEDIUM",
    "PRIORITY_LOW",
]

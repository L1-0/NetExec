"""Dashboard pages package."""

from nxc.dashboard.pages.overview import OverviewPage
from nxc.dashboard.pages.hosts import HostsPage
from nxc.dashboard.pages.creds import CredsPage
from nxc.dashboard.pages.shares import SharesPage
from nxc.dashboard.pages.groups import GroupsPage
from nxc.dashboard.pages.dpapi import DPAPIPage
from nxc.dashboard.pages.wcc import WCCPage
from nxc.dashboard.pages.logs import LogsPage
from nxc.dashboard.pages.passpol import PassPolPage

__all__ = [
    "OverviewPage",
    "HostsPage",
    "CredsPage",
    "SharesPage",
    "GroupsPage",
    "DPAPIPage",
    "WCCPage",
    "LogsPage",
    "PassPolPage",
]

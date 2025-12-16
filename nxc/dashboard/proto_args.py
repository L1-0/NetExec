"""Dashboard CLI argument parser."""

import argparse


def add_dashboard_parser(subparsers, std_parser=None):
    """Add dashboard subparser to the main argument parser."""
    dashboard_parser = subparsers.add_parser(
        "dashboard",
        help="Interactive TUI dashboard for nxcdb data",
        description="Launch an interactive terminal dashboard to view collected data from all protocol databases.",
    )

    dashboard_parser.add_argument(
        "-w",
        "--workspace",
        default="default",
        help="Workspace to use (default: default)",
    )
    dashboard_parser.add_argument(
        "-s",
        "--page-size",
        type=int,
        default=20,
        help="Number of rows per page (default: 20)",
    )
    dashboard_parser.add_argument(
        "-r",
        "--refresh",
        type=int,
        default=0,
        help="Auto-refresh interval in seconds, 0 to disable (default: 0)",
    )
    dashboard_parser.add_argument(
        "-l",
        "--log-file",
        type=str,
        default=None,
        help="Log file to tail (default: auto-detect)",
    )
    dashboard_parser.add_argument(
        "-u",
        "--unmask",
        action="store_true",
        help="Show secrets (credentials/dpapi) unmasked",
    )
    dashboard_parser.add_argument(
        "-p",
        "--start-page",
        type=int,
        choices=range(1, 10),
        default=1,
        metavar="PAGE",
        help="Start on specific page 1-9 (default: 1)",
    )
    dashboard_parser.add_argument(
        "--demo",
        action="store_true",
        help="Populate workspace with GOAD lab demo data",
    )
    dashboard_parser.add_argument(
        "--demo-clear",
        action="store_true",
        help="Clear demo data from workspace",
    )

    return dashboard_parser

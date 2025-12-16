"""
GOAD Lab Demo Data Generator for NetExec Dashboard.

This module populates the dashboard with realistic data from the
Game of Active Directory (GOAD) lab for demonstration purposes.

To remove: Simply delete this file and remove the --demo flag handling
from proto_args.py and app.py.
"""

import os
import sqlite3
from os.path import join as path_join, exists

from nxc.paths import WORKSPACE_DIR


# =============================================================================
# GOAD LAB DATA
# =============================================================================

GOAD_DOMAINS = {
    "sevenkingdoms.local": {
        "netbios": "SEVENKINGDOMS",
        "dc": "kingslanding",
        "dc_ip": "192.168.56.10",
    },
    "north.sevenkingdoms.local": {
        "netbios": "NORTH",
        "dc": "winterfell",
        "dc_ip": "192.168.56.11",
    },
    "essos.local": {
        "netbios": "ESSOS",
        "dc": "meereen",
        "dc_ip": "192.168.56.12",
    },
}

GOAD_HOSTS = [
    # ==========================================================================
    # WINDOWS HOSTS (Domain Controllers & Member Servers)
    # ==========================================================================
    # DC01 - King's Landing (Primary DC, SEVENKINGDOMS)
    {
        "ip": "192.168.56.10",
        "hostname": "KINGSLANDING",
        "domain": "sevenkingdoms.local",
        "os": "Windows Server 2019 Standard",
        "dc": True,
        "signing": True,
        "smbv1": False,
        "protocols": ["smb", "ldap", "winrm", "wmi", "rdp"],
    },
    # DC02 - Winterfell (Primary DC, NORTH)
    {
        "ip": "192.168.56.11",
        "hostname": "WINTERFELL",
        "domain": "north.sevenkingdoms.local",
        "os": "Windows Server 2019 Standard",
        "dc": True,
        "signing": True,
        "smbv1": False,
        "protocols": ["smb", "ldap", "winrm", "wmi", "rdp"],
    },
    # SRV02 - Castel Black (Member Server, NORTH)
    {
        "ip": "192.168.56.22",
        "hostname": "CASTELBLACK",
        "domain": "north.sevenkingdoms.local",
        "os": "Windows Server 2019 Standard",
        "dc": False,
        "signing": False,
        "smbv1": False,
        "protocols": ["smb", "winrm", "mssql", "wmi", "rdp"],
    },
    # DC03 - Meereen (Primary DC, ESSOS)
    {
        "ip": "192.168.56.12",
        "hostname": "MEEREEN",
        "domain": "essos.local",
        "os": "Windows Server 2019 Standard",
        "dc": True,
        "signing": True,
        "smbv1": False,
        "protocols": ["smb", "ldap", "winrm", "wmi", "rdp"],
    },
    # SRV03 - Braavos (Member Server, ESSOS)
    {
        "ip": "192.168.56.23",
        "hostname": "BRAAVOS",
        "domain": "essos.local",
        "os": "Windows Server 2019 Standard",
        "dc": False,
        "signing": False,
        "smbv1": True,  # Legacy SMBv1 enabled for exploitation
        "protocols": ["smb", "winrm", "mssql", "wmi", "rdp", "vnc"],
    },
    # ==========================================================================
    # LINUX HOSTS (Jump hosts, File servers, Web servers)
    # ==========================================================================
    # The Wall - Linux jump host
    {
        "ip": "192.168.56.30",
        "hostname": "thewall",
        "domain": "",
        "os": "Ubuntu 22.04 LTS",
        "dc": False,
        "signing": False,
        "smbv1": False,
        "protocols": ["ssh", "ftp"],
        "banner": "OpenSSH_8.9p1 Ubuntu-3ubuntu0.6",
    },
    # Dragonstone - Linux NFS/File server
    {
        "ip": "192.168.56.31",
        "hostname": "dragonstone",
        "domain": "",
        "os": "Debian 12",
        "dc": False,
        "signing": False,
        "smbv1": False,
        "protocols": ["ssh", "nfs", "ftp"],
        "banner": "OpenSSH_9.2p1 Debian-2+deb12u2",
    },
    # Pyke - CentOS web server
    {
        "ip": "192.168.56.32",
        "hostname": "pyke",
        "domain": "",
        "os": "CentOS Stream 9",
        "dc": False,
        "signing": False,
        "smbv1": False,
        "protocols": ["ssh"],
        "banner": "OpenSSH_8.7p1",
    },
    # Oldtown - Citadel library server (legacy)
    {
        "ip": "192.168.56.33",
        "hostname": "oldtown",
        "domain": "",
        "os": "CentOS 7",
        "dc": False,
        "signing": False,
        "smbv1": False,
        "protocols": ["ssh", "ftp", "vnc"],
        "banner": "OpenSSH_7.4p1",
    },
]

GOAD_USERS = [
    # SEVENKINGDOMS domain users
    {
        "domain": "SEVENKINGDOMS",
        "username": "tywin.lannister",
        "password": "powerkingftw135",
        "credtype": "plaintext",
    },
    {
        "domain": "SEVENKINGDOMS",
        "username": "jaime.lannister",
        "password": "cersei",
        "credtype": "plaintext",
    },
    {
        "domain": "SEVENKINGDOMS",
        "username": "cersei.lannister",
        "password": "il0vejaime",
        "credtype": "plaintext",
    },
    {
        "domain": "SEVENKINGDOMS",
        "username": "tyron.lannister",
        "password": "Alc00L&S3x",
        "credtype": "plaintext",
    },
    {
        "domain": "SEVENKINGDOMS",
        "username": "robert.baratheon",
        "password": "iamthekingoftheworld",
        "credtype": "plaintext",
    },
    {
        "domain": "SEVENKINGDOMS",
        "username": "joffrey.baratheon",
        "password": "1killerlion",
        "credtype": "plaintext",
    },
    {
        "domain": "SEVENKINGDOMS",
        "username": "renly.baratheon",
        "password": "lorastyrell",
        "credtype": "plaintext",
    },
    {
        "domain": "SEVENKINGDOMS",
        "username": "stannis.baratheon",
        "password": "Drag0nst0ne",
        "credtype": "plaintext",
    },
    {
        "domain": "SEVENKINGDOMS",
        "username": "petyer.baelish",
        "password": "@littlefinger@",
        "credtype": "plaintext",
    },
    {
        "domain": "SEVENKINGDOMS",
        "username": "lord.varys",
        "password": "_W1sper_$",
        "credtype": "plaintext",
    },
    {
        "domain": "SEVENKINGDOMS",
        "username": "maester.pycelle",
        "password": "MaesterOfMaesters",
        "credtype": "plaintext",
    },
    # NORTH domain users
    {
        "domain": "NORTH",
        "username": "arya.stark",
        "password": "Needle",
        "credtype": "plaintext",
    },
    {
        "domain": "NORTH",
        "username": "eddard.stark",
        "password": "FightP3aceAndHonor!",
        "credtype": "plaintext",
    },
    {
        "domain": "NORTH",
        "username": "catelyn.stark",
        "password": "robbsansabradonaryarickon",
        "credtype": "plaintext",
    },
    {
        "domain": "NORTH",
        "username": "robb.stark",
        "password": "sexywolfy",
        "credtype": "plaintext",
    },
    {
        "domain": "NORTH",
        "username": "sansa.stark",
        "password": "345ertdfg",
        "credtype": "plaintext",
    },
    {
        "domain": "NORTH",
        "username": "brandon.stark",
        "password": "iseedeadpeople",
        "credtype": "plaintext",
    },
    {
        "domain": "NORTH",
        "username": "rickon.stark",
        "password": "Winter2022",
        "credtype": "plaintext",
    },
    {
        "domain": "NORTH",
        "username": "hodor",
        "password": "hodor",
        "credtype": "plaintext",
    },
    {
        "domain": "NORTH",
        "username": "jon.snow",
        "password": "iknownothing",
        "credtype": "plaintext",
    },
    {
        "domain": "NORTH",
        "username": "samwell.tarly",
        "password": "Heartsbane",
        "credtype": "plaintext",
    },
    {
        "domain": "NORTH",
        "username": "jeor.mormont",
        "password": "_L0ngCl@w_",
        "credtype": "plaintext",
    },
    {
        "domain": "NORTH",
        "username": "sql_svc",
        "password": "YouWillNotKerboroast1ngMeeeeee",
        "credtype": "plaintext",
    },
    # ESSOS domain users
    {
        "domain": "ESSOS",
        "username": "daenerys.targaryen",
        "password": "BurnThemAll!",
        "credtype": "plaintext",
    },
    {
        "domain": "ESSOS",
        "username": "viserys.targaryen",
        "password": "GoldCrown",
        "credtype": "plaintext",
    },
    {
        "domain": "ESSOS",
        "username": "khal.drogo",
        "password": "horse",
        "credtype": "plaintext",
    },
    {
        "domain": "ESSOS",
        "username": "jorah.mormont",
        "password": "H0nnor!",
        "credtype": "plaintext",
    },
    {
        "domain": "ESSOS",
        "username": "missandei",
        "password": "fr3edom",
        "credtype": "plaintext",
    },
    {
        "domain": "ESSOS",
        "username": "drogon",
        "password": "Dracarys",
        "credtype": "plaintext",
    },
    {
        "domain": "ESSOS",
        "username": "sql_svc",
        "password": "YouWillNotKerboroast1ngMeeeeee",
        "credtype": "plaintext",
    },
    # Some hashes for variety
    {
        "domain": "SEVENKINGDOMS",
        "username": "Administrator",
        "password": "aad3b435b51404eeaad3b435b51404ee:8dCT-DJjgScp",
        "credtype": "hash",
    },
    {
        "domain": "NORTH",
        "username": "Administrator",
        "password": "aad3b435b51404eeaad3b435b51404ee:NgtI75cKV+Pu",
        "credtype": "hash",
    },
    {
        "domain": "ESSOS",
        "username": "Administrator",
        "password": "aad3b435b51404eeaad3b435b51404ee:Ufe-bVXSx9rk",
        "credtype": "hash",
    },
]

# =============================================================================
# LINUX CREDENTIALS (SSH, FTP)
# =============================================================================
LINUX_USERS = [
    # The Wall - Jump host users
    {
        "host": "192.168.56.30",
        "username": "nightswatch",
        "password": "Castle!Black2024",
        "credtype": "plaintext",
        "shell": True,
        "root": False,
    },
    {
        "host": "192.168.56.30",
        "username": "root",
        "password": "N0rthRemembersRoot!",
        "credtype": "plaintext",
        "shell": True,
        "root": True,
    },
    {
        "host": "192.168.56.30",
        "username": "jonsnow",
        "password": "",
        "credtype": "key",
        "key_data": "-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXktdjEAAAAACmFlczI1Ni1jdHIAAAAGYmNyeXB0AAAAGAAA\nABCCwxVdR8RH...(truncated for demo)\n-----END OPENSSH PRIVATE KEY-----",
        "shell": True,
        "root": False,
    },
    # Dragonstone - File server
    {
        "host": "192.168.56.31",
        "username": "stannis",
        "password": "OneTrueKing!",
        "credtype": "plaintext",
        "shell": True,
        "root": False,
    },
    {
        "host": "192.168.56.31",
        "username": "davos",
        "password": "smuggler99",
        "credtype": "plaintext",
        "shell": True,
        "root": False,
    },
    {
        "host": "192.168.56.31",
        "username": "root",
        "password": "Dr4g0nst0n3R00t!",
        "credtype": "plaintext",
        "shell": True,
        "root": True,
    },
    # Pyke - Web server
    {
        "host": "192.168.56.32",
        "username": "theon",
        "password": "IronPrice!",
        "credtype": "plaintext",
        "shell": True,
        "root": False,
    },
    {
        "host": "192.168.56.32",
        "username": "euron",
        "password": "Kr4k3nRul3s",
        "credtype": "plaintext",
        "shell": True,
        "root": False,
    },
    # Oldtown - Legacy server
    {
        "host": "192.168.56.33",
        "username": "samwell",
        "password": "m4ester",
        "credtype": "plaintext",
        "shell": True,
        "root": False,
    },
    {
        "host": "192.168.56.33",
        "username": "archmaester",
        "password": "citadel123",
        "credtype": "plaintext",
        "shell": True,
        "root": True,
    },
]

# FTP specific data
FTP_CREDENTIALS = [
    {
        "host": "192.168.56.30",
        "port": 21,
        "banner": "vsFTPd 3.0.5",
        "username": "anonymous",
        "password": "",
    },
    {
        "host": "192.168.56.30",
        "port": 21,
        "banner": "vsFTPd 3.0.5",
        "username": "nightswatch",
        "password": "Castle!Black2024",
    },
    {
        "host": "192.168.56.31",
        "port": 21,
        "banner": "ProFTPD 1.3.8",
        "username": "davos",
        "password": "smuggler99",
    },
    {
        "host": "192.168.56.31",
        "port": 21,
        "banner": "ProFTPD 1.3.8",
        "username": "stannis",
        "password": "OneTrueKing!",
    },
    {
        "host": "192.168.56.33",
        "port": 21,
        "banner": "vsFTPd 2.3.5",
        "username": "samwell",
        "password": "m4ester",
    },
]

FTP_DIRECTORY_LISTINGS = [
    {
        "host": "192.168.56.30",
        "username": "anonymous",
        "listing": "drwxr-xr-x 2 ftp ftp 4096 Jan 15 10:00 pub\n-rw-r--r-- 1 ftp ftp 1234 Jan 10 09:00 welcome.txt",
    },
    {
        "host": "192.168.56.31",
        "username": "davos",
        "listing": "drwxr-x--- 3 davos users 4096 Feb 01 14:00 smuggled_goods\n-rw-r--r-- 1 davos users 5678 Jan 25 11:00 inventory.csv",
    },
]

# NFS specific data
NFS_EXPORTS = [
    {
        "host": "192.168.56.31",
        "port": 2049,
        "exports": [
            "/export/home - (rw,sync,no_root_squash)",
            "/export/shared - (ro,sync)",
            "/var/backups - (rw,sync,no_subtree_check)",
        ],
    },
]

# VNC specific data
VNC_HOSTS = [
    {
        "ip": "192.168.56.23",
        "hostname": "BRAAVOS",
        "port": 5900,
        "banner": "RFB 003.008",
        "username": "",
        "password": "faceless",  # VNC password
    },
    {
        "ip": "192.168.56.33",
        "hostname": "oldtown",
        "port": 5901,
        "banner": "RFB 003.007",
        "username": "",
        "password": "citadel",
    },
]

# RDP specific data
RDP_HOSTS = [
    {
        "ip": "192.168.56.10",
        "hostname": "KINGSLANDING",
        "port": 3389,
        "banner": "Windows Server 2019",
        "nla": True,
    },
    {
        "ip": "192.168.56.11",
        "hostname": "WINTERFELL",
        "port": 3389,
        "banner": "Windows Server 2019",
        "nla": True,
    },
    {
        "ip": "192.168.56.12",
        "hostname": "MEEREEN",
        "port": 3389,
        "banner": "Windows Server 2019",
        "nla": True,
    },
    {
        "ip": "192.168.56.22",
        "hostname": "CASTELBLACK",
        "port": 3389,
        "banner": "Windows Server 2019",
        "nla": False,  # NLA disabled
    },
    {
        "ip": "192.168.56.23",
        "hostname": "BRAAVOS",
        "port": 3389,
        "banner": "Windows Server 2019",
        "nla": False,  # NLA disabled
    },
]

# WMI specific data (uses same Windows creds as SMB/WinRM)

GOAD_SHARES = [
    # KINGSLANDING
    {
        "host": "192.168.56.10",
        "name": "ADMIN$",
        "remark": "Remote Admin",
        "read": False,
        "write": False,
    },
    {
        "host": "192.168.56.10",
        "name": "C$",
        "remark": "Default share",
        "read": True,
        "write": True,
    },
    {
        "host": "192.168.56.10",
        "name": "IPC$",
        "remark": "Remote IPC",
        "read": True,
        "write": False,
    },
    {
        "host": "192.168.56.10",
        "name": "NETLOGON",
        "remark": "Logon server share",
        "read": True,
        "write": False,
    },
    {
        "host": "192.168.56.10",
        "name": "SYSVOL",
        "remark": "Logon server share",
        "read": True,
        "write": False,
    },
    # WINTERFELL
    {
        "host": "192.168.56.11",
        "name": "ADMIN$",
        "remark": "Remote Admin",
        "read": False,
        "write": False,
    },
    {
        "host": "192.168.56.11",
        "name": "C$",
        "remark": "Default share",
        "read": True,
        "write": True,
    },
    {
        "host": "192.168.56.11",
        "name": "IPC$",
        "remark": "Remote IPC",
        "read": True,
        "write": False,
    },
    {
        "host": "192.168.56.11",
        "name": "NETLOGON",
        "remark": "Logon server share",
        "read": True,
        "write": False,
    },
    {
        "host": "192.168.56.11",
        "name": "SYSVOL",
        "remark": "Logon server share",
        "read": True,
        "write": False,
    },
    # CASTELBLACK
    {
        "host": "192.168.56.22",
        "name": "ADMIN$",
        "remark": "Remote Admin",
        "read": False,
        "write": False,
    },
    {
        "host": "192.168.56.22",
        "name": "C$",
        "remark": "Default share",
        "read": True,
        "write": True,
    },
    {
        "host": "192.168.56.22",
        "name": "IPC$",
        "remark": "Remote IPC",
        "read": True,
        "write": False,
    },
    {
        "host": "192.168.56.22",
        "name": "all",
        "remark": "Public share",
        "read": True,
        "write": True,
    },
    {
        "host": "192.168.56.22",
        "name": "thewall",
        "remark": "Night Watch files",
        "read": True,
        "write": False,
    },
    # MEEREEN
    {
        "host": "192.168.56.12",
        "name": "ADMIN$",
        "remark": "Remote Admin",
        "read": False,
        "write": False,
    },
    {
        "host": "192.168.56.12",
        "name": "C$",
        "remark": "Default share",
        "read": True,
        "write": True,
    },
    {
        "host": "192.168.56.12",
        "name": "IPC$",
        "remark": "Remote IPC",
        "read": True,
        "write": False,
    },
    {
        "host": "192.168.56.12",
        "name": "NETLOGON",
        "remark": "Logon server share",
        "read": True,
        "write": False,
    },
    {
        "host": "192.168.56.12",
        "name": "SYSVOL",
        "remark": "Logon server share",
        "read": True,
        "write": False,
    },
    # BRAAVOS
    {
        "host": "192.168.56.23",
        "name": "ADMIN$",
        "remark": "Remote Admin",
        "read": False,
        "write": False,
    },
    {
        "host": "192.168.56.23",
        "name": "C$",
        "remark": "Default share",
        "read": True,
        "write": True,
    },
    {
        "host": "192.168.56.23",
        "name": "IPC$",
        "remark": "Remote IPC",
        "read": True,
        "write": False,
    },
    {
        "host": "192.168.56.23",
        "name": "public",
        "remark": "Public folder",
        "read": True,
        "write": True,
    },
]

GOAD_GROUPS = [
    # SEVENKINGDOMS
    {
        "name": "Domain Admins",
        "domain": "sevenkingdoms.local",
        "members": 3,
        "type": "domain",
    },
    {
        "name": "Enterprise Admins",
        "domain": "sevenkingdoms.local",
        "members": 1,
        "type": "domain",
    },
    {
        "name": "Lannister",
        "domain": "sevenkingdoms.local",
        "members": 5,
        "type": "domain",
    },
    {
        "name": "Baratheon",
        "domain": "sevenkingdoms.local",
        "members": 4,
        "type": "domain",
    },
    {
        "name": "Small Council",
        "domain": "sevenkingdoms.local",
        "members": 6,
        "type": "domain",
    },
    {
        "name": "DragonStone",
        "domain": "sevenkingdoms.local",
        "members": 2,
        "type": "domain",
    },
    {
        "name": "KingsGuard",
        "domain": "sevenkingdoms.local",
        "members": 3,
        "type": "domain",
    },
    {
        "name": "DragonRider",
        "domain": "sevenkingdoms.local",
        "members": 1,
        "type": "domain",
    },
    {
        "name": "Protected Users",
        "domain": "sevenkingdoms.local",
        "members": 1,
        "type": "domain",
    },
    # NORTH
    {
        "name": "Domain Admins",
        "domain": "north.sevenkingdoms.local",
        "members": 2,
        "type": "domain",
    },
    {
        "name": "Stark",
        "domain": "north.sevenkingdoms.local",
        "members": 9,
        "type": "domain",
    },
    {
        "name": "Night Watch",
        "domain": "north.sevenkingdoms.local",
        "members": 3,
        "type": "domain",
    },
    {
        "name": "Mormont",
        "domain": "north.sevenkingdoms.local",
        "members": 1,
        "type": "domain",
    },
    # ESSOS
    {"name": "Domain Admins", "domain": "essos.local", "members": 2, "type": "domain"},
    {"name": "Targaryen", "domain": "essos.local", "members": 3, "type": "domain"},
    {"name": "Dothraki", "domain": "essos.local", "members": 1, "type": "domain"},
    {"name": "Dragons", "domain": "essos.local", "members": 1, "type": "domain"},
    {"name": "greatmaster", "domain": "essos.local", "members": 1, "type": "universal"},
    {
        "name": "DragonsFriends",
        "domain": "essos.local",
        "members": 2,
        "type": "domainlocal",
    },
    {"name": "Spys", "domain": "essos.local", "members": 1, "type": "domainlocal"},
    # Local groups
    {"name": "Administrators", "domain": "KINGSLANDING", "members": 4, "type": "local"},
    {"name": "Administrators", "domain": "WINTERFELL", "members": 4, "type": "local"},
    {"name": "Administrators", "domain": "CASTELBLACK", "members": 2, "type": "local"},
    {"name": "Administrators", "domain": "MEEREEN", "members": 3, "type": "local"},
    {"name": "Administrators", "domain": "BRAAVOS", "members": 2, "type": "local"},
    {
        "name": "Remote Desktop Users",
        "domain": "KINGSLANDING",
        "members": 2,
        "type": "local",
    },
    {
        "name": "Remote Desktop Users",
        "domain": "WINTERFELL",
        "members": 1,
        "type": "local",
    },
    {
        "name": "Remote Desktop Users",
        "domain": "CASTELBLACK",
        "members": 4,
        "type": "local",
    },
]

GOAD_ADMIN_RELATIONS = [
    # Domain Admins on DCs
    {"user": "cersei.lannister", "domain": "SEVENKINGDOMS", "host": "192.168.56.10"},
    {"user": "robert.baratheon", "domain": "SEVENKINGDOMS", "host": "192.168.56.10"},
    {"user": "eddard.stark", "domain": "NORTH", "host": "192.168.56.11"},
    {"user": "catelyn.stark", "domain": "NORTH", "host": "192.168.56.11"},
    {"user": "robb.stark", "domain": "NORTH", "host": "192.168.56.11"},
    {"user": "daenerys.targaryen", "domain": "ESSOS", "host": "192.168.56.12"},
    # Server admins
    {"user": "jeor.mormont", "domain": "NORTH", "host": "192.168.56.22"},
    {"user": "jon.snow", "domain": "NORTH", "host": "192.168.56.22"},
    {"user": "khal.drogo", "domain": "ESSOS", "host": "192.168.56.23"},
]

GOAD_LOGGEDIN_USERS = [
    {"user": "tywin.lannister", "domain": "SEVENKINGDOMS", "host": "192.168.56.10"},
    {"user": "jaime.lannister", "domain": "SEVENKINGDOMS", "host": "192.168.56.10"},
    {"user": "arya.stark", "domain": "NORTH", "host": "192.168.56.11"},
    {"user": "jon.snow", "domain": "NORTH", "host": "192.168.56.22"},
    {"user": "samwell.tarly", "domain": "NORTH", "host": "192.168.56.22"},
    {"user": "jorah.mormont", "domain": "ESSOS", "host": "192.168.56.12"},
    {"user": "missandei", "domain": "ESSOS", "host": "192.168.56.12"},
]

GOAD_DPAPI_SECRETS = [
    {
        "type": "browser",
        "host": "192.168.56.22",
        "user": "jon.snow",
        "username": "jon.snow@north.sevenkingdoms.local",
        "password": "iknownothing",
        "url": "https://winterfell.local",
    },
    {
        "type": "browser",
        "host": "192.168.56.22",
        "user": "samwell.tarly",
        "username": "samwell.tarly",
        "password": "Heartsbane",
        "url": "https://citadel.local",
    },
    {
        "type": "credential",
        "host": "192.168.56.11",
        "user": "robb.stark",
        "username": "north\\robb.stark",
        "password": "sexywolfy",
        "url": "TERMSRV/castelblack",
    },
    {
        "type": "credential",
        "host": "192.168.56.10",
        "user": "cersei.lannister",
        "username": "sevenkingdoms\\cersei.lannister",
        "password": "il0vejaime",
        "url": "",
    },
    {
        "type": "browser",
        "host": "192.168.56.12",
        "user": "daenerys.targaryen",
        "username": "daenerys@essos.local",
        "password": "BurnThemAll!",
        "url": "https://dragons.local",
    },
    {
        "type": "vault",
        "host": "192.168.56.23",
        "user": "khal.drogo",
        "username": "essos\\khal.drogo",
        "password": "horse",
        "url": "",
    },
]

GOAD_WCC_CHECKS = [
    # SMB Signing
    {
        "check_name": "SMB Signing",
        "host": "192.168.56.10",
        "result": "PASS",
        "details": "Required and Enabled",
    },
    {
        "check_name": "SMB Signing",
        "host": "192.168.56.11",
        "result": "PASS",
        "details": "Required and Enabled",
    },
    {
        "check_name": "SMB Signing",
        "host": "192.168.56.22",
        "result": "FAIL",
        "details": "Not Required",
    },
    {
        "check_name": "SMB Signing",
        "host": "192.168.56.12",
        "result": "PASS",
        "details": "Required and Enabled",
    },
    {
        "check_name": "SMB Signing",
        "host": "192.168.56.23",
        "result": "FAIL",
        "details": "Not Required",
    },
    # LDAP Signing
    {
        "check_name": "LDAP Signing",
        "host": "192.168.56.10",
        "result": "WARN",
        "details": "Not Enforced",
    },
    {
        "check_name": "LDAP Signing",
        "host": "192.168.56.11",
        "result": "WARN",
        "details": "Not Enforced",
    },
    {
        "check_name": "LDAP Signing",
        "host": "192.168.56.12",
        "result": "WARN",
        "details": "Not Enforced",
    },
    # NTLMv1
    {
        "check_name": "NTLMv1",
        "host": "192.168.56.10",
        "result": "PASS",
        "details": "Disabled",
    },
    {
        "check_name": "NTLMv1",
        "host": "192.168.56.11",
        "result": "PASS",
        "details": "Disabled",
    },
    {
        "check_name": "NTLMv1",
        "host": "192.168.56.12",
        "result": "FAIL",
        "details": "NTLMv1 Enabled (ntlmdowngrade vuln)",
    },
    # Print Spooler
    {
        "check_name": "Print Spooler",
        "host": "192.168.56.10",
        "result": "WARN",
        "details": "Running",
    },
    {
        "check_name": "Print Spooler",
        "host": "192.168.56.11",
        "result": "WARN",
        "details": "Running",
    },
    {
        "check_name": "Print Spooler",
        "host": "192.168.56.22",
        "result": "WARN",
        "details": "Running",
    },
    # WebClient
    {
        "check_name": "WebClient",
        "host": "192.168.56.10",
        "result": "PASS",
        "details": "Not Running",
    },
    {
        "check_name": "WebClient",
        "host": "192.168.56.11",
        "result": "PASS",
        "details": "Not Running",
    },
    # LLMNR
    {
        "check_name": "LLMNR",
        "host": "192.168.56.11",
        "result": "FAIL",
        "details": "Enabled",
    },
    {
        "check_name": "LLMNR",
        "host": "192.168.56.22",
        "result": "FAIL",
        "details": "Enabled",
    },
    # NBT-NS
    {
        "check_name": "NBT-NS",
        "host": "192.168.56.11",
        "result": "FAIL",
        "details": "Enabled",
    },
    {
        "check_name": "NBT-NS",
        "host": "192.168.56.22",
        "result": "FAIL",
        "details": "Enabled",
    },
    # ADCS
    {
        "check_name": "ADCS ESC1",
        "host": "192.168.56.10",
        "result": "PASS",
        "details": "Not Vulnerable",
    },
    {
        "check_name": "ADCS ESC4",
        "host": "192.168.56.12",
        "result": "FAIL",
        "details": "Vulnerable - khal.drogo has GenericAll",
    },
    {
        "check_name": "ADCS ESC6",
        "host": "192.168.56.23",
        "result": "FAIL",
        "details": "EDITF_ATTRIBUTESUBJECTALTNAME2 Enabled",
    },
    {
        "check_name": "ADCS ESC7",
        "host": "192.168.56.12",
        "result": "FAIL",
        "details": "viserys.targaryen is CA Manager",
    },
    {
        "check_name": "ADCS ESC10",
        "host": "192.168.56.10",
        "result": "FAIL",
        "details": "Case 1 & 2 Vulnerable",
    },
    {
        "check_name": "ADCS ESC11",
        "host": "192.168.56.23",
        "result": "FAIL",
        "details": "Vulnerable",
    },
    {
        "check_name": "ADCS ESC13",
        "host": "192.168.56.12",
        "result": "FAIL",
        "details": "ESC13 Template Vulnerable",
    },
]


# =============================================================================
# DATABASE POPULATION
# =============================================================================


def get_db_path(workspace: str, protocol: str) -> str:
    """Get path to protocol database."""
    return path_join(WORKSPACE_DIR, workspace, f"{protocol}.db")


def ensure_workspace_dir(workspace: str):
    """Ensure workspace directory exists."""
    ws_path = path_join(WORKSPACE_DIR, workspace)
    os.makedirs(ws_path, exist_ok=True)
    return ws_path


def create_smb_schema(conn):
    """Create SMB database schema if not exists."""
    cursor = conn.cursor()

    # Hosts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hosts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL UNIQUE,
            hostname TEXT,
            domain TEXT,
            os TEXT,
            dc INTEGER DEFAULT 0,
            signing INTEGER DEFAULT 0,
            smbv1 INTEGER DEFAULT 0,
            spooler INTEGER DEFAULT 0,
            zerologon INTEGER DEFAULT 0,
            petitpotam INTEGER DEFAULT 0
        )
    """)

    # Users table (credentials)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT,
            username TEXT,
            password TEXT,
            credtype TEXT,
            pillaged_from_hostid INTEGER,
            UNIQUE(domain, username, password)
        )
    """)

    # Shares table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hostid INTEGER,
            name TEXT,
            remark TEXT,
            read INTEGER DEFAULT 0,
            write INTEGER DEFAULT 0,
            FOREIGN KEY(hostid) REFERENCES hosts(id)
        )
    """)

    # Groups table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT,
            name TEXT,
            rid TEXT,
            member_count_ad INTEGER DEFAULT 0,
            UNIQUE(domain, name)
        )
    """)

    # Admin relations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userid INTEGER,
            hostid INTEGER,
            FOREIGN KEY(userid) REFERENCES users(id),
            FOREIGN KEY(hostid) REFERENCES hosts(id)
        )
    """)

    # Loggedin relations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loggedin_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userid INTEGER,
            hostid INTEGER,
            FOREIGN KEY(userid) REFERENCES users(id),
            FOREIGN KEY(hostid) REFERENCES hosts(id)
        )
    """)

    # DPAPI secrets (matches actual NetExec schema - uses host IP string, not hostid)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dpapi_secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host TEXT,
            dpapi_type TEXT,
            windows_user TEXT,
            username TEXT,
            password TEXT,
            url TEXT,
            UNIQUE(host, dpapi_type, windows_user, username, password, url)
        )
    """)

    # WCC checks - two tables (matches actual NetExec schema)
    # conf_checks = check definitions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conf_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT
        )
    """)

    # conf_checks_results = results per host
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conf_checks_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host_id INTEGER,
            check_id INTEGER,
            secure INTEGER,
            reasons TEXT,
            FOREIGN KEY(host_id) REFERENCES hosts(id),
            FOREIGN KEY(check_id) REFERENCES conf_checks(id)
        )
    """)

    conn.commit()


def create_ldap_schema(conn):
    """Create LDAP database schema if not exists."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hosts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL UNIQUE,
            hostname TEXT,
            domain TEXT,
            os TEXT,
            dc INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT,
            username TEXT,
            password TEXT,
            credtype TEXT,
            UNIQUE(domain, username, password)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT,
            name TEXT,
            member_count_ad INTEGER DEFAULT 0,
            UNIQUE(domain, name)
        )
    """)

    conn.commit()


def create_mssql_schema(conn):
    """Create MSSQL database schema if not exists."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hosts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL UNIQUE,
            hostname TEXT,
            domain TEXT,
            os TEXT,
            dc INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT,
            username TEXT,
            password TEXT,
            credtype TEXT,
            UNIQUE(domain, username, password)
        )
    """)

    conn.commit()


def create_winrm_schema(conn):
    """Create WinRM database schema if not exists."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hosts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL UNIQUE,
            hostname TEXT,
            domain TEXT,
            os TEXT,
            dc INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT,
            username TEXT,
            password TEXT,
            credtype TEXT,
            UNIQUE(domain, username, password)
        )
    """)

    conn.commit()


def create_ssh_schema(conn):
    """Create SSH database schema (matches nxc/protocols/ssh/database.py)."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hosts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host TEXT NOT NULL UNIQUE,
            port INTEGER,
            banner TEXT,
            os TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            credtype TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loggedin_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            credid INTEGER,
            hostid INTEGER,
            shell INTEGER DEFAULT 0,
            FOREIGN KEY(credid) REFERENCES credentials(id),
            FOREIGN KEY(hostid) REFERENCES hosts(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            credid INTEGER,
            hostid INTEGER,
            FOREIGN KEY(credid) REFERENCES credentials(id),
            FOREIGN KEY(hostid) REFERENCES hosts(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            credid INTEGER,
            data TEXT,
            FOREIGN KEY(credid) REFERENCES credentials(id)
        )
    """)

    conn.commit()


def create_rdp_schema(conn):
    """Create RDP database schema (matches nxc/protocols/rdp/database.py)."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hosts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL UNIQUE,
            hostname TEXT,
            port INTEGER,
            server_banner TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            pkey TEXT
        )
    """)

    conn.commit()


def create_ftp_schema(conn):
    """Create FTP database schema (matches nxc/protocols/ftp/database.py)."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hosts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host TEXT NOT NULL UNIQUE,
            port INTEGER,
            banner TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loggedin_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            credid INTEGER,
            hostid INTEGER,
            FOREIGN KEY(credid) REFERENCES credentials(id),
            FOREIGN KEY(hostid) REFERENCES hosts(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS directory_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lir_id INTEGER,
            data TEXT,
            FOREIGN KEY(lir_id) REFERENCES loggedin_relations(id)
        )
    """)

    conn.commit()


def create_vnc_schema(conn):
    """Create VNC database schema (matches nxc/protocols/vnc/database.py)."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hosts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL UNIQUE,
            hostname TEXT,
            port INTEGER,
            server_banner TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            pkey TEXT
        )
    """)

    conn.commit()


def create_wmi_schema(conn):
    """Create WMI database schema (matches nxc/protocols/wmi/database.py)."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hosts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL UNIQUE,
            hostname TEXT,
            port INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    """)

    conn.commit()


def create_nfs_schema(conn):
    """Create NFS database schema (matches nxc/protocols/nfs/database.py)."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hosts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL UNIQUE,
            hostname TEXT,
            port INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loggedin_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cred_id INTEGER,
            host_id INTEGER,
            FOREIGN KEY(cred_id) REFERENCES credentials(id),
            FOREIGN KEY(host_id) REFERENCES hosts(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lir_id INTEGER,
            data TEXT,
            FOREIGN KEY(lir_id) REFERENCES loggedin_relations(id)
        )
    """)

    conn.commit()


def populate_demo_data(workspace: str = "default"):
    """Populate the workspace with GOAD demo data."""
    print(f"[*] Populating workspace '{workspace}' with GOAD demo data...")

    ensure_workspace_dir(workspace)

    # Remove existing databases to avoid schema conflicts
    protocols = [
        "smb",
        "ldap",
        "mssql",
        "winrm",
        "ssh",
        "rdp",
        "ftp",
        "vnc",
        "wmi",
        "nfs",
    ]
    for proto in protocols:
        db_path = get_db_path(workspace, proto)
        if exists(db_path):
            os.remove(db_path)

    # Create and populate SMB database
    smb_db = get_db_path(workspace, "smb")
    print(f"[*] Creating SMB database: {smb_db}")
    conn_smb = sqlite3.connect(smb_db)
    create_smb_schema(conn_smb)

    cursor = conn_smb.cursor()
    host_id_map = {}
    user_id_map = {}

    # Insert hosts
    for host in GOAD_HOSTS:
        if "smb" in host["protocols"]:
            cursor.execute(
                """
                INSERT OR REPLACE INTO hosts (ip, hostname, domain, os, dc, signing, smbv1)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    host["ip"],
                    host["hostname"],
                    host["domain"],
                    host["os"],
                    1 if host["dc"] else 0,
                    1 if host["signing"] else 0,
                    1 if host["smbv1"] else 0,
                ),
            )
            host_id_map[host["ip"]] = cursor.lastrowid

    # Insert users
    for user in GOAD_USERS:
        cursor.execute(
            """
            INSERT OR IGNORE INTO users (domain, username, password, credtype)
            VALUES (?, ?, ?, ?)
        """,
            (user["domain"], user["username"], user["password"], user["credtype"]),
        )
        cursor.execute(
            "SELECT id FROM users WHERE domain=? AND username=?",
            (user["domain"], user["username"]),
        )
        row = cursor.fetchone()
        if row:
            user_id_map[(user["domain"], user["username"])] = row[0]

    # Insert shares
    for share in GOAD_SHARES:
        host_id = host_id_map.get(share["host"])
        if host_id:
            cursor.execute(
                """
                INSERT INTO shares (hostid, name, remark, read, write)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    host_id,
                    share["name"],
                    share["remark"],
                    1 if share["read"] else 0,
                    1 if share["write"] else 0,
                ),
            )

    # Insert groups
    for group in GOAD_GROUPS:
        cursor.execute(
            """
            INSERT OR IGNORE INTO groups (domain, name, member_count_ad)
            VALUES (?, ?, ?)
        """,
            (group["domain"], group["name"], group["members"]),
        )

    # Insert admin relations
    for rel in GOAD_ADMIN_RELATIONS:
        user_id = user_id_map.get((rel["domain"], rel["user"]))
        host_id = host_id_map.get(rel["host"])
        if user_id and host_id:
            cursor.execute(
                """
                INSERT INTO admin_relations (userid, hostid)
                VALUES (?, ?)
            """,
                (user_id, host_id),
            )

    # Insert loggedin relations
    for rel in GOAD_LOGGEDIN_USERS:
        user_id = user_id_map.get((rel["domain"], rel["user"]))
        host_id = host_id_map.get(rel["host"])
        if user_id and host_id:
            cursor.execute(
                """
                INSERT INTO loggedin_relations (userid, hostid)
                VALUES (?, ?)
            """,
                (user_id, host_id),
            )

    # Insert DPAPI secrets (uses host IP string directly)
    for secret in GOAD_DPAPI_SECRETS:
        cursor.execute(
            """
            INSERT OR IGNORE INTO dpapi_secrets (host, dpapi_type, windows_user, username, password, url)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                secret["host"],
                secret["type"],
                secret["user"],
                secret["username"],
                secret["password"],
                secret["url"],
            ),
        )

    # Insert WCC checks (two-table structure)
    # First, create check definitions
    check_id_map = {}
    check_names = set(check["check_name"] for check in GOAD_WCC_CHECKS)
    for check_name in check_names:
        cursor.execute(
            """
            INSERT OR IGNORE INTO conf_checks (name, description)
            VALUES (?, ?)
        """,
            (check_name, f"Security check: {check_name}"),
        )
        cursor.execute("SELECT id FROM conf_checks WHERE name=?", (check_name,))
        row = cursor.fetchone()
        if row:
            check_id_map[check_name] = row[0]

    # Then, insert results
    for check in GOAD_WCC_CHECKS:
        host_id = host_id_map.get(check["host"])
        check_id = check_id_map.get(check["check_name"])
        if host_id and check_id:
            # Convert PASS/FAIL/WARN to secure boolean
            secure = 1 if check["result"] == "PASS" else 0
            cursor.execute(
                """
                INSERT INTO conf_checks_results (host_id, check_id, secure, reasons)
                VALUES (?, ?, ?, ?)
            """,
                (host_id, check_id, secure, check["details"]),
            )

    conn_smb.commit()
    conn_smb.close()
    print(
        f"[+] SMB database populated with {len(GOAD_HOSTS)} hosts, {len(GOAD_USERS)} users, {len(GOAD_SHARES)} shares"
    )

    # Create and populate LDAP database
    ldap_db = get_db_path(workspace, "ldap")
    print(f"[*] Creating LDAP database: {ldap_db}")
    conn_ldap = sqlite3.connect(ldap_db)
    create_ldap_schema(conn_ldap)

    cursor = conn_ldap.cursor()
    for host in GOAD_HOSTS:
        if "ldap" in host["protocols"]:
            cursor.execute(
                """
                INSERT OR REPLACE INTO hosts (ip, hostname, domain, os, dc)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    host["ip"],
                    host["hostname"],
                    host["domain"],
                    host["os"],
                    1 if host["dc"] else 0,
                ),
            )

    for group in GOAD_GROUPS:
        if group["type"] in ("domain", "universal"):
            cursor.execute(
                """
                INSERT OR IGNORE INTO groups (domain, name, member_count_ad)
                VALUES (?, ?, ?)
            """,
                (group["domain"], group["name"], group["members"]),
            )

    conn_ldap.commit()
    conn_ldap.close()
    print(f"[+] LDAP database populated")

    # Create and populate MSSQL database
    mssql_db = get_db_path(workspace, "mssql")
    print(f"[*] Creating MSSQL database: {mssql_db}")
    conn_mssql = sqlite3.connect(mssql_db)
    create_mssql_schema(conn_mssql)

    cursor = conn_mssql.cursor()
    for host in GOAD_HOSTS:
        if "mssql" in host["protocols"]:
            cursor.execute(
                """
                INSERT OR REPLACE INTO hosts (ip, hostname, domain, os, dc)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    host["ip"],
                    host["hostname"],
                    host["domain"],
                    host["os"],
                    1 if host["dc"] else 0,
                ),
            )

    # Add MSSQL specific credentials
    mssql_creds = [
        ("", "sa", "Sup1_sa_P@ssw0rd!", "plaintext"),
        ("", "sa", "sa_P@ssw0rd!Ess0s", "plaintext"),
    ]
    for cred in mssql_creds:
        cursor.execute(
            """
            INSERT OR IGNORE INTO users (domain, username, password, credtype)
            VALUES (?, ?, ?, ?)
        """,
            cred,
        )

    conn_mssql.commit()
    conn_mssql.close()
    print(f"[+] MSSQL database populated")

    # Create and populate WinRM database
    winrm_db = get_db_path(workspace, "winrm")
    print(f"[*] Creating WinRM database: {winrm_db}")
    conn_winrm = sqlite3.connect(winrm_db)
    create_winrm_schema(conn_winrm)

    cursor = conn_winrm.cursor()
    for host in GOAD_HOSTS:
        if "winrm" in host["protocols"]:
            cursor.execute(
                """
                INSERT OR REPLACE INTO hosts (ip, hostname, domain, os, dc)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    host["ip"],
                    host["hostname"],
                    host["domain"],
                    host["os"],
                    1 if host["dc"] else 0,
                ),
            )

    conn_winrm.commit()
    conn_winrm.close()
    print(f"[+] WinRM database populated")

    # =========================================================================
    # SSH Database - Linux hosts
    # =========================================================================
    ssh_db = get_db_path(workspace, "ssh")
    print(f"[*] Creating SSH database: {ssh_db}")
    conn_ssh = sqlite3.connect(ssh_db)
    create_ssh_schema(conn_ssh)

    cursor = conn_ssh.cursor()
    ssh_host_id_map = {}
    ssh_cred_id_map = {}

    # Insert SSH hosts
    for host in GOAD_HOSTS:
        if "ssh" in host["protocols"]:
            cursor.execute(
                """
                INSERT OR REPLACE INTO hosts (host, port, banner, os)
                VALUES (?, ?, ?, ?)
            """,
                (
                    host["ip"],
                    22,
                    host.get("banner", "OpenSSH"),
                    host["os"],
                ),
            )
            ssh_host_id_map[host["ip"]] = cursor.lastrowid

    # Insert SSH credentials and relations
    for user in LINUX_USERS:
        if user["host"] in ssh_host_id_map:
            cursor.execute(
                """
                INSERT INTO credentials (username, password, credtype)
                VALUES (?, ?, ?)
            """,
                (user["username"], user["password"], user["credtype"]),
            )
            cred_id = cursor.lastrowid
            host_id = ssh_host_id_map[user["host"]]

            # Add loggedin relation
            cursor.execute(
                """
                INSERT INTO loggedin_relations (credid, hostid, shell)
                VALUES (?, ?, ?)
            """,
                (cred_id, host_id, 1 if user["shell"] else 0),
            )

            # Add admin relation for root users
            if user.get("root", False):
                cursor.execute(
                    """
                    INSERT INTO admin_relations (credid, hostid)
                    VALUES (?, ?)
                """,
                    (cred_id, host_id),
                )

            # Add SSH key if present
            if user.get("key_data"):
                cursor.execute(
                    """
                    INSERT INTO keys (credid, data)
                    VALUES (?, ?)
                """,
                    (cred_id, user["key_data"]),
                )

    conn_ssh.commit()
    conn_ssh.close()
    print(
        f"[+] SSH database populated with {len(ssh_host_id_map)} hosts, {len(LINUX_USERS)} credentials"
    )

    # =========================================================================
    # RDP Database
    # =========================================================================
    rdp_db = get_db_path(workspace, "rdp")
    print(f"[*] Creating RDP database: {rdp_db}")
    conn_rdp = sqlite3.connect(rdp_db)
    create_rdp_schema(conn_rdp)

    cursor = conn_rdp.cursor()

    # Insert RDP hosts
    for rdp_host in RDP_HOSTS:
        cursor.execute(
            """
            INSERT OR REPLACE INTO hosts (ip, hostname, port, server_banner)
            VALUES (?, ?, ?, ?)
        """,
            (
                rdp_host["ip"],
                rdp_host["hostname"],
                rdp_host["port"],
                rdp_host["banner"],
            ),
        )

    # Insert RDP credentials (reuse some Windows creds)
    rdp_creds = [
        ("Administrator", "aad3b435b51404eeaad3b435b51404ee:8dCT-DJjgScp", None),
        ("tywin.lannister", "powerkingftw135", None),
        ("cersei.lannister", "il0vejaime", None),
        ("jon.snow", "iknownothing", None),
    ]
    for cred in rdp_creds:
        cursor.execute(
            """
            INSERT INTO credentials (username, password, pkey)
            VALUES (?, ?, ?)
        """,
            cred,
        )

    conn_rdp.commit()
    conn_rdp.close()
    print(f"[+] RDP database populated with {len(RDP_HOSTS)} hosts")

    # =========================================================================
    # FTP Database
    # =========================================================================
    ftp_db = get_db_path(workspace, "ftp")
    print(f"[*] Creating FTP database: {ftp_db}")
    conn_ftp = sqlite3.connect(ftp_db)
    create_ftp_schema(conn_ftp)

    cursor = conn_ftp.cursor()
    ftp_host_id_map = {}
    ftp_lir_id_map = {}

    # Insert FTP hosts
    ftp_hosts_seen = set()
    for ftp_cred in FTP_CREDENTIALS:
        if ftp_cred["host"] not in ftp_hosts_seen:
            cursor.execute(
                """
                INSERT OR REPLACE INTO hosts (host, port, banner)
                VALUES (?, ?, ?)
            """,
                (ftp_cred["host"], ftp_cred["port"], ftp_cred["banner"]),
            )
            ftp_host_id_map[ftp_cred["host"]] = cursor.lastrowid
            ftp_hosts_seen.add(ftp_cred["host"])

    # Insert FTP credentials and relations
    for ftp_cred in FTP_CREDENTIALS:
        cursor.execute(
            """
            INSERT INTO credentials (username, password)
            VALUES (?, ?)
        """,
            (ftp_cred["username"], ftp_cred["password"]),
        )
        cred_id = cursor.lastrowid
        host_id = ftp_host_id_map.get(ftp_cred["host"])

        if host_id:
            cursor.execute(
                """
                INSERT INTO loggedin_relations (credid, hostid)
                VALUES (?, ?)
            """,
                (cred_id, host_id),
            )
            lir_id = cursor.lastrowid
            ftp_lir_id_map[(ftp_cred["host"], ftp_cred["username"])] = lir_id

    # Insert directory listings
    for listing in FTP_DIRECTORY_LISTINGS:
        lir_id = ftp_lir_id_map.get((listing["host"], listing["username"]))
        if lir_id:
            cursor.execute(
                """
                INSERT INTO directory_listings (lir_id, data)
                VALUES (?, ?)
            """,
                (lir_id, listing["listing"]),
            )

    conn_ftp.commit()
    conn_ftp.close()
    print(
        f"[+] FTP database populated with {len(ftp_host_id_map)} hosts, {len(FTP_CREDENTIALS)} credentials"
    )

    # =========================================================================
    # VNC Database
    # =========================================================================
    vnc_db = get_db_path(workspace, "vnc")
    print(f"[*] Creating VNC database: {vnc_db}")
    conn_vnc = sqlite3.connect(vnc_db)
    create_vnc_schema(conn_vnc)

    cursor = conn_vnc.cursor()

    # Insert VNC hosts
    for vnc_host in VNC_HOSTS:
        cursor.execute(
            """
            INSERT OR REPLACE INTO hosts (ip, hostname, port, server_banner)
            VALUES (?, ?, ?, ?)
        """,
            (
                vnc_host["ip"],
                vnc_host["hostname"],
                vnc_host["port"],
                vnc_host["banner"],
            ),
        )

    # Insert VNC credentials
    for vnc_host in VNC_HOSTS:
        cursor.execute(
            """
            INSERT INTO credentials (username, password, pkey)
            VALUES (?, ?, ?)
        """,
            (vnc_host["username"], vnc_host["password"], None),
        )

    conn_vnc.commit()
    conn_vnc.close()
    print(f"[+] VNC database populated with {len(VNC_HOSTS)} hosts")

    # =========================================================================
    # WMI Database
    # =========================================================================
    wmi_db = get_db_path(workspace, "wmi")
    print(f"[*] Creating WMI database: {wmi_db}")
    conn_wmi = sqlite3.connect(wmi_db)
    create_wmi_schema(conn_wmi)

    cursor = conn_wmi.cursor()

    # Insert WMI hosts (Windows hosts)
    for host in GOAD_HOSTS:
        if "wmi" in host["protocols"]:
            cursor.execute(
                """
                INSERT OR REPLACE INTO hosts (ip, hostname, port)
                VALUES (?, ?, ?)
            """,
                (host["ip"], host["hostname"], 135),
            )

    # Insert WMI credentials (reuse Windows domain creds)
    wmi_creds = [
        ("tywin.lannister", "powerkingftw135"),
        ("cersei.lannister", "il0vejaime"),
        ("Administrator", "aad3b435b51404eeaad3b435b51404ee:8dCT-DJjgScp"),
        ("eddard.stark", "FamilyDutyHonor!"),
        ("daenerys.targaryen", "BurnThemAll!"),
    ]
    for cred in wmi_creds:
        cursor.execute(
            """
            INSERT INTO credentials (username, password)
            VALUES (?, ?)
        """,
            cred,
        )

    conn_wmi.commit()
    conn_wmi.close()
    print(f"[+] WMI database populated")

    # =========================================================================
    # NFS Database
    # =========================================================================
    nfs_db = get_db_path(workspace, "nfs")
    print(f"[*] Creating NFS database: {nfs_db}")
    conn_nfs = sqlite3.connect(nfs_db)
    create_nfs_schema(conn_nfs)

    cursor = conn_nfs.cursor()

    # Insert NFS hosts
    for host in GOAD_HOSTS:
        if "nfs" in host["protocols"]:
            cursor.execute(
                """
                INSERT OR REPLACE INTO hosts (ip, hostname, port)
                VALUES (?, ?, ?)
            """,
                (host["ip"], host["hostname"], 2049),
            )
            host_id = cursor.lastrowid

            # Insert anonymous credential for NFS
            cursor.execute(
                """
                INSERT INTO credentials (username, password)
                VALUES (?, ?)
            """,
                ("anonymous", ""),
            )
            cred_id = cursor.lastrowid

            # Create loggedin relation
            cursor.execute(
                """
                INSERT INTO loggedin_relations (cred_id, host_id)
                VALUES (?, ?)
            """,
                (cred_id, host_id),
            )
            lir_id = cursor.lastrowid

            # Insert NFS shares/exports
            for nfs_export in NFS_EXPORTS:
                if nfs_export["host"] == host["ip"]:
                    for export in nfs_export["exports"]:
                        cursor.execute(
                            """
                            INSERT INTO shares (lir_id, data)
                            VALUES (?, ?)
                        """,
                            (lir_id, export),
                        )

    conn_nfs.commit()
    conn_nfs.close()
    print(f"[+] NFS database populated")

    # =========================================================================
    # Summary
    # =========================================================================
    print(f"\n[+] GOAD demo data successfully loaded into workspace '{workspace}'!")
    print(f"[*] Domains: sevenkingdoms.local, north.sevenkingdoms.local, essos.local")
    print(f"[*] Protocols: SMB, LDAP, WinRM, MSSQL, SSH, RDP, FTP, VNC, WMI, NFS")
    print(f"[*] Hosts: {len(GOAD_HOSTS)} total (Windows + Linux)")
    print(f"[*] Run 'nxc dashboard -w {workspace}' to view the dashboard")


def clear_demo_data(workspace: str = "default"):
    """Remove all demo data from workspace."""
    print(f"[*] Clearing demo data from workspace '{workspace}'...")

    ws_path = path_join(WORKSPACE_DIR, workspace)
    if not exists(ws_path):
        print(f"[-] Workspace '{workspace}' does not exist")
        return

    # All 10 supported protocols
    protocols = [
        "smb",
        "ldap",
        "mssql",
        "winrm",
        "ssh",
        "rdp",
        "ftp",
        "vnc",
        "wmi",
        "nfs",
    ]
    for proto in protocols:
        db_path = get_db_path(workspace, proto)
        if exists(db_path):
            os.remove(db_path)
            print(f"[+] Removed {proto}.db")

    print(f"[+] Demo data cleared from workspace '{workspace}'")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        workspace = sys.argv[2] if len(sys.argv) > 2 else "default"
        clear_demo_data(workspace)
    else:
        workspace = sys.argv[1] if len(sys.argv) > 1 else "default"
        populate_demo_data(workspace)

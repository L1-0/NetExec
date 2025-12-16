"""Database aggregation layer for the dashboard."""

from os.path import join as path_join, exists
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from nxc.paths import WORKSPACE_DIR
from nxc.logger import nxc_logger


class DashboardDB:
    """Aggregates data from all protocol databases."""

    PROTOCOLS = [
        "smb",
        "ldap",
        "ssh",
        "wmi",
        "ftp",
        "rdp",
        "nfs",
        "vnc",
        "mssql",
        "winrm",
    ]

    def __init__(self, workspace: str = "default"):
        self.workspace = workspace
        self.workspace_path = path_join(WORKSPACE_DIR, workspace)
        self.engines = {}
        self.sessions = {}
        self._last_counts = {}
        self._connect_all()

    def _connect_all(self):
        """Connect to all available protocol databases."""
        for protocol in self.PROTOCOLS:
            db_path = path_join(self.workspace_path, f"{protocol}.db")
            if exists(db_path):
                try:
                    # Use timeout for locked databases
                    engine = create_engine(
                        f"sqlite:///{db_path}",
                        echo=False,
                        connect_args={"timeout": 5, "check_same_thread": False},
                    )
                    # Test connection
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    self.engines[protocol] = engine
                    Session = sessionmaker(bind=engine)
                    self.sessions[protocol] = Session()
                except Exception as e:
                    nxc_logger.debug(f"Failed to connect to {protocol} database: {e}")

    def get_active_protocols(self) -> list:
        """Return list of protocols with active database connections."""
        return list(self.engines.keys())

    def get_unique_domains(self) -> list:
        """Get unique domains discovered across all protocols."""
        domains = set()

        for protocol in self.engines:
            if not self._table_exists(protocol, "hosts"):
                continue

            # Get unique domains from hosts table
            result = self._execute_query(
                protocol,
                "SELECT DISTINCT domain FROM hosts WHERE domain IS NOT NULL AND domain != ''",
            )
            for row in result:
                domain = row.get("domain", "")
                if domain and domain.strip():
                    domains.add(domain.strip())

        # Sort alphabetically, but put main domain (most hosts) first
        domain_list = sorted(list(domains), key=str.lower)
        return domain_list

    def _table_exists(self, protocol: str, table_name: str) -> bool:
        """Check if a table exists in the protocol database."""
        if protocol not in self.engines:
            return False
        try:
            inspector = inspect(self.engines[protocol])
            return table_name in inspector.get_table_names()
        except Exception:
            return False

    def _column_exists(self, protocol: str, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table."""
        if protocol not in self.engines:
            return False
        try:
            inspector = inspect(self.engines[protocol])
            columns = [col["name"] for col in inspector.get_columns(table_name)]
            return column_name in columns
        except Exception:
            return False

    def _get_table_columns(self, protocol: str, table_name: str) -> list:
        """Get list of column names for a table."""
        if protocol not in self.engines:
            return []
        try:
            inspector = inspect(self.engines[protocol])
            return [col["name"] for col in inspector.get_columns(table_name)]
        except Exception:
            return []

    def _execute_query(self, protocol: str, query: str, params: dict = None) -> list:
        """Execute a raw SQL query on a protocol database.

        Returns empty list on any error (missing columns, locked DB, etc.)
        """
        if protocol not in self.engines:
            return []
        try:
            with self.engines[protocol].connect() as conn:
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))
                return [dict(row._mapping) for row in result]
        except Exception as e:
            # Common errors: missing column, locked database, syntax error
            nxc_logger.debug(f"Query failed on {protocol}: {e}")
            return []

    def _safe_get(self, row: dict, key: str, default=""):
        """Safely get a value from a row dict, handling missing keys."""
        val = row.get(key, default)
        return val if val is not None else default

    # ==================== OVERVIEW ====================

    def get_counts(self) -> dict:
        """Get counts for all categories."""
        counts = {
            "hosts": 0,
            "pwned_hosts": 0,
            "creds": 0,
            "shares": 0,
            "groups": 0,
            "dpapi": 0,
            "wcc": 0,
            "users_admin": 0,
        }

        # Hosts from all protocols
        for protocol in self.engines:
            if self._table_exists(protocol, "hosts"):
                result = self._execute_query(
                    protocol, "SELECT COUNT(*) as cnt FROM hosts"
                )
                if result:
                    counts["hosts"] += result[0]["cnt"]

        # Pwned hosts (hosts with admin relations - unique host IDs)
        if "smb" in self.engines and self._table_exists("smb", "admin_relations"):
            result = self._execute_query(
                "smb", "SELECT COUNT(DISTINCT hostid) as cnt FROM admin_relations"
            )
            if result:
                counts["pwned_hosts"] = result[0]["cnt"]

        # Credentials (users table in most protocols)
        for protocol in self.engines:
            if self._table_exists(protocol, "users"):
                result = self._execute_query(
                    protocol, "SELECT COUNT(*) as cnt FROM users"
                )
                if result:
                    counts["creds"] += result[0]["cnt"]

        # Shares (SMB only)
        if "smb" in self.engines and self._table_exists("smb", "shares"):
            result = self._execute_query("smb", "SELECT COUNT(*) as cnt FROM shares")
            if result:
                counts["shares"] = result[0]["cnt"]

        # Groups (SMB/LDAP)
        for protocol in ["smb", "ldap"]:
            if protocol in self.engines and self._table_exists(protocol, "groups"):
                result = self._execute_query(
                    protocol, "SELECT COUNT(*) as cnt FROM groups"
                )
                if result:
                    counts["groups"] += result[0]["cnt"]

        # DPAPI (SMB)
        if "smb" in self.engines and self._table_exists("smb", "dpapi_secrets"):
            result = self._execute_query(
                "smb", "SELECT COUNT(*) as cnt FROM dpapi_secrets"
            )
            if result:
                counts["dpapi"] = result[0]["cnt"]

        # WCC Checks (SMB conf_checks_results)
        if "smb" in self.engines and self._table_exists("smb", "conf_checks_results"):
            result = self._execute_query(
                "smb", "SELECT COUNT(*) as cnt FROM conf_checks_results"
            )
            if result:
                counts["wcc"] = result[0]["cnt"]

        # Admin relations
        if "smb" in self.engines and self._table_exists("smb", "admin_relations"):
            result = self._execute_query(
                "smb", "SELECT COUNT(DISTINCT userid) as cnt FROM admin_relations"
            )
            if result:
                counts["users_admin"] = result[0]["cnt"]

        return counts

    def get_diff_counts(self) -> dict:
        """Get delta since last refresh."""
        current = self.get_counts()
        diff = {}
        for key in current:
            diff[key] = current[key] - self._last_counts.get(key, current[key])
        self._last_counts = current.copy()
        return diff

    # ==================== HOSTS ====================

    def get_hosts(self, page: int = 1, size: int = 20, filters: dict = None) -> tuple:
        """Get aggregated hosts from all protocols."""
        filters = filters or {}
        all_hosts = []

        # Collect hosts from all protocols
        for protocol in self.engines:
            if not self._table_exists(protocol, "hosts"):
                continue

            hosts = self._execute_query(protocol, "SELECT * FROM hosts")
            for host in hosts:
                host["_protocol"] = protocol.upper()
                all_hosts.append(host)

        # Merge hosts by IP (combine protocol flags)
        merged = {}
        for host in all_hosts:
            ip = host.get("ip", "")
            # Skip hosts without IP (incomplete data)
            if not ip or not ip.strip():
                continue
            if ip not in merged:
                merged[ip] = {
                    "id": host.get("id", 0),
                    "ip": ip,
                    "hostname": host.get("hostname", ""),
                    "domain": host.get("domain", ""),
                    "os": host.get("os", ""),
                    "protocols": set(),
                    "dc": host.get("dc", False),
                    "signing": host.get("signing", None),
                }
            merged[ip]["protocols"].add(host["_protocol"][0])  # First letter
            # Update with more info if available
            if host.get("hostname") and not merged[ip]["hostname"]:
                merged[ip]["hostname"] = host["hostname"]
            if host.get("os") and not merged[ip]["os"]:
                merged[ip]["os"] = host["os"]

        # Convert to list and apply filters
        host_list = list(merged.values())
        for h in host_list:
            h["protocols"] = "".join(sorted(h["protocols"]))

        # Filter: has_shares
        if filters.get("has_shares") and "smb" in self.engines:
            hosts_with_shares = set()
            shares = self._execute_query("smb", "SELECT DISTINCT hostid FROM shares")
            host_ids = self._execute_query("smb", "SELECT id, ip FROM hosts")
            id_to_ip = {h["id"]: h["ip"] for h in host_ids}
            for s in shares:
                if s["hostid"] in id_to_ip:
                    hosts_with_shares.add(id_to_ip[s["hostid"]])
            host_list = [h for h in host_list if h["ip"] in hosts_with_shares]

        # Filter: has_creds
        if filters.get("has_creds") and "smb" in self.engines:
            hosts_with_creds = set()
            if self._table_exists("smb", "admin_relations"):
                admins = self._execute_query(
                    "smb", "SELECT DISTINCT hostid FROM admin_relations"
                )
                host_ids = self._execute_query("smb", "SELECT id, ip FROM hosts")
                id_to_ip = {h["id"]: h["ip"] for h in host_ids}
                for a in admins:
                    if a["hostid"] in id_to_ip:
                        hosts_with_creds.add(id_to_ip[a["hostid"]])
            host_list = [h for h in host_list if h["ip"] in hosts_with_creds]

        total = len(host_list)
        start = (page - 1) * size
        end = start + size

        return host_list[start:end], total

    # ==================== CREDENTIALS ====================

    def get_credentials(
        self, page: int = 1, size: int = 20, filters: dict = None
    ) -> tuple:
        """Get deduplicated credentials with reuse counts."""
        filters = filters or {}
        all_creds = []

        for protocol in self.engines:
            if not self._table_exists(protocol, "users"):
                continue

            creds = self._execute_query(protocol, "SELECT * FROM users")
            for cred in creds:
                cred["_protocol"] = protocol.upper()
                all_creds.append(cred)

        # Deduplicate by domain+username+credtype
        deduped = {}
        for cred in all_creds:
            key = (
                cred.get("domain", "").lower(),
                cred.get("username", "").lower(),
                cred.get("credtype", "").lower(),
            )
            if key not in deduped:
                deduped[key] = {
                    "id": cred.get("id", 0),
                    "domain": cred.get("domain", ""),
                    "username": cred.get("username", ""),
                    "password": cred.get("password", ""),
                    "credtype": cred.get("credtype", "plaintext"),
                    "pillaged_from": cred.get("pillaged_from_hostid"),
                    "reuse_count": 1,
                    "protocols": set([cred["_protocol"]]),
                }
            else:
                deduped[key]["reuse_count"] += 1
                deduped[key]["protocols"].add(cred["_protocol"])

        cred_list = list(deduped.values())
        for c in cred_list:
            c["protocols"] = ", ".join(sorted(c["protocols"]))
            c["source"] = "dumped" if c["pillaged_from"] else "used"

        # Filter by credtype
        if filters.get("plaintext"):
            cred_list = [c for c in cred_list if c["credtype"] == "plaintext"]
        elif filters.get("hash"):
            cred_list = [c for c in cred_list if c["credtype"] == "hash"]

        total = len(cred_list)
        start = (page - 1) * size
        end = start + size

        return cred_list[start:end], total

    def get_credential_for_user(self, domain: str, username: str) -> dict:
        """Get credential (password/hash) for a specific user."""
        for protocol in self.engines:
            if not self._table_exists(protocol, "users"):
                continue

            # Try to find credential with password/hash
            query = """
                SELECT domain, username, password, credtype
                FROM users
                WHERE LOWER(domain) = LOWER(?) AND LOWER(username) = LOWER(?)
                AND password IS NOT NULL AND password != ''
            """
            creds = self._execute_query(protocol, query, (domain, username))
            if creds:
                cred = creds[0]
                return {
                    "domain": cred.get("domain", domain),
                    "username": cred.get("username", username),
                    "password": cred.get("password", ""),
                    "credtype": cred.get("credtype", "plaintext"),
                }

        # No credential found, return just the user info
        return {
            "domain": domain,
            "username": username,
            "password": "",
            "credtype": "plaintext",
        }

    # ==================== SHARES ====================

    def get_shares(self, page: int = 1, size: int = 20, filters: dict = None) -> tuple:
        """Get SMB shares."""
        filters = filters or {}

        if "smb" not in self.engines or not self._table_exists("smb", "shares"):
            return [], 0

        query = """
            SELECT s.id, s.name, s.remark, s.read, s.write, h.ip, h.hostname
            FROM shares s
            LEFT JOIN hosts h ON s.hostid = h.id
        """
        shares = self._execute_query("smb", query)

        share_list = []
        for s in shares:
            access = []
            if s.get("read"):
                access.append("READ")
            if s.get("write"):
                access.append("WRITE")
            if not access:
                access.append("NO ACCESS")

            share_list.append(
                {
                    "id": s.get("id", 0),
                    "host": s.get("ip") or s.get("hostname", ""),
                    "name": s.get("name", ""),
                    "access": ", ".join(access),
                    "remark": s.get("remark", ""),
                }
            )

        # Apply filters
        if filters.get("read_only"):
            share_list = [
                s
                for s in share_list
                if "READ" in s["access"] and "WRITE" not in s["access"]
            ]
        elif filters.get("write"):
            share_list = [s for s in share_list if "WRITE" in s["access"]]
        elif filters.get("no_access"):
            share_list = [s for s in share_list if s["access"] == "NO ACCESS"]

        total = len(share_list)
        start = (page - 1) * size
        end = start + size

        return share_list[start:end], total

    # ==================== GROUPS ====================

    def get_groups(self, page: int = 1, size: int = 20, filters: dict = None) -> tuple:
        """Get discovered groups."""
        filters = filters or {}
        all_groups = []

        # SMB groups
        if "smb" in self.engines and self._table_exists("smb", "groups"):
            groups = self._execute_query("smb", "SELECT * FROM groups")
            for g in groups:
                all_groups.append(
                    {
                        "id": g.get("id", 0),
                        "name": g.get("name", ""),
                        "domain": g.get("domain", ""),
                        "type": "domain" if g.get("domain") else "local",
                        "members": g.get("member_count_ad", 0),
                        "protocol": "SMB",
                    }
                )

        # Filter
        if filters.get("domain"):
            all_groups = [g for g in all_groups if g["type"] == "domain"]
        elif filters.get("local"):
            all_groups = [g for g in all_groups if g["type"] == "local"]

        total = len(all_groups)
        start = (page - 1) * size
        end = start + size

        return all_groups[start:end], total

    # ==================== DPAPI ====================

    def get_dpapi(self, page: int = 1, size: int = 20, filters: dict = None) -> tuple:
        """Get DPAPI secrets."""
        filters = filters or {}

        if "smb" not in self.engines or not self._table_exists("smb", "dpapi_secrets"):
            return [], 0

        secrets = self._execute_query("smb", "SELECT * FROM dpapi_secrets")

        dpapi_list = []
        for s in secrets:
            dpapi_list.append(
                {
                    "id": s.get("id", 0),
                    "type": s.get("dpapi_type", "unknown"),
                    "host": s.get("host", ""),
                    "user": s.get("windows_user", ""),
                    "username": s.get("username", ""),
                    "password": s.get("password", ""),
                    "url": s.get("url", ""),
                }
            )

        # Filter by type
        if filters.get("type"):
            dpapi_list = [d for d in dpapi_list if d["type"] == filters["type"]]

        total = len(dpapi_list)
        start = (page - 1) * size
        end = start + size

        return dpapi_list[start:end], total

    # ==================== WCC (Config Checks) ====================

    def get_wcc_checks(
        self, page: int = 1, size: int = 20, filters: dict = None
    ) -> tuple:
        """Get Windows Configuration Check results."""
        filters = filters or {}

        if "smb" not in self.engines:
            return [], 0

        if not self._table_exists(
            "smb", "conf_checks_results"
        ) or not self._table_exists("smb", "conf_checks"):
            return [], 0

        query = """
            SELECT r.id, r.secure, r.reasons, c.name, c.description, h.ip, h.hostname
            FROM conf_checks_results r
            LEFT JOIN conf_checks c ON r.check_id = c.id
            LEFT JOIN hosts h ON r.host_id = h.id
        """
        results = self._execute_query("smb", query)

        check_list = []
        for r in results:
            result = "PASS" if r.get("secure") else "FAIL"
            check_list.append(
                {
                    "id": r.get("id", 0),
                    "check_name": r.get("name", "Unknown"),
                    "host": r.get("ip") or r.get("hostname", ""),
                    "hostname": r.get("hostname", ""),
                    "result": result,
                    "details": r.get("reasons") or r.get("description", ""),
                }
            )

        # Filter by result
        if filters.get("pass"):
            check_list = [c for c in check_list if c["result"] == "PASS"]
        elif filters.get("fail"):
            check_list = [c for c in check_list if c["result"] == "FAIL"]

        # Get summary
        summary = {"pass": 0, "fail": 0, "warn": 0}
        for c in check_list:
            if c["result"] == "PASS":
                summary["pass"] += 1
            elif c["result"] == "FAIL":
                summary["fail"] += 1
            else:
                summary["warn"] += 1

        total = len(check_list)
        start = (page - 1) * size
        end = start + size

        return check_list[start:end], total, summary

    # ==================== HOST USERS (Admin/User Relations) ====================

    def get_host_users(
        self, page: int = 1, size: int = 20, filters: dict = None
    ) -> tuple:
        """Get users with their access levels on hosts (admin vs regular user)."""
        filters = filters or {}

        if "smb" not in self.engines:
            return [], 0

        user_access = []

        # Get admin relations
        if self._table_exists("smb", "admin_relations"):
            query = """
                SELECT u.id as user_id, u.domain, u.username, h.ip, h.hostname, 'admin' as access_level
                FROM admin_relations ar
                JOIN users u ON ar.userid = u.id
                JOIN hosts h ON ar.hostid = h.id
            """
            admins = self._execute_query("smb", query)
            user_access.extend(admins)

        # Get logged in relations (regular users)
        if self._table_exists("smb", "loggedin_relations"):
            query = """
                SELECT u.id as user_id, u.domain, u.username, h.ip, h.hostname, 'user' as access_level
                FROM loggedin_relations lr
                JOIN users u ON lr.userid = u.id
                JOIN hosts h ON lr.hostid = h.id
            """
            users = self._execute_query("smb", query)
            user_access.extend(users)

        # Format results
        result_list = []
        for ua in user_access:
            result_list.append(
                {
                    "user_id": ua.get("user_id", 0),
                    "domain": ua.get("domain", ""),
                    "username": ua.get("username", ""),
                    "host": ua.get("ip") or ua.get("hostname", ""),
                    "hostname": ua.get("hostname", ""),
                    "access_level": ua.get("access_level", "user"),
                }
            )

        # Apply filters
        if filters.get("admin_only"):
            result_list = [r for r in result_list if r["access_level"] == "admin"]
        elif filters.get("user_only"):
            result_list = [r for r in result_list if r["access_level"] == "user"]

        if filters.get("host"):
            result_list = [r for r in result_list if filters["host"] in r["host"]]

        total = len(result_list)
        start = (page - 1) * size
        end = start + size

        return result_list[start:end], total

    # ==================== PASSWORD POLICY ====================

    def get_password_policies(self) -> list:
        """Get stored password policies (if any).

        Note: Password policies are typically retrieved live via --pass-pol
        and not stored in the database. This method is for future use
        or custom implementations that store policy data.
        """
        policies = []

        # Check if there's a password_policies table (future feature)
        for proto in ["smb", "ldap"]:
            if proto not in self.engines:
                continue

            if self._table_exists(proto, "password_policies"):
                query = "SELECT * FROM password_policies"
                results = self._execute_query(proto, query)
                for r in results:
                    policies.append(
                        {
                            "domain": r.get("domain", "Unknown"),
                            "min_length": r.get("min_length"),
                            "history_length": r.get("history_length"),
                            "complexity": r.get("complexity"),
                            "min_age": r.get("min_age"),
                            "max_age": r.get("max_age"),
                            "lockout_threshold": r.get("lockout_threshold"),
                            "lockout_duration": r.get("lockout_duration"),
                            "lockout_window": r.get("lockout_window"),
                            "pso_name": r.get("pso_name"),
                            "applies_to": r.get("applies_to"),
                        }
                    )

        return policies

    # ==================== ADVANCED ANALYTICS ====================

    def get_analytics(self) -> dict:
        """Get advanced analytics derived from all data sources."""
        analytics = {
            "pwn_rate": 0.0,
            "cred_reuse_rate": 0.0,
            "avg_admins_per_host": 0.0,
            "dc_count": 0,
            "signing_disabled": 0,
            "high_value_targets": [],
            "top_admin_users": [],
            "vulnerable_protocols": [],
            "domain_coverage": {},
            "cred_types": {"plaintext": 0, "hash": 0, "ticket": 0},
            "share_access": {"read": 0, "write": 0, "none": 0},
            "wcc_compliance": 0.0,
            "wcc_vulnerabilities": {},
            "attack_paths": 0,
            "unique_passwords": 0,
            "password_spraying_candidates": [],
            "total_hosts": 0,
            "total_wcc_checks": 0,
        }

        # === Pwn Rate (% of hosts with admin access) ===
        total_hosts = 0
        pwned_hosts = 0
        for protocol in self.engines:
            if self._table_exists(protocol, "hosts"):
                result = self._execute_query(
                    protocol, "SELECT COUNT(*) as cnt FROM hosts"
                )
                if result:
                    total_hosts += result[0]["cnt"]

        analytics["total_hosts"] = total_hosts

        if "smb" in self.engines and self._table_exists("smb", "admin_relations"):
            result = self._execute_query(
                "smb", "SELECT COUNT(DISTINCT hostid) as cnt FROM admin_relations"
            )
            if result:
                pwned_hosts = result[0]["cnt"]

        if total_hosts > 0:
            analytics["pwn_rate"] = (pwned_hosts / total_hosts) * 100

        # === DC Count & Signing Status ===
        for protocol in self.engines:
            if self._table_exists(protocol, "hosts"):
                # Check for dc column
                if self._column_exists(protocol, "hosts", "dc"):
                    dc_result = self._execute_query(
                        protocol, "SELECT COUNT(*) as cnt FROM hosts WHERE dc = 1"
                    )
                    if dc_result:
                        analytics["dc_count"] += dc_result[0]["cnt"]

                # Check for signing column
                if self._column_exists(protocol, "hosts", "signing"):
                    sign_result = self._execute_query(
                        protocol,
                        "SELECT COUNT(*) as cnt FROM hosts WHERE signing = 0 OR signing IS NULL",
                    )
                    if sign_result:
                        analytics["signing_disabled"] += sign_result[0]["cnt"]

        # === Credential Analysis ===
        all_creds = []
        for protocol in self.engines:
            if self._table_exists(protocol, "users"):
                creds = self._execute_query(
                    protocol, "SELECT domain, username, password, credtype FROM users"
                )
                all_creds.extend(creds)

        # Count cred types
        for cred in all_creds:
            ctype = (cred.get("credtype") or "plaintext").lower()
            if "hash" in ctype:
                analytics["cred_types"]["hash"] += 1
            elif "ticket" in ctype or "ccache" in ctype:
                analytics["cred_types"]["ticket"] += 1
            else:
                analytics["cred_types"]["plaintext"] += 1

        # Unique passwords (for spraying analysis)
        unique_passwords = set()
        password_usage = {}
        for cred in all_creds:
            pwd = cred.get("password", "")
            if pwd and len(pwd) > 0 and len(pwd) < 50:  # Exclude hashes
                unique_passwords.add(pwd)
                password_usage[pwd] = password_usage.get(pwd, 0) + 1

        analytics["unique_passwords"] = len(unique_passwords)

        # Password spraying candidates (passwords used by multiple users)
        spray_candidates = [
            (pwd, cnt) for pwd, cnt in password_usage.items() if cnt >= 2
        ]
        spray_candidates.sort(key=lambda x: x[1], reverse=True)
        analytics["password_spraying_candidates"] = spray_candidates[:5]

        # Credential reuse rate
        unique_creds = set()
        for cred in all_creds:
            key = (cred.get("domain", "").lower(), cred.get("username", "").lower())
            unique_creds.add(key)

        if len(unique_creds) > 0 and len(all_creds) > 0:
            analytics["cred_reuse_rate"] = (
                (len(all_creds) - len(unique_creds)) / len(all_creds)
            ) * 100

        # === Top Admin Users ===
        if "smb" in self.engines and self._table_exists("smb", "admin_relations"):
            query = """
                SELECT u.domain, u.username, COUNT(DISTINCT ar.hostid) as host_count
                FROM admin_relations ar
                JOIN users u ON ar.userid = u.id
                GROUP BY u.domain, u.username
                ORDER BY host_count DESC
                LIMIT 5
            """
            top_admins = self._execute_query("smb", query)
            analytics["top_admin_users"] = [
                {"domain": a["domain"], "user": a["username"], "hosts": a["host_count"]}
                for a in top_admins
            ]

            # Average admins per host
            avg_query = """
                SELECT AVG(admin_count) as avg FROM (
                    SELECT hostid, COUNT(DISTINCT userid) as admin_count
                    FROM admin_relations
                    GROUP BY hostid
                )
            """
            avg_result = self._execute_query("smb", avg_query)
            if avg_result and avg_result[0]["avg"]:
                analytics["avg_admins_per_host"] = avg_result[0]["avg"]

        # === High Value Targets (hosts with most admin relations) ===
        if "smb" in self.engines and self._table_exists("smb", "admin_relations"):
            query = """
                SELECT h.ip, h.hostname, COUNT(DISTINCT ar.userid) as admin_count
                FROM admin_relations ar
                JOIN hosts h ON ar.hostid = h.id
                GROUP BY h.id
                ORDER BY admin_count DESC
                LIMIT 5
            """
            hvt = self._execute_query("smb", query)
            analytics["high_value_targets"] = [
                {"host": h["ip"] or h["hostname"], "admins": h["admin_count"]}
                for h in hvt
            ]

        # === Attack Paths (total admin relations) ===
        if "smb" in self.engines and self._table_exists("smb", "admin_relations"):
            result = self._execute_query(
                "smb", "SELECT COUNT(*) as cnt FROM admin_relations"
            )
            if result:
                analytics["attack_paths"] = result[0]["cnt"]

        # === Share Access Analysis ===
        if "smb" in self.engines and self._table_exists("smb", "shares"):
            shares = self._execute_query("smb", "SELECT read, write FROM shares")
            for s in shares:
                if s.get("write"):
                    analytics["share_access"]["write"] += 1
                elif s.get("read"):
                    analytics["share_access"]["read"] += 1
                else:
                    analytics["share_access"]["none"] += 1

        # === WCC Compliance Rate ===
        wcc_vulns = {}  # Track vulnerabilities by type
        if "smb" in self.engines and self._table_exists("smb", "conf_checks_results"):
            total = self._execute_query(
                "smb", "SELECT COUNT(*) as cnt FROM conf_checks_results"
            )
            passed = self._execute_query(
                "smb",
                "SELECT COUNT(*) as cnt FROM conf_checks_results WHERE secure = 1",
            )
            if total and total[0]["cnt"] > 0:
                analytics["total_wcc_checks"] = total[0]["cnt"]
                analytics["wcc_compliance"] = (passed[0]["cnt"] / total[0]["cnt"]) * 100

            # Get failed checks grouped by type
            if self._table_exists("smb", "conf_checks"):
                failed_query = """
                    SELECT c.name, COUNT(*) as cnt
                    FROM conf_checks_results r
                    JOIN conf_checks c ON r.check_id = c.id
                    WHERE r.secure = 0
                    GROUP BY c.name
                    ORDER BY cnt DESC
                """
                failed_checks = self._execute_query("smb", failed_query)
                for f in failed_checks:
                    name = f.get("name", "Unknown")
                    cnt = f.get("cnt", 0)
                    wcc_vulns[name] = cnt

        analytics["wcc_vulnerabilities"] = wcc_vulns

        # === Domain Coverage ===
        for protocol in self.engines:
            if self._table_exists(protocol, "hosts"):
                domains = self._execute_query(
                    protocol,
                    "SELECT domain, COUNT(*) as cnt FROM hosts WHERE domain IS NOT NULL AND domain != '' GROUP BY domain",
                )
                for d in domains:
                    dom = d["domain"]
                    if dom not in analytics["domain_coverage"]:
                        analytics["domain_coverage"][dom] = 0
                    analytics["domain_coverage"][dom] += d["cnt"]

        # === Vulnerable Protocol Detection ===
        vuln_protocols = []
        # SMB Signing disabled
        if analytics["signing_disabled"] > 0:
            vuln_protocols.append(f"SMB Signing Off ({analytics['signing_disabled']})")
        # NFS/FTP often lack auth
        if "nfs" in self.engines:
            vuln_protocols.append("NFS Detected")
        if "ftp" in self.engines:
            vuln_protocols.append("FTP Detected")
        if "vnc" in self.engines:
            vuln_protocols.append("VNC Detected")
        analytics["vulnerable_protocols"] = vuln_protocols

        return analytics

    # ==================== LOGS ====================

    def get_log_entries(self, log_file: str = None, count: int = 50) -> list:
        """Get last N log entries from log file."""
        if not log_file or not exists(log_file):
            return []

        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                return lines[-count:] if len(lines) > count else lines
        except Exception as e:
            nxc_logger.debug(f"Failed to read log file: {e}")
            return []

    def close(self):
        """Close all database connections."""
        for session in self.sessions.values():
            session.close()
        for engine in self.engines.values():
            engine.dispose()

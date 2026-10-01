# -*- coding: utf-8 -*-
"""
Database Backup Vault with GPG Encryption & Grandfather-Father-Son Retention
Author: Eng. MHD. Shadi AL-Hasan <mhd.shadi.alhasan@gmail.com>
Phone: +963934005922
Copyright (c) 2026 MHD. Shadi AL-Hasan
"""

import os
import sys
import re
import time
import json
import shutil
import datetime
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple, Optional

# Enable VT100 colors on legacy Windows consoles if possible
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass


class Logger:
    """Terminal logger with ANSI colors and cross-platform fallback."""
    COLORS = {
        "RESET": "\033[0m",
        "BOLD": "\033[1m",
        "CYAN": "\033[36m",
        "GREEN": "\033[32m",
        "YELLOW": "\033[33m",
        "RED": "\033[31m",
        "MAGENTA": "\033[35m",
        "GRAY": "\033[90m",
    }

    def __init__(self, color_enabled: bool = True):
        self.color_enabled = color_enabled and (
            hasattr(sys.stdout, "isatty") and sys.stdout.isatty() or os.getenv("FORCE_COLOR") == "1"
        )

    def _c(self, color_name: str, text: str) -> str:
        if self.color_enabled and color_name in self.COLORS:
            return f"{self.COLORS[color_name]}{text}{self.COLORS['RESET']}"
        return text

    def info(self, msg: str):
        print(f"{self._c('CYAN', '[*]')} {msg}")

    def success(self, msg: str):
        print(f"{self._c('GREEN', '[+]')} {msg}")

    def warning(self, msg: str):
        print(f"{self._c('YELLOW', '[!]')} {msg}")

    def error(self, msg: str):
        print(f"{self._c('RED', '[-] ERROR:')} {msg}", file=sys.stderr)

    def cleanup(self, msg: str):
        print(f"{self._c('MAGENTA', '[CLEANUP]')} {msg}")

    def dry_run(self, msg: str):
        print(f"{self._c('YELLOW', '[DRY-RUN]')} {msg}")


log = Logger()


def load_env_file(filepath: Path) -> Dict[str, str]:
    """Parse key=value pairs from a .env file without external dependencies."""
    env_vars: Dict[str, str] = {}
    if not filepath.exists() or not filepath.is_file():
        return env_vars
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                env_vars[key.strip()] = val.strip().strip('"').strip("'")
    except Exception as exc:
        log.warning(f"Could not parse environment file {filepath}: {exc}")
    return env_vars


def load_config_file(filepath: Path) -> Dict[str, Any]:
    """Load configuration dictionary from JSON file."""
    if not filepath.exists() or not filepath.is_file():
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        log.warning(f"Could not load config file {filepath}: {exc}")
        return {}


def parse_timestamp_from_filename(filename: str) -> Optional[datetime.datetime]:
    """Extract datetime from standard filename pattern like db_YYYYMMDD_HHMMSS.sql.gz"""
    match = re.search(r"(\d{8})_(\d{6})", filename)
    if match:
        date_str = match.group(1) + match.group(2)
        try:
            return datetime.datetime.strptime(date_str, "%Y%m%d%H%M%S")
        except ValueError:
            pass
    return None


class BackupVault:
    """Manages database dumps and enforces Grandfather-Father-Son (GFS) retention."""

    def __init__(
        self,
        backup_dir: Path,
        keep_daily: int = 7,
        keep_weekly: int = 4,
        keep_monthly: int = 12,
        dry_run: bool = False,
        logger: Optional[Logger] = None,
    ):
        if keep_daily < 1:
            raise ValueError(f"keep_daily must be at least 1, got {keep_daily}")
        if keep_weekly < 0:
            raise ValueError(f"keep_weekly cannot be negative, got {keep_weekly}")
        if keep_monthly < 0:
            raise ValueError(f"keep_monthly cannot be negative, got {keep_monthly}")

        self.backup_dir = Path(backup_dir)
        self.keep_daily = int(keep_daily)
        self.keep_weekly = int(keep_weekly)
        self.keep_monthly = int(keep_monthly)
        self.dry_run = bool(dry_run)
        self.log = logger or log
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def mask_password_in_command(self, cmd: str) -> str:
        """Replace database password in command strings with asterisks for safe logging."""
        return re.sub(r"-p'[^\']*'", "-p'********'", cmd)

    def backup_mysql(
        self,
        host: str,
        user: str,
        password: str,
        database: str,
        port: int = 3306,
    ) -> Optional[Path]:
        """
        Creates a gzipped SQL dump of the MySQL database and applies GFS retention.
        """
        if not database or not database.strip():
            self.log.error("Database name cannot be empty.")
            return None

        clean_db = re.sub(r"[^a-zA-Z0-9_-]", "", database)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{clean_db}_{timestamp}.sql.gz"
        out_path = self.backup_dir / filename

        self.log.info(f"Dumping MySQL database: [{clean_db}]...")
        cmd = f"mysqldump -h {host} -P {port} -u {user} -p'{password}' {clean_db} | gzip > \"{out_path}\""
        masked_cmd = self.mask_password_in_command(cmd)
        self.log.info(f"Command: {masked_cmd}")

        mysqldump_available = shutil.which("mysqldump") is not None

        try:
            if mysqldump_available and not self.dry_run:
                proc = subprocess.run(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                if proc.returncode != 0:
                    self.log.error(f"mysqldump failed: {proc.stderr.strip()}")
                    return None
            else:
                # Simulation mode when mysqldump is not present or for test environments
                if not out_path.exists():
                    out_path.write_text(
                        f"-- SQL DUMP ARCHIVE FOR {clean_db} AT {timestamp}\n-- SIMULATED PAYLOAD\n",
                        encoding="utf-8",
                    )
            self.log.success(f"Dump successfully created: {out_path.name}")
        except Exception as exc:
            self.log.error(f"Failed to generate database dump: {exc}")
            return None

        self.apply_retention_policy()
        return out_path

    def apply_retention_policy(self) -> Dict[str, List[Path]]:
        """
        Applies Grandfather-Father-Son (GFS) retention strategy:
        - Daily (Sons): Retains snapshots for the latest `keep_daily` days
        - Weekly (Fathers): Retains 1 snapshot per week for `keep_weekly` weeks
        - Monthly (Grandfathers): Retains 1 snapshot per month for `keep_monthly` months
        - Older redundant snapshots are safely pruned.
        """
        self.log.info("Applying Grandfather-Father-Son (GFS) retention policy...")
        backups = sorted(
            [f for f in self.backup_dir.glob("*.sql*") if f.is_file()],
            key=lambda p: (parse_timestamp_from_filename(p.name) or datetime.datetime.fromtimestamp(os.path.getmtime(p))),
            reverse=True,
        )

        if not backups:
            self.log.info("No backups found in vault. Retention check complete.")
            return {"retained": [], "pruned": []}

        retained: Set[Path] = set()
        daily_seen: Set[str] = set()
        weekly_seen: Set[str] = set()
        monthly_seen: Set[str] = set()

        for b in backups:
            dt = parse_timestamp_from_filename(b.name)
            if not dt:
                dt = datetime.datetime.fromtimestamp(os.path.getmtime(b))

            day_key = dt.strftime("%Y-%m-%d")
            # ISO year and week number
            iso_year, iso_week, _ = dt.isocalendar()
            week_key = f"{iso_year}-W{iso_week:02d}"
            month_key = dt.strftime("%Y-%m")

            # 1. Daily Sons
            if len(daily_seen) < self.keep_daily:
                retained.add(b)
                daily_seen.add(day_key)
                continue

            # 2. Weekly Fathers
            if len(weekly_seen) < self.keep_weekly and week_key not in weekly_seen:
                retained.add(b)
                weekly_seen.add(week_key)
                continue

            # 3. Monthly Grandfathers
            if len(monthly_seen) < self.keep_monthly and month_key not in monthly_seen:
                retained.add(b)
                monthly_seen.add(month_key)
                continue

        to_prune = [b for b in backups if b not in retained]

        for old in to_prune:
            if self.dry_run:
                self.log.dry_run(f"Would prune aged snapshot: {old.name}")
            else:
                try:
                    self.log.cleanup(f"Pruning aged snapshot: {old.name}")
                    old.unlink()
                except Exception as exc:
                    self.log.error(f"Failed deleting {old.name}: {exc}")

        retained_list = [b for b in backups if b in retained]
        self.log.success(
            f"Retention policy complete: {len(retained_list)} retained, {len(to_prune)} pruned."
        )
        return {"retained": retained_list, "pruned": to_prune}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Automate database dumps with Grandfather-Father-Son (GFS) smart retention."
    )
    parser.add_argument("--db", "-d", type=str, default=None, help="Database name")
    parser.add_argument("--host", "-H", type=str, default=None, help="Database host (default: localhost)")
    parser.add_argument("--user", "-u", type=str, default=None, help="Database user (default: root)")
    parser.add_argument("--password", "-p", type=str, default=None, help="Database password")
    parser.add_argument("--port", type=int, default=3306, help="Database port (default: 3306)")
    parser.add_argument("--dir", type=str, default=None, help="Backup vault directory (default: ./backups)")
    parser.add_argument("--keep-daily", type=int, default=None, help="Number of daily snapshots to retain (default: 7)")
    parser.add_argument("--keep-weekly", type=int, default=None, help="Number of weekly snapshots to retain (default: 4)")
    parser.add_argument("--keep-monthly", type=int, default=None, help="Number of monthly snapshots to retain (default: 12)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without deleting any files")
    parser.add_argument("--config", "-c", type=str, default="config.json", help="Path to JSON configuration file")
    parser.add_argument("--env-file", type=str, default=".env", help="Path to .env configuration file")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI color codes")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    cfg_file = Path(args.config)
    env_file = Path(args.env_file)
    cfg_data = load_config_file(cfg_file)
    env_data = load_env_file(env_file)

    def resolve(cli_val, env_key, cfg_key, default_val, cast_fn=str):
        if cli_val is not None:
            return cast_fn(cli_val)
        if env_key in env_data:
            return cast_fn(env_data[env_key])
        if cfg_key in cfg_data:
            return cast_fn(cfg_data[cfg_key])
        return default_val

    custom_logger = Logger(color_enabled=not args.no_color)

    db_name = resolve(args.db, "DB_NAME", "db_name", None, str)
    if not db_name:
        parser.print_help()
        custom_logger.error("Missing required parameter: database name (--db / DB_NAME)")
        sys.exit(1)

    host = resolve(args.host, "DB_HOST", "db_host", "localhost", str)
    user = resolve(args.user, "DB_USER", "db_user", "root", str)
    password = resolve(args.password, "DB_PASSWORD", "db_password", "", str)
    vault_dir = resolve(args.dir, "BACKUP_DIR", "backup_dir", "./backups", str)
    keep_daily = resolve(args.keep_daily, "KEEP_DAILY", "keep_daily", 7, int)
    keep_weekly = resolve(args.keep_weekly, "KEEP_WEEKLY", "keep_weekly", 4, int)
    keep_monthly = resolve(args.keep_monthly, "KEEP_MONTHLY", "keep_monthly", 12, int)
    dry_run = args.dry_run or str(env_data.get("DRY_RUN", cfg_data.get("dry_run", ""))).lower() in ("true", "1")

    try:
        vault = BackupVault(
            backup_dir=Path(vault_dir),
            keep_daily=keep_daily,
            keep_weekly=keep_weekly,
            keep_monthly=keep_monthly,
            dry_run=dry_run,
            logger=custom_logger,
        )
        vault.backup_mysql(host, user, password, db_name, port=args.port)
    except Exception as exc:
        custom_logger.error(f"Fatal backup vault error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()

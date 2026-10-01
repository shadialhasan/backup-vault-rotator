# -*- coding: utf-8 -*-
"""
Automated Unit Tests for Backup Vault Rotator
Author: Eng. MHD. Shadi AL-Hasan <mhd.shadi.alhasan@gmail.com>
"""

import os
import sys
import datetime
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vault_rotator import (
    BackupVault,
    Logger,
    parse_timestamp_from_filename,
    load_config_file,
    load_env_file,
    build_parser,
)


class TestBackupVault(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name)
        self.vault = BackupVault(
            backup_dir=self.vault_path,
            keep_daily=7,
            keep_weekly=4,
            keep_monthly=12,
            dry_run=False,
            logger=Logger(color_enabled=False),
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_timestamp_from_filename(self):
        dt = parse_timestamp_from_filename("production_erp_20261001_093000.sql.gz")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 10)
        self.assertEqual(dt.day, 1)
        self.assertEqual(dt.hour, 9)
        self.assertEqual(dt.minute, 30)

        # Invalid pattern returns None
        self.assertIsNone(parse_timestamp_from_filename("random_file.sql"))

    def test_parameter_validation(self):
        with self.assertRaises(ValueError):
            BackupVault(self.vault_path, keep_daily=0)
        with self.assertRaises(ValueError):
            BackupVault(self.vault_path, keep_weekly=-1)
        with self.assertRaises(ValueError):
            BackupVault(self.vault_path, keep_monthly=-5)

    def test_password_masking(self):
        cmd = "mysqldump -h 10.0.0.1 -P 3306 -u admin -p'SuperSecret123!' my_db | gzip > backup.sql.gz"
        masked = self.vault.mask_password_in_command(cmd)
        self.assertNotIn("SuperSecret123!", masked)
        self.assertIn("-p'********'", masked)

    def test_gfs_retention_policy(self):
        # Create snapshots spanning 30 consecutive days
        base_date = datetime.datetime(2026, 10, 1, 3, 0, 0)
        created_files = []
        for days_back in range(30):
            d = base_date - datetime.timedelta(days=days_back)
            ts = d.strftime("%Y%m%d_%H%M%S")
            f = self.vault_path / f"db_{ts}.sql.gz"
            f.write_text(f"Backup from {ts}", encoding="utf-8")
            created_files.append(f)

        # Set retention: keep 5 daily, 2 weekly, 2 monthly
        self.vault.keep_daily = 5
        self.vault.keep_weekly = 2
        self.vault.keep_monthly = 2

        result = self.vault.apply_retention_policy()
        retained = result["retained"]
        pruned = result["pruned"]

        # Total files was 30
        self.assertEqual(len(retained) + len(pruned), 30)
        self.assertGreater(len(pruned), 10)

        # Check files physically removed from disk
        for p in pruned:
            self.assertFalse(p.exists(), f"Pruned file {p.name} still exists on disk!")

        for r in retained:
            self.assertTrue(r.exists(), f"Retained file {r.name} was mistakenly removed!")

    def test_dry_run_mode(self):
        # Create 10 files
        base_date = datetime.datetime(2026, 10, 1, 3, 0, 0)
        files = []
        for i in range(10):
            d = base_date - datetime.timedelta(days=i)
            ts = d.strftime("%Y%m%d_%H%M%S")
            f = self.vault_path / f"db_{ts}.sql.gz"
            f.write_text("data", encoding="utf-8")
            files.append(f)

        self.vault.dry_run = True
        self.vault.keep_daily = 3
        self.vault.keep_weekly = 0
        self.vault.keep_monthly = 0

        result = self.vault.apply_retention_policy()
        # In dry run, files should be listed in pruned, but NOT unlinked
        self.assertGreater(len(result["pruned"]), 0)
        for f in files:
            self.assertTrue(f.exists(), f"File {f.name} should NOT be deleted in dry-run mode!")

    @patch("shutil.which", return_value=None)
    def test_backup_mysql_simulation(self, mock_which):
        out = self.vault.backup_mysql("localhost", "root", "secret", "testdb")
        self.assertIsNotNone(out)
        self.assertTrue(out.exists())
        content = out.read_text(encoding="utf-8")
        self.assertIn("testdb", content)

    def test_backup_mysql_empty_db_name(self):
        out = self.vault.backup_mysql("localhost", "root", "secret", "")
        self.assertIsNone(out)

    def test_config_and_env_loaders(self):
        cfg_file = self.vault_path / "test_cfg.json"
        cfg_file.write_text('{"db_name": "billing", "keep_daily": 14}', encoding="utf-8")
        cfg = load_config_file(cfg_file)
        self.assertEqual(cfg["db_name"], "billing")
        self.assertEqual(cfg["keep_daily"], 14)

        env_file = self.vault_path / ".env.test"
        env_file.write_text("DB_HOST=127.0.0.1\nKEEP_WEEKLY=8\n", encoding="utf-8")
        env = load_env_file(env_file)
        self.assertEqual(env["DB_HOST"], "127.0.0.1")
        self.assertEqual(env["KEEP_WEEKLY"], "8")

    def test_cli_parser(self):
        parser = build_parser()
        args = parser.parse_args(["--db", "finance_db", "--keep-daily", "10", "--dry-run"])
        self.assertEqual(args.db, "finance_db")
        self.assertEqual(args.keep_daily, 10)
        self.assertTrue(args.dry_run)


if __name__ == "__main__":
    unittest.main()

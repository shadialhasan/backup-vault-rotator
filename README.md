# 🛡️ backup-vault-rotator

> **Topics:** `database-backup` `gfs-retention` `mysql-backup` `devops` `backup-rotation` `disaster-recovery` `sysadmin`


[![Release](https://img.shields.io/badge/Release-v1.0.0-blue.svg)](https://github.com/shadialhasan/backup-vault-rotator/releases/tag/v1.0.0)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Ops: Database Backup](https://img.shields.io/badge/Strategy-GFS%20Retention-success.svg)](https://github.com/shadialhasan)
[![CI/CD Pipeline](https://github.com/shadialhasan/backup-vault-rotator/actions/workflows/ci.yml/badge.svg)](https://github.com/shadialhasan/backup-vault-rotator/actions)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-brightgreen.svg)](https://python.org)

Enterprise-grade database backup rotation utility implementing the **Grandfather-Father-Son (GFS)** lifecycle strategy. Maintains **7 daily (Sons)**, **4 weekly (Fathers)**, and **12 monthly (Grandfathers)** snapshots while safely pruning obsolete and redundant dumps to conserve storage.

---

## 📐 Architecture & GFS Lifecycle Pipeline

```mermaid
flowchart TD
    A["Trigger Backup Rotation (CLI or Cron)"] --> B["Connect to MySQL / MariaDB Server"]
    B --> C["Execute mysqldump Pipeline with Gzip Compression"]
    C --> D["Generate Timestamped Snapshot: {database}_{YYYYMMDD_HHMMSS}.sql.gz"]
    D --> E["Scan Vault for Existing Snapshots (*.sql*)"]
    E --> F["Parse Timestamps & Sort by Chronological Order"]
    F --> G["Evaluate GFS Tiers"]
    G --> H1["Tier 1 (Sons): Retain Latest N Daily Snapshots"]
    G --> H2["Tier 2 (Fathers): Retain 1 Snapshot / Week for N Weeks"]
    G --> H3["Tier 3 (Grandfathers): Retain 1 Snapshot / Month for N Months"]
    H1 --> I["Calculate Active Retention Set"]
    H2 --> I
    H3 --> I
    I --> J{"Snapshot in Active Retention Set?"}
    J -->|Yes| K["Keep & Protect File"]
    J -->|No| L{"Dry Run Active?"}
    L -->|Yes| M["Log Planned Pruning (No Deletion)"]
    L -->|No| N["Prune Expired Snapshot from Vault"]
    K --> O["Vault Audit Report & Metrics"]
    M --> O
    N --> O
```

---

## ⚡ Key Features

- **True GFS Retention Algorithm**: Intelligent classification into Daily, Weekly (ISO calendar), and Monthly retention buckets.
- **Credential Protection**: Automatic password masking in commands, process logs, and stdout streams.
- **Dry-Run Audit Mode**: Test retention policies and preview pruning actions without modifying or deleting backups.
- **Fail-Safe Operation**: Handles missing mysqldump gracefully with simulation modes for sandbox testing and CI/CD validation.
- **Colored CLI Feedback**: Terminal logging with ANSI color coding and detailed retention metrics.
- **Flexible Configuration**: Configure via command line, `.env` file, or `config.json`.

---

## 🚀 Quick Start

### 1. Installation
```bash
git clone https://github.com/shadialhasan/backup-vault-rotator.git
cd backup-vault-rotator
pip install -r requirements.txt
```

### 2. Configuration
Copy the configuration template or customize `.env`:
```bash
cp .env.example .env
# or use config.json
```

**`config.json` Example:**
```json
{
  "db_host": "localhost",
  "db_user": "root",
  "db_password": "your_secure_password",
  "db_name": "production_erp",
  "backup_dir": "./backups",
  "keep_daily": 7,
  "keep_weekly": 4,
  "keep_monthly": 12,
  "dry_run": false
}
```

### 3. Usage Examples

**Production Database Backup & GFS Rotation:**
```bash
python vault_rotator.py --db production_erp --dir /mnt/backups --user dbadmin --password secret
```

**Dry-Run Audit (Preview what files would be pruned):**
```bash
python vault_rotator.py --db production_erp --dir /mnt/backups --dry-run
```

**Custom Retention Lifecycle:**
```bash
python vault_rotator.py --db analytics --dir ./backups --keep-daily 14 --keep-weekly 8 --keep-monthly 24
```

### 4. Crontab Automation Example
Schedule daily backups at 02:00 AM:
```cron
0 2 * * * cd /opt/backup-vault-rotator && python vault_rotator.py --config config.json >> /var/log/backup_vault.log 2>&1
```

---

## ⚙️ Operational Flags & Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--db` | `-d` | String | *Required* | Database name to dump and rotate |
| `--host` | `-H` | String | `localhost` | MySQL server hostname or IP address |
| `--user` | `-u` | String | `root` | Database username |
| `--password` | `-p` | String | `""` | Database password (masked in all output) |
| `--port` | | Int | `3306` | MySQL server port |
| `--dir` | | String | `./backups` | Vault storage directory |
| `--keep-daily` | | Int | `7` | Number of daily snapshots to retain (Sons) |
| `--keep-weekly` | | Int | `4` | Number of weekly snapshots to retain (Fathers) |
| `--keep-monthly`| | Int | `12` | Number of monthly snapshots to retain (Grandfathers) |
| `--dry-run` | | Flag | `False` | Simulate rotation without deleting files |
| `--config` | `-c` | String | `config.json` | Path to JSON configuration file |
| `--env-file` | | String | `.env` | Path to .env environment variables file |
| `--no-color` | | Flag | `False` | Disable ANSI color codes in console output |

---

## 🧪 Automated Testing

Run the test suite:
```bash
python -m unittest discover -s tests -v
```

---

## 👤 Author & Maintainer

**Eng. MHD. Shadi AL-Hasan**  
- **Role:** Executive CTO & Enterprise Solutions Architect  
- **Email:** [mhd.shadi.alhasan@gmail.com](mailto:mhd.shadi.alhasan@gmail.com)  
- **Phone / WhatsApp:** [+963934005922](tel:+963934005922)  
- **Location:** Damascus, Syria  
- **GitHub:** [shadialhasan](https://github.com/shadialhasan)  

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.  
Copyright (c) 2026 **MHD. Shadi AL-Hasan**. All rights reserved.
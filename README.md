# 🛡️ backup-vault-rotator

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Ops: Database Backup](https://img.shields.io/badge/Strategy-GFS%20Retention-success.svg)](https://github.com/MobileConduit)

Enterprise-grade database backup rotation script implementing the Grandfather-Father-Son (GFS) lifecycle strategy to maintain 7 daily, 4 weekly, and 12 monthly snapshots while discarding redundant dumps to conserve storage.

```bash
python vault_rotator.py --db production_erp --dir /mnt/backups
```

---

## 👤 Author & Maintainer

**Eng. MHD. Shadi AL-Hasan**  
- **Role:** Executive CTO & Enterprise Solutions Architect  
- **Email:** [mhd.shadi.alhasan@gmail.com](mailto:mhd.shadi.alhasan@gmail.com)  
- **Phone / WhatsApp:** [+963934005922](tel:+963934005922)  
- **Location:** Damascus, Syria  
- **GitHub:** [MobileConduit](https://github.com/MobileConduit)  

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.  
Copyright (c) 2026 **MHD. Shadi AL-Hasan**. All rights reserved.


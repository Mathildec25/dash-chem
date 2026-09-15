#!/bin/sh
# Nightly copy of what the chemists write. Install with:
#   chmod +x deploy/backup.sh
#   (crontab -l 2>/dev/null; echo "0 3 * * * /opt/reacto/deploy/backup.sh") | crontab -
# Copy /var/backups/reacto off the machine from time to time.
set -e
mkdir -p /var/backups/reacto
cd /opt/reacto
tar czf /var/backups/reacto/reacto_$(date +%F).tgz hitl_bench/forms/live data/excel_files data/domains 2>/dev/null || true
find /var/backups/reacto -name "reacto_*.tgz" -mtime +60 -delete

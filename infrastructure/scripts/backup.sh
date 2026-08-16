#!/bin/bash

# Configuration
BACKUP_DIR="/backups/postgres"
CONTAINER_NAME="erp-db"
DB_USER="postgres"
DB_NAME="erp"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/backup_${DB_NAME}_${DATE}.sql.gz"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

echo "Starting backup of database $DB_NAME..."

# Execute pg_dump within the container
docker exec $CONTAINER_NAME pg_dump -U $DB_USER -d $DB_NAME -F c | gzip > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Backup completed successfully: $BACKUP_FILE"
    
    # Clean up old backups
    echo "Cleaning up backups older than $RETENTION_DAYS days..."
    find "$BACKUP_DIR" -type f -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    
else
    echo "Backup failed!"
    exit 1
fi

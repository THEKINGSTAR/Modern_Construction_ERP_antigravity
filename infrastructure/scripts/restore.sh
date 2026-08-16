#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <path_to_backup_file.sql.gz>"
    exit 1
fi

BACKUP_FILE="$1"
CONTAINER_NAME="erp-db"
DB_USER="postgres"
DB_NAME="erp"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file $BACKUP_FILE does not exist."
    exit 1
fi

echo "Warning: This will overwrite the existing database '$DB_NAME'."
read -p "Are you sure you want to continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore aborted."
    exit 1
fi

echo "Starting restore from $BACKUP_FILE..."

# Drop and recreate the database to ensure a clean slate
docker exec $CONTAINER_NAME dropdb -U $DB_USER -f $DB_NAME
docker exec $CONTAINER_NAME createdb -U $DB_USER -O $DB_USER $DB_NAME

# Restore the dump
zcat "$BACKUP_FILE" | docker exec -i $CONTAINER_NAME pg_restore -U $DB_USER -d $DB_NAME --clean --if-exists

if [ $? -eq 0 ]; then
    echo "Restore completed successfully."
else
    echo "Restore failed!"
    exit 1
fi

#!/bin/bash

# Exit on error
set -e

# Configuration
BACKUP_DIR="/var/backups/qubit"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7
LOG_FILE="/var/log/qubit/backup.log"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Backup PostgreSQL
backup_postgres() {
    log "Starting PostgreSQL backup..."
    if docker-compose exec -T db pg_dump -U postgres qubit > "$BACKUP_DIR/db_$TIMESTAMP.sql"; then
        log "PostgreSQL backup completed successfully"
    else
        log "ERROR: PostgreSQL backup failed"
        return 1
    fi
}

# Backup Redis
backup_redis() {
    log "Starting Redis backup..."
    if docker-compose exec -T redis redis-cli SAVE; then
        log "Redis backup completed successfully"
    else
        log "ERROR: Redis backup failed"
        return 1
    fi
}

# Compress backups
compress_backups() {
    log "Compressing backups..."
    if gzip "$BACKUP_DIR/db_$TIMESTAMP.sql"; then
        log "Backup compression completed successfully"
    else
        log "ERROR: Backup compression failed"
        return 1
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log "Cleaning up old backups..."
    find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +"$RETENTION_DAYS" -delete
    log "Cleanup completed"
}

# Main backup process
main() {
    log "Starting backup process..."
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    
    # Perform backups
    backup_postgres
    backup_redis
    compress_backups
    cleanup_old_backups
    
    log "Backup process completed successfully"
}

# Run main function
main

# Check for errors
if [ $? -eq 0 ]; then
    log "Backup completed successfully"
    exit 0
else
    log "Backup failed"
    exit 1
fi 
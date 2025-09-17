"""
Data backup and recovery utilities for the expense management system.
Provides automated backup creation, restoration, and data integrity checks.
"""
import shutil
import gzip
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib

from .paths import DATA_DIR, PARQUET, EXCEL
from .logging_config import main_logger

logger = main_logger

class BackupManager:
    """Manages data backups and recovery operations"""

    def __init__(self, backup_dir: Optional[Path] = None):
        self.backup_dir = backup_dir or (DATA_DIR / "backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.max_backups = 30  # Keep last 30 days of backups

    def create_backup(self, backup_type: str = "auto") -> Optional[Path]:
        """
        Create a backup of current data.
        Returns the path to the backup file if successful.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{backup_type}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir()

            files_backed_up = []

            # Backup Parquet data file
            if PARQUET.exists():
                parquet_backup = backup_path / "data.parquet.gz"
                with open(PARQUET, 'rb') as src, gzip.open(parquet_backup, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
                files_backed_up.append("data.parquet")

            # Backup Excel file
            if EXCEL.exists():
                excel_backup = backup_path / "Presupuesto_Auto.xlsx"
                shutil.copy2(EXCEL, excel_backup)
                files_backed_up.append("Presupuesto_Auto.xlsx")

            # Create backup metadata
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "type": backup_type,
                "files": files_backed_up,
                "data_dir": str(DATA_DIR),
                "version": "1.0.0-alpha"
            }

            metadata_file = backup_path / "backup_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            # Create checksum for integrity verification
            checksum = self._calculate_backup_checksum(backup_path)
            checksum_file = backup_path / "backup_checksum.sha256"
            with open(checksum_file, 'w') as f:
                f.write(checksum)

            logger.info(f"Backup created successfully: {backup_name}", extra={
                "backup_name": backup_name,
                "files_backed_up": files_backed_up,
                "backup_path": str(backup_path)
            })

            # Clean up old backups
            self._cleanup_old_backups()

            return backup_path

        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}", exc_info=True)
            return None

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups with metadata"""
        backups = []

        if not self.backup_dir.exists():
            return backups

        for backup_dir in sorted(self.backup_dir.iterdir(), reverse=True):
            if not backup_dir.is_dir():
                continue

            metadata_file = backup_dir / "backup_metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)

                    # Check if backup is valid
                    checksum_file = backup_dir / "backup_checksum.sha256"
                    is_valid = self._verify_backup_integrity(backup_dir)

                    backups.append({
                        "name": backup_dir.name,
                        "path": str(backup_dir),
                        "timestamp": metadata.get("timestamp"),
                        "type": metadata.get("type", "unknown"),
                        "files": metadata.get("files", []),
                        "valid": is_valid,
                        "size_mb": self._calculate_backup_size(backup_dir)
                    })
                except Exception as e:
                    logger.warning(f"Could not read backup metadata for {backup_dir.name}: {e}")
                    backups.append({
                        "name": backup_dir.name,
                        "path": str(backup_dir),
                        "timestamp": None,
                        "type": "unknown",
                        "files": [],
                        "valid": False,
                        "size_mb": self._calculate_backup_size(backup_dir)
                    })

        return backups

    def restore_backup(self, backup_name: str) -> bool:
        """
        Restore data from a backup.
        Returns True if successful, False otherwise.
        """
        try:
            backup_path = self.backup_dir / backup_name

            if not backup_path.exists():
                logger.error(f"Backup not found: {backup_name}")
                return False

            # Verify backup integrity
            if not self._verify_backup_integrity(backup_path):
                logger.error(f"Backup integrity check failed: {backup_name}")
                return False

            # Create pre-restore backup
            pre_restore_backup = self.create_backup("pre_restore")
            if pre_restore_backup:
                logger.info(f"Created pre-restore backup: {pre_restore_backup.name}")

            restored_files = []

            # Restore Parquet data
            parquet_backup = backup_path / "data.parquet.gz"
            if parquet_backup.exists():
                with gzip.open(parquet_backup, 'rb') as src, open(PARQUET, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
                restored_files.append("data.parquet")

            # Restore Excel file
            excel_backup = backup_path / "Presupuesto_Auto.xlsx"
            if excel_backup.exists():
                shutil.copy2(excel_backup, EXCEL)
                restored_files.append("Presupuesto_Auto.xlsx")

            logger.info(f"Backup restored successfully: {backup_name}", extra={
                "backup_name": backup_name,
                "restored_files": restored_files
            })

            return True

        except Exception as e:
            logger.error(f"Failed to restore backup {backup_name}: {str(e)}", exc_info=True)
            return False

    def _calculate_backup_checksum(self, backup_path: Path) -> str:
        """Calculate SHA256 checksum of all files in backup"""
        sha256 = hashlib.sha256()

        for file_path in sorted(backup_path.rglob("*")):
            if file_path.is_file() and file_path.name != "backup_checksum.sha256":
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        sha256.update(chunk)

        return sha256.hexdigest()

    def _verify_backup_integrity(self, backup_path: Path) -> bool:
        """Verify backup integrity using stored checksum"""
        try:
            checksum_file = backup_path / "backup_checksum.sha256"
            if not checksum_file.exists():
                return False

            with open(checksum_file, 'r') as f:
                stored_checksum = f.read().strip()

            calculated_checksum = self._calculate_backup_checksum(backup_path)

            return stored_checksum == calculated_checksum

        except Exception as e:
            logger.error(f"Error verifying backup integrity: {e}")
            return False

    def _calculate_backup_size(self, backup_path: Path) -> float:
        """Calculate total size of backup in MB"""
        try:
            total_size = sum(
                f.stat().st_size for f in backup_path.rglob("*") if f.is_file()
            )
            return round(total_size / (1024 * 1024), 2)
        except Exception:
            return 0.0

    def _cleanup_old_backups(self):
        """Remove old backups to save space, keeping the most recent ones"""
        try:
            backups = []
            for backup_dir in self.backup_dir.iterdir():
                if backup_dir.is_dir() and backup_dir.name.startswith("backup_"):
                    # Extract timestamp from backup name
                    try:
                        # Format: backup_{type}_{YYYYMMDD_HHMMSS}
                        parts = backup_dir.name.split("_")
                        if len(parts) >= 3:
                            timestamp_str = parts[2]  # YYYYMMDD_HHMMSS
                            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                            backups.append((backup_dir, timestamp))
                    except ValueError:
                        # If we can't parse the timestamp, treat as very old
                        backups.append((backup_dir, datetime.min))

            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x[1], reverse=True)

            # Remove old backups
            for backup_dir, _ in backups[self.max_backups:]:
                try:
                    shutil.rmtree(backup_dir)
                    logger.info(f"Removed old backup: {backup_dir.name}")
                except Exception as e:
                    logger.warning(f"Failed to remove old backup {backup_dir.name}: {e}")

        except Exception as e:
            logger.error(f"Error during backup cleanup: {e}")

    def get_backup_stats(self) -> Dict[str, Any]:
        """Get statistics about backups"""
        backups = self.list_backups()

        total_size = sum(b.get("size_mb", 0) for b in backups)
        valid_backups = sum(1 for b in backups if b.get("valid", False))

        # Get latest backup info
        latest_backup = None
        if backups:
            latest_backup = backups[0]

        return {
            "total_backups": len(backups),
            "valid_backups": valid_backups,
            "total_size_mb": round(total_size, 2),
            "latest_backup": latest_backup,
            "backup_dir": str(self.backup_dir)
        }

# Global backup manager instance
backup_manager = BackupManager()

# Convenience functions
def create_backup(backup_type: str = "manual") -> Optional[Path]:
    """Create a backup with the specified type"""
    return backup_manager.create_backup(backup_type)

def list_backups() -> List[Dict[str, Any]]:
    """List all available backups"""
    return backup_manager.list_backups()

def restore_backup(backup_name: str) -> bool:
    """Restore from the specified backup"""
    return backup_manager.restore_backup(backup_name)

def get_backup_stats() -> Dict[str, Any]:
    """Get backup statistics"""
    return backup_manager.get_backup_stats()
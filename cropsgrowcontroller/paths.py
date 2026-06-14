"""Canonical filesystem paths for IPC and persistence."""

from pathlib import Path

# Volatile RAM disk (tmpfs) — all hot-path reads/writes land here.
RAM_DISK_ROOT: Path = Path("/tmp/grow_ram")

LIVE_JSON_PATH: Path = RAM_DISK_ROOT / "live.json"
CONFIG_JSON_PATH: Path = RAM_DISK_ROOT / "config.json"
RAM_DB_PATH: Path = RAM_DISK_ROOT / "grow_live.db"

# SD-card archive — written only by the 12-hour batch sync job.
ARCHIVE_DB_PATH: Path = Path("/home/pi/grow_archive.db")

# Default on-device project root (systemd WorkingDirectory).
PROJECT_ROOT: Path = Path("/home/pi/cropsgrowcontroller")

"""SQLite schema and row models for RAM-disk logging and SD-card archive."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from cropsgrowcontroller.models.enums import ControlMode, LightSchedulePhase
from cropsgrowcontroller.models.live import LiveState

SCHEMA_VERSION: int = 1

KLIMA_LOG_DDL: str = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS klima_log (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    recorded_at             TEXT    NOT NULL,
    temp1_c                 REAL    NOT NULL,
    temp2_c                 REAL    NOT NULL,
    avg_temp_c              REAL    NOT NULL,
    rh1_pct                 REAL    NOT NULL,
    rh2_pct                 REAL    NOT NULL,
    avg_rh_pct              REAL    NOT NULL,
    leaf_temp_c             REAL    NOT NULL,
    vpd_kpa                 REAL    NOT NULL,
    fan_speed_pct           INTEGER NOT NULL CHECK (fan_speed_pct BETWEEN 0 AND 100),
    light_intensity_pct     INTEGER NOT NULL CHECK (light_intensity_pct BETWEEN 0 AND 100),
    control_mode            TEXT    NOT NULL,
    light_phase             TEXT    NOT NULL,
    emergency_active        INTEGER NOT NULL DEFAULT 0 CHECK (emergency_active IN (0, 1)),
    consecutive_sensor_failures INTEGER NOT NULL DEFAULT 0 CHECK (consecutive_sensor_failures >= 0),
    last_error              TEXT,
    synced_to_archive       INTEGER NOT NULL DEFAULT 0 CHECK (synced_to_archive IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_klima_log_recorded_at
    ON klima_log (recorded_at);

CREATE INDEX IF NOT EXISTS idx_klima_log_synced
    ON klima_log (synced_to_archive, id);
"""

SCHEMA_META_INSERT_VERSION: str = """
INSERT OR REPLACE INTO schema_meta (key, value)
VALUES ('schema_version', ?);
"""

KLIMA_LOG_INSERT: str = """
INSERT INTO klima_log (
    recorded_at,
    temp1_c,
    temp2_c,
    avg_temp_c,
    rh1_pct,
    rh2_pct,
    avg_rh_pct,
    leaf_temp_c,
    vpd_kpa,
    fan_speed_pct,
    light_intensity_pct,
    control_mode,
    light_phase,
    emergency_active,
    consecutive_sensor_failures,
    last_error,
    synced_to_archive
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0);
"""


class KlimaLogRecord(BaseModel):
    """One row in the `klima_log` table."""

    model_config = ConfigDict(extra="forbid")

    id: int | None = None
    recorded_at: datetime
    temp1_c: float
    temp2_c: float
    avg_temp_c: float
    rh1_pct: float
    rh2_pct: float
    avg_rh_pct: float
    leaf_temp_c: float
    vpd_kpa: float = Field(ge=0.0)
    fan_speed_pct: int = Field(ge=0, le=100)
    light_intensity_pct: int = Field(ge=0, le=100)
    control_mode: ControlMode
    light_phase: LightSchedulePhase
    emergency_active: bool = False
    consecutive_sensor_failures: int = Field(default=0, ge=0)
    last_error: str | None = None
    synced_to_archive: bool = False

    @classmethod
    def from_live_state(cls, state: LiveState) -> KlimaLogRecord:
        """Map a live snapshot to a persistable database row."""
        sensors = state.sensors
        actuators = state.actuators
        control = state.control

        return cls(
            recorded_at=state.timestamp,
            temp1_c=sensors.canopy.temperature_c,
            temp2_c=sensors.intake.temperature_c,
            avg_temp_c=sensors.avg_temperature_c,
            rh1_pct=sensors.canopy.relative_humidity_pct,
            rh2_pct=sensors.intake.relative_humidity_pct,
            avg_rh_pct=sensors.avg_relative_humidity_pct,
            leaf_temp_c=sensors.leaf_temperature_c,
            vpd_kpa=sensors.vpd_kpa,
            fan_speed_pct=actuators.fan_speed_pct,
            light_intensity_pct=actuators.light_intensity_pct,
            control_mode=control.mode,
            light_phase=control.light_phase,
            emergency_active=control.emergency_active,
            consecutive_sensor_failures=control.consecutive_sensor_failures,
            last_error=control.last_error,
        )

    def insert_params(self) -> tuple[object, ...]:
        """Return positional parameters for `KLIMA_LOG_INSERT`."""
        return (
            self.recorded_at.isoformat(),
            self.temp1_c,
            self.temp2_c,
            self.avg_temp_c,
            self.rh1_pct,
            self.rh2_pct,
            self.avg_rh_pct,
            self.leaf_temp_c,
            self.vpd_kpa,
            self.fan_speed_pct,
            self.light_intensity_pct,
            self.control_mode.value,
            self.light_phase.value,
            int(self.emergency_active),
            self.consecutive_sensor_failures,
            self.last_error,
        )

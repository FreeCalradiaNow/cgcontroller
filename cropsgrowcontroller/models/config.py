"""Pydantic models for `/tmp/grow_ram/config.json` operator settings."""

from __future__ import annotations

import re
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


class ManualOverrides(BaseModel):
    """Optional operator overrides; when enabled, core defers to these setpoints."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    fan_speed_pct: int | None = Field(default=None, ge=0, le=100)
    light_intensity_pct: int | None = Field(default=None, ge=0, le=100)

    @model_validator(mode="after")
    def validate_override_values(self) -> Self:
        if self.enabled and self.fan_speed_pct is None and self.light_intensity_pct is None:
            raise ValueError(
                "manual_overrides.enabled requires at least one of "
                "fan_speed_pct or light_intensity_pct",
            )
        return self


class SystemConfig(BaseModel):
    """
    Operator-adjustable settings read by `controller_core.py`.

    Persisted to `/tmp/grow_ram/config.json` by the FastAPI backend.
    """

    model_config = ConfigDict(extra="forbid")

    # --- VPD & RH cascade thresholds ---
    target_vpd_kpa: float = Field(default=1.0, ge=0.4, le=2.5)
    min_rh_pct: float = Field(
        default=40.0,
        ge=0.0,
        le=100.0,
        description="Safety floor — fan retention profile below this RH",
    )
    max_rh_pct: float = Field(
        default=65.0,
        ge=0.0,
        le=100.0,
        description="Safety ceiling — fan extraction profile above this RH",
    )
    rh_stable_min_pct: float = Field(
        default=45.0,
        ge=0.0,
        le=100.0,
        description="Lower bound of the VPD-regulation RH band",
    )
    rh_stable_max_pct: float = Field(
        default=60.0,
        ge=0.0,
        le=100.0,
        description="Upper bound of the VPD-regulation RH band",
    )

    # --- VPD calculation ---
    leaf_temp_offset_c: float = Field(
        default=2.0,
        ge=0.0,
        le=10.0,
        description="Subtracted from air temp to estimate leaf temperature",
    )

    # --- Photoperiod (local wall-clock, HH:MM 24 h) ---
    light_on_time: str = Field(default="07:00", examples=["07:00"])
    light_off_time: str = Field(default="19:00", examples=["19:00"])
    sunrise_sunset_minutes: int = Field(
        default=30,
        ge=0,
        le=120,
        description="Linear dimming ramp duration at on/off transitions",
    )

    # --- Safety fan profiles (RH override branch) ---
    fan_speed_dehumidify_pct: int = Field(
        default=80,
        ge=0,
        le=100,
        description="Fan duty when RH exceeds max_rh_pct",
    )
    fan_speed_retention_pct: int = Field(
        default=15,
        ge=0,
        le=100,
        description="Fan duty when RH falls below min_rh_pct",
    )

    # --- Loop & archive timing ---
    loop_interval_seconds: float = Field(default=5.0, gt=0.0, le=60.0)
    archive_sync_interval_hours: float = Field(default=12.0, gt=0.0, le=168.0)

    manual_overrides: ManualOverrides = Field(default_factory=ManualOverrides)

    @field_validator("light_on_time", "light_off_time")
    @classmethod
    def validate_hh_mm(cls, value: str) -> str:
        if not _TIME_PATTERN.fullmatch(value):
            raise ValueError("Time must be formatted as HH:MM (24-hour clock)")
        return value

    @model_validator(mode="after")
    def validate_threshold_ordering(self) -> Self:
        if self.min_rh_pct >= self.max_rh_pct:
            raise ValueError("min_rh_pct must be strictly less than max_rh_pct")
        if self.rh_stable_min_pct >= self.rh_stable_max_pct:
            raise ValueError("rh_stable_min_pct must be strictly less than rh_stable_max_pct")
        if self.rh_stable_min_pct < self.min_rh_pct:
            raise ValueError("rh_stable_min_pct must be >= min_rh_pct")
        if self.rh_stable_max_pct > self.max_rh_pct:
            raise ValueError("rh_stable_max_pct must be <= max_rh_pct")
        if self.fan_speed_retention_pct >= self.fan_speed_dehumidify_pct:
            raise ValueError(
                "fan_speed_retention_pct must be less than fan_speed_dehumidify_pct",
            )
        return self

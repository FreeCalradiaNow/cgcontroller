"""Pydantic models for `/tmp/grow_ram/live.json` telemetry broadcast."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, computed_field

from cropsgrowcontroller.models.enums import ControlMode, LightSchedulePhase


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProbeReading(BaseModel):
    """Single SHT3x/40 probe sample."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    temperature_c: float = Field(description="Air temperature in °C")
    relative_humidity_pct: float = Field(ge=0.0, le=100.0, description="Relative humidity in %")


class SensorTelemetry(BaseModel):
    """Dual-probe readings, aggregates, and derived VPD."""

    model_config = ConfigDict(extra="forbid")

    canopy: ProbeReading = Field(description="Probe 1 — canopy (TCA9548A channel 0)")
    intake: ProbeReading = Field(description="Probe 2 — intake (TCA9548A channel 1)")
    avg_temperature_c: float = Field(description="Mean air temperature in °C")
    avg_relative_humidity_pct: float = Field(
        ge=0.0,
        le=100.0,
        description="Mean relative humidity in %",
    )
    leaf_temperature_c: float = Field(
        description="Estimated leaf temperature used for VPD (air temp − offset)",
    )
    vpd_kpa: float = Field(ge=0.0, description="Vapor pressure deficit in kPa (Magnus formula)")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def temp1_c(self) -> float:
        return self.canopy.temperature_c

    @computed_field  # type: ignore[prop-decorator]
    @property
    def temp2_c(self) -> float:
        return self.intake.temperature_c

    @computed_field  # type: ignore[prop-decorator]
    @property
    def rh1_pct(self) -> float:
        return self.canopy.relative_humidity_pct

    @computed_field  # type: ignore[prop-decorator]
    @property
    def rh2_pct(self) -> float:
        return self.intake.relative_humidity_pct

    @computed_field  # type: ignore[prop-decorator]
    @property
    def avg_temp_c(self) -> float:
        return self.avg_temperature_c

    @computed_field  # type: ignore[prop-decorator]
    @property
    def avg_rh_pct(self) -> float:
        return self.avg_relative_humidity_pct


class ActuatorState(BaseModel):
    """Current hardware output levels."""

    model_config = ConfigDict(extra="forbid")

    fan_speed_pct: int = Field(ge=0, le=100, description="AeroZesh G8 PWM duty cycle")
    light_intensity_pct: int = Field(
        ge=0,
        le=100,
        description="XLED 720W intensity via PCA9685 → 0–10 V DAC",
    )


class ControlStatus(BaseModel):
    """Runtime control and health metadata."""

    model_config = ConfigDict(extra="forbid")

    mode: ControlMode = ControlMode.VPD_REGULATION
    light_phase: LightSchedulePhase = LightSchedulePhase.OFF
    emergency_active: bool = False
    consecutive_sensor_failures: int = Field(default=0, ge=0)
    last_error: str | None = None


class LiveState(BaseModel):
    """
    Authoritative live snapshot written by `controller_core.py` every loop.

    Serialized to `/tmp/grow_ram/live.json` for consumption by the API and UI.
    """

    model_config = ConfigDict(extra="forbid")

    timestamp: datetime = Field(default_factory=utc_now)
    sensors: SensorTelemetry
    actuators: ActuatorState
    control: ControlStatus = Field(default_factory=ControlStatus)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def vpd_kpa(self) -> float:
        return self.sensors.vpd_kpa

    @computed_field  # type: ignore[prop-decorator]
    @property
    def fan_speed_pct(self) -> int:
        return self.actuators.fan_speed_pct

    @computed_field  # type: ignore[prop-decorator]
    @property
    def light_intensity_pct(self) -> int:
        return self.actuators.light_intensity_pct

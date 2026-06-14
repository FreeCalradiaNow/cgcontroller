"""VPD calculation using the Magnus saturation vapor pressure formula."""

from __future__ import annotations

import math

from cropsgrowcontroller.models.live import ProbeReading, SensorTelemetry

# Magnus coefficients for saturation vapor pressure over liquid water (°C → kPa).
_MAGNUS_A: float = 0.6108
_MAGNUS_B: float = 17.27
_MAGNUS_C: float = 237.3


def saturation_vapor_pressure_kpa(temperature_c: float) -> float:
    """Return saturation vapor pressure (kPa) at ``temperature_c``."""
    exponent = (_MAGNUS_B * temperature_c) / (temperature_c + _MAGNUS_C)
    return _MAGNUS_A * math.exp(exponent)


def calculate_vpd_kpa(
    air_temperature_c: float,
    relative_humidity_pct: float,
    leaf_temperature_c: float,
) -> float:
    """
    Compute VPD (kPa) from air conditions and estimated leaf temperature.

    VPD = SVP(leaf) − AVP(air), where AVP = SVP(air) × RH/100.
    """
    svp_leaf_kpa = saturation_vapor_pressure_kpa(leaf_temperature_c)
    svp_air_kpa = saturation_vapor_pressure_kpa(air_temperature_c)
    actual_vapor_pressure_kpa = svp_air_kpa * (relative_humidity_pct / 100.0)
    return max(0.0, svp_leaf_kpa - actual_vapor_pressure_kpa)


def build_sensor_telemetry(
    canopy: ProbeReading,
    intake: ProbeReading,
    leaf_temp_offset_c: float,
) -> SensorTelemetry:
    """Average dual-probe readings and derive leaf temperature + VPD."""
    avg_temperature_c = (canopy.temperature_c + intake.temperature_c) / 2.0
    avg_relative_humidity_pct = (
        canopy.relative_humidity_pct + intake.relative_humidity_pct
    ) / 2.0
    leaf_temperature_c = avg_temperature_c - leaf_temp_offset_c
    vpd_kpa = calculate_vpd_kpa(
        air_temperature_c=avg_temperature_c,
        relative_humidity_pct=avg_relative_humidity_pct,
        leaf_temperature_c=leaf_temperature_c,
    )

    return SensorTelemetry(
        canopy=canopy,
        intake=intake,
        avg_temperature_c=avg_temperature_c,
        avg_relative_humidity_pct=avg_relative_humidity_pct,
        leaf_temperature_c=leaf_temperature_c,
        vpd_kpa=vpd_kpa,
    )

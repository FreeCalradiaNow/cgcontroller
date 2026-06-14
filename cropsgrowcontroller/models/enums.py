"""Shared enumerations for control logic and persistence."""

from enum import StrEnum


class ControlMode(StrEnum):
    """Active control strategy for the current loop iteration."""

    VPD_REGULATION = "vpd_regulation"
    RH_HIGH = "rh_high"
    RH_LOW = "rh_low"
    MANUAL = "manual"
    EMERGENCY = "emergency"


class LightSchedulePhase(StrEnum):
    """Software-timer phase for the 30-minute sunrise/sunset ramp."""

    OFF = "off"
    SUNRISE = "sunrise"
    ON = "on"
    SUNSET = "sunset"

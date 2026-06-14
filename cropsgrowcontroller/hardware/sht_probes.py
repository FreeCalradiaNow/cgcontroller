"""Dual SHT4x probe reader via TCA9548A multiplexer."""

from __future__ import annotations

import logging
import os
from typing import Any, Protocol

from cropsgrowcontroller.climate.vpd import build_sensor_telemetry
from cropsgrowcontroller.hardware.constants import (
    CANOPY_PROBE_CHANNEL,
    INTAKE_PROBE_CHANNEL,
    TCA9548A_DEFAULT_ADDRESS,
)
from cropsgrowcontroller.hardware.exceptions import SensorReadError
from cropsgrowcontroller.hardware.tca9548a import Tca9548a
from cropsgrowcontroller.models.live import ProbeReading, SensorTelemetry

logger = logging.getLogger(__name__)


class DualShtProbeReader(Protocol):
    """Interface consumed by ``controller_core.py``."""

    def read_telemetry(self, leaf_temp_offset_c: float) -> SensorTelemetry:
        """Return averaged probe data with derived VPD."""


class HardwareDualShtProbeReader:
    """Read canopy and intake SHT4x probes through a TCA9548A multiplexer."""

    def __init__(
        self,
        i2c: Any,
        mux_address: int = TCA9548A_DEFAULT_ADDRESS,
    ) -> None:
        self._i2c = i2c
        self._mux = Tca9548a(i2c, address=mux_address)

    def _read_channel(self, channel: int) -> ProbeReading:
        import adafruit_sht4x

        self._mux.select_channel(channel)
        try:
            sensor = adafruit_sht4x.SHT4x(self._i2c)
            temperature_c, relative_humidity = sensor.measurements
        except (OSError, RuntimeError, ValueError) as exc:
            raise SensorReadError(
                f"SHT probe read failed on TCA9548A channel {channel}",
            ) from exc

        return ProbeReading(
            temperature_c=float(temperature_c),
            relative_humidity_pct=float(relative_humidity),
        )

    def read_telemetry(self, leaf_temp_offset_c: float) -> SensorTelemetry:
        try:
            canopy = self._read_channel(CANOPY_PROBE_CHANNEL)
            intake = self._read_channel(INTAKE_PROBE_CHANNEL)
            return build_sensor_telemetry(canopy, intake, leaf_temp_offset_c)
        finally:
            try:
                self._mux.disable_all()
            except Exception:
                logger.warning("Failed to deselect TCA9548A channels after probe read", exc_info=True)


class SimulatedDualShtProbeReader:
    """Deterministic probe values for off-device development and CI."""

    _CANOPY_BASE: ProbeReading = ProbeReading(
        temperature_c=24.6,
        relative_humidity_pct=58.0,
    )
    _INTAKE_BASE: ProbeReading = ProbeReading(
        temperature_c=23.1,
        relative_humidity_pct=54.5,
    )

    def read_telemetry(self, leaf_temp_offset_c: float) -> SensorTelemetry:
        logger.debug("Returning simulated SHT probe telemetry")
        return build_sensor_telemetry(
            self._CANOPY_BASE,
            self._INTAKE_BASE,
            leaf_temp_offset_c,
        )


def _hardware_available() -> bool:
    try:
        import board  # type: ignore[import-untyped]
        import busio  # type: ignore[import-untyped]

        _ = board, busio
        return True
    except ImportError:
        return False


def create_dual_probe_reader(
    *,
    simulate: bool | None = None,
    mux_address: int = TCA9548A_DEFAULT_ADDRESS,
) -> DualShtProbeReader:
    """
    Build a probe reader for the current environment.

    Simulation is enabled when ``simulate=True``, when ``CROPSGROW_SIMULATE`` is
    set, or when Blinka/board libraries are unavailable (e.g. dev laptop).
    """
    if simulate is None:
        env_flag = os.environ.get("CROPSGROW_SIMULATE", "").lower()
        simulate = env_flag in {"1", "true", "yes"} or not _hardware_available()

    if simulate:
        logger.info("Using simulated dual SHT probe reader")
        return SimulatedDualShtProbeReader()

    import board  # type: ignore[import-untyped]
    import busio  # type: ignore[import-untyped]

    i2c = busio.I2C(board.SCL, board.SDA)
    logger.info(
        "Initialized I2C bus for TCA9548A @ 0x%02X (canopy ch%d, intake ch%d)",
        mux_address,
        CANOPY_PROBE_CHANNEL,
        INTAKE_PROBE_CHANNEL,
    )
    return HardwareDualShtProbeReader(i2c, mux_address=mux_address)

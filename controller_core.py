#!/usr/bin/env python3
"""
Process 1 — background climate controller daemon.

Task 2.1: initialize the TCA9548A multiplexer, read dual SHT probes,
average readings, and compute live VPD via the Magnus formula.
"""

from __future__ import annotations

import logging
import signal
import sys
import time
from typing import Final

from cropsgrowcontroller.hardware.exceptions import SensorReadError
from cropsgrowcontroller.hardware.sht_probes import DualShtProbeReader, create_dual_probe_reader
from cropsgrowcontroller.models.config import SystemConfig
from cropsgrowcontroller.models.live import ActuatorState, ControlStatus, LiveState, utc_now

logger = logging.getLogger(__name__)

_SHUTDOWN_REQUESTED: bool = False
_LOG_FORMAT: Final[str] = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def _request_shutdown(signum: int, _frame: object | None) -> None:
    global _SHUTDOWN_REQUESTED
    logger.info("Received signal %s — shutting down", signum)
    _SHUTDOWN_REQUESTED = True


def initialize_probe_reader() -> DualShtProbeReader:
    """Create the dual SHT probe reader (hardware or simulated)."""
    reader = create_dual_probe_reader()
    logger.info("Probe reader ready")
    return reader


def fetch_sensor_telemetry(
    reader: DualShtProbeReader,
    config: SystemConfig,
) -> LiveState:
    """
    Read both probes, average values, and calculate VPD.

    Returns a ``LiveState`` snapshot with sensor telemetry populated.
    Actuator fields remain at safe placeholders until Tasks 2.2–2.3.
    """
    sensors = reader.read_telemetry(leaf_temp_offset_c=config.leaf_temp_offset_c)

    return LiveState(
        timestamp=utc_now(),
        sensors=sensors,
        actuators=ActuatorState(fan_speed_pct=0, light_intensity_pct=0),
        control=ControlStatus(last_error=None),
    )


def run_controller_loop(
    reader: DualShtProbeReader,
    config: SystemConfig,
) -> None:
    """Main polling loop — one sensor read per iteration."""
    consecutive_failures = 0

    while not _SHUTDOWN_REQUESTED:
        loop_started = time.monotonic()

        try:
            live_state = fetch_sensor_telemetry(reader, config)
            consecutive_failures = 0

            sensors = live_state.sensors
            logger.info(
                "canopy=%.1f°C/%.1f%%RH intake=%.1f°C/%.1f%%RH "
                "avg=%.1f°C/%.1f%%RH leaf=%.1f°C vpd=%.2f kPa",
                sensors.canopy.temperature_c,
                sensors.canopy.relative_humidity_pct,
                sensors.intake.temperature_c,
                sensors.intake.relative_humidity_pct,
                sensors.avg_temperature_c,
                sensors.avg_relative_humidity_pct,
                sensors.leaf_temperature_c,
                sensors.vpd_kpa,
            )
        except SensorReadError as exc:
            consecutive_failures += 1
            logger.error(
                "Sensor read failed (%d consecutive): %s",
                consecutive_failures,
                exc,
            )
            # Emergency fail-safe handling is implemented in Task 3.3.

        elapsed = time.monotonic() - loop_started
        sleep_seconds = max(0.0, config.loop_interval_seconds - elapsed)
        time.sleep(sleep_seconds)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format=_LOG_FORMAT)

    signal.signal(signal.SIGTERM, _request_shutdown)
    signal.signal(signal.SIGINT, _request_shutdown)

    config = SystemConfig()

    try:
        reader = initialize_probe_reader()
    except Exception:
        logger.exception("Failed to initialize probe reader")
        return 1

    logger.info(
        "CropsGrowController core started (leaf offset=%.1f°C, loop=%.1fs)",
        config.leaf_temp_offset_c,
        config.loop_interval_seconds,
    )

    try:
        run_controller_loop(reader, config)
    except Exception:
        logger.exception("Unhandled error in controller loop")
        return 1

    logger.info("CropsGrowController core stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())

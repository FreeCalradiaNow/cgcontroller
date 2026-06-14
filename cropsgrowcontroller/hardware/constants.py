"""I2C addresses and channel map for the grow cabinet sensor bus."""

from typing import Final

# TCA9548A default address (A0–A2 strapped low).
TCA9548A_DEFAULT_ADDRESS: Final[int] = 0x70

# Probe placement on the multiplexer.
CANOPY_PROBE_CHANNEL: Final[int] = 0
INTAKE_PROBE_CHANNEL: Final[int] = 1

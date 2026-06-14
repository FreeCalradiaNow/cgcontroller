"""TCA9548A I2C multiplexer driver."""

from __future__ import annotations

import time
from typing import Any, Final

from cropsgrowcontroller.hardware.constants import TCA9548A_DEFAULT_ADDRESS
from cropsgrowcontroller.hardware.exceptions import HardwareError

_CHANNEL_COUNT: Final[int] = 8
_CHANNEL_SETTLE_SECONDS: Final[float] = 0.01


class Tca9548a:
    """Select one downstream I2C channel on a TCA9548A multiplexer."""

    def __init__(self, i2c: Any, address: int = TCA9548A_DEFAULT_ADDRESS) -> None:
        self._i2c = i2c
        self._address = address

    def select_channel(self, channel: int) -> None:
        """Route the upstream I2C bus to ``channel`` (0–7)."""
        if not 0 <= channel < _CHANNEL_COUNT:
            raise ValueError(f"TCA9548A channel must be 0–7, got {channel}")

        mask = 1 << channel
        try:
            while not self._i2c.try_lock():
                pass
            self._i2c.writeto(self._address, bytes([mask]))
        except OSError as exc:
            raise HardwareError(
                f"Failed to select TCA9548A channel {channel} at 0x{self._address:02X}",
            ) from exc
        finally:
            self._i2c.unlock()

        time.sleep(_CHANNEL_SETTLE_SECONDS)

    def disable_all(self) -> None:
        """Deselect every downstream channel."""
        try:
            while not self._i2c.try_lock():
                pass
            self._i2c.writeto(self._address, b"\x00")
        except OSError as exc:
            raise HardwareError(
                f"Failed to disable all TCA9548A channels at 0x{self._address:02X}",
            ) from exc
        finally:
            self._i2c.unlock()

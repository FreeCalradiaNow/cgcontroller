"""Hardware-layer exceptions."""


class HardwareError(Exception):
    """Base class for I2C / actuator failures."""


class SensorReadError(HardwareError):
    """Raised when a probe read through the multiplexer fails."""

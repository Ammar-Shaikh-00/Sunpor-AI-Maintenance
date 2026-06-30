"""
WinCC-style MQTT signal definitions for local subscriber testing.

Tags must match backend signal catalog wincc_tag values.
"""

import math
import random


def _sin_value(tick: float, base: float, amplitude: float, period: float, jitter: float = 0.0) -> float:
    return round(base + math.sin(tick / period) * amplitude + random.uniform(-jitter, jitter), 2)


SIGNAL_GENERATORS: dict[str, callable] = {
    "S7HMI030.WinCC.E10L_Heizzone1TemperaturIstwert": lambda t: _sin_value(t, 180, 5, 20, 1),
    "S7HMI030.WinCC.E10L_Heizzone2TemperaturIstwert": lambda t: _sin_value(t, 182, 5, 20, 1),
    "S7HMI030.WinCC.E10L_Heizzone3TemperaturIstwert": lambda t: _sin_value(t, 184, 5, 20, 1),
    "S7HMI030.WinCC.E10L_ExtruderDrehzahl": lambda t: _sin_value(t, 1250, 30, 15, 5),
    "S7HMI030.WinCC.E10L_ExtruderDrehmoment": lambda t: _sin_value(t, 72, 4, 12, 1),
    "S7HMI030.WinCC.E10L_MasseDruck01": lambda t: _sin_value(t, 120, 10, 10, 0.5),
    "S7HMI030.WinCC.E10L_MasseDruck02": lambda t: _sin_value(t, 118, 10, 10, 0.5),
    "S7HMI030.WinCC.E10L_MasseDruck03": lambda t: _sin_value(t, 116, 10, 10, 0.5),
    "S7HMI030.WinCC.E10L_MasseDruck04": lambda t: _sin_value(t, 114, 10, 10, 0.5),
    "S7HMI030.WinCC.E10L_GesamtDurchsatzIstwert": lambda t: _sin_value(t, 1050, 50, 15, 10),
    "S7HMI030.WinCC.EX10I121_masse": lambda t: _sin_value(t, 20, 1, 18, 0.3),
    "S7HMI030.WinCC.EX10X132.Flow_Ist": lambda t: _sin_value(t, 8, 0.5, 16, 0.1),
    "S7HMI030.WinCC.E10GGranulatorDrehzahl": lambda t: _sin_value(t, 1500, 20, 14, 3),
    "S7HMI030.WinCC.E10GGranulatorDrehmoment": lambda t: _sin_value(t, 35, 3, 11, 0.5),
    "S7HMI030.WinCC.E10L_Heizzone4TemperaturIstwert": lambda t: _sin_value(t, 186, 5, 20, 1),
    "S7HMI030.WinCC.E10L_Heizzone5TemperaturIstwert": lambda t: _sin_value(t, 188, 5, 20, 1),
}

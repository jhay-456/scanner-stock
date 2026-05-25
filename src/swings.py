"""Swing-high / swing-low detection for the higher-high / higher-low rules.

A pivot at index i is confirmed when its value is the strict extreme over
`window` bars on each side. Because confirmation needs `window` future bars,
the most recent detectable pivot is `window` bars old — fine for an EOD scan.
"""
from typing import List, Tuple, Sequence

Pivot = Tuple[int, float]


def swing_highs(values: Sequence[float], window: int) -> List[Pivot]:
    out: List[Pivot] = []
    n = len(values)
    for i in range(window, n - window):
        v = values[i]
        left = values[i - window:i]
        right = values[i + 1:i + window + 1]
        if v > max(left) and v > max(right):
            out.append((i, float(v)))
    return out


def swing_lows(values: Sequence[float], window: int) -> List[Pivot]:
    out: List[Pivot] = []
    n = len(values)
    for i in range(window, n - window):
        v = values[i]
        left = values[i - window:i]
        right = values[i + 1:i + window + 1]
        if v < min(left) and v < min(right):
            out.append((i, float(v)))
    return out


def is_higher_high(high_values: Sequence[float], window: int) -> bool:
    """True when the latest swing high exceeds the prior swing high."""
    highs = swing_highs(high_values, window)
    if len(highs) < 2:
        return False
    return highs[-1][1] > highs[-2][1]


def is_higher_low(low_values: Sequence[float], window: int) -> bool:
    """True when the latest swing low exceeds the prior swing low."""
    lows = swing_lows(low_values, window)
    if len(lows) < 2:
        return False
    return lows[-1][1] > lows[-2][1]

"""Signal generation utilities for the trading agent core."""

from __future__ import annotations

from statistics import mean


class SignalGenerator:
    """Generates BUY/SELL/HOLD signals from price history."""

    def __init__(
        self,
        fast_window: int = 3,
        slow_window: int = 10,
        volume_window: int = 5,
        min_confidence: float = 0.51,
    ):
        self.fast_window = fast_window
        self.slow_window = slow_window
        self.volume_window = volume_window
        self.min_confidence = min_confidence

    def _sma(self, values: list[float], period: int) -> float | None:
        if len(values) < period:
            return None
        return sum(values[-period:]) / period

    def generate(self, history: list[dict]) -> tuple[str, float, str]:
        """Generate a signal from OHLCV history."""
        if len(history) < self.slow_window:
            return "HOLD", 0.0, "Not enough history"

        closes = [float(item["close"]) for item in history]

        fast_sma = self._sma(closes, self.fast_window)
        slow_sma = self._sma(closes, self.slow_window)

        if fast_sma is None or slow_sma is None:
            return "HOLD", 0.0, "Insufficient history"

        diff = (fast_sma - slow_sma) / slow_sma
        
        # Simple momentum check
        momentum = (closes[-1] - closes[-2]) / closes[-2] if len(closes) >= 2 else 0.0

        # BUY: fast above slow AND price moved up
        if diff > 0.001 and momentum > 0:
            confidence = min(0.95, 0.55 + abs(diff) * 100)
            return "BUY", round(confidence, 3), f"Fast SMA > Slow SMA, momentum up"

        # SELL: fast below slow AND price moved down
        if diff < -0.001 and momentum < 0:
            confidence = min(0.95, 0.55 + abs(diff) * 100)
            return "SELL", round(confidence, 3), f"Fast SMA < Slow SMA, momentum down"

        return "HOLD", 0.0, "No clear signal"

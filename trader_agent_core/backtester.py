"""Backtesting infrastructure for the trader agent core."""

from __future__ import annotations

from dataclasses import dataclass

from trader_agent_core.broker import SimulatedBroker
from trader_agent_core.exits import ExitEngine
from trader_agent_core.journal import DecisionJournal
from trader_agent_core.models import Portfolio, RiskLimits
from trader_agent_core.signal import SignalGenerator


@dataclass
class BacktestMetrics:
    """Results from a backtest run."""
    initial_cash: float
    final_cash: float
    total_return: float
    num_trades: int
    wins: int
    losses: int
    win_rate: float
    max_drawdown: float
    avg_trade_return: float


class SimpleBacktester:
    """Simple backtest engine that tracks entry/exit signals."""

    def __init__(
        self,
        symbol: str = "AAPL",
        signal_generator: SignalGenerator | None = None,
    ):
        self.symbol = symbol
        self.signal_generator = signal_generator or SignalGenerator()

    def run(
        self,
        history: list[dict],
        initial_cash: float = 100000.0,
    ) -> tuple[list[dict], BacktestMetrics]:
        """Run a simple backtest."""
        trades: list[dict] = []
        cash = initial_cash
        position: dict | None = None
        last_peak = initial_cash
        max_drawdown = 0.0

        for idx, row in enumerate(history):
            current_price = float(row["close"])
            window = history[max(0, idx - 25):idx + 1]
            signal, confidence, rationale = self.signal_generator.generate(window)

            # Entry logic
            if signal == "BUY" and confidence > 0.60 and position is None:
                shares = (cash * 0.95) / current_price  # Use 95% of cash
                position = {
                    "entry_date": row["date"],
                    "entry_price": current_price,
                    "shares": shares,
                    "entry_confidence": confidence,
                }
                cash -= shares * current_price
                trades.append({
                    "type": "ENTRY",
                    "date": row["date"],
                    "price": current_price,
                    "shares": shares,
                    "signal": signal,
                    "confidence": confidence,
                })

            # Exit logic
            if position is not None and signal == "SELL" and confidence > 0.60:
                exit_proceeds = position["shares"] * current_price
                profit = exit_proceeds - (position["shares"] * position["entry_price"])
                cash += exit_proceeds
                trades.append({
                    "type": "EXIT",
                    "date": row["date"],
                    "price": current_price,
                    "shares": position["shares"],
                    "entry_price": position["entry_price"],
                    "profit": profit,
                    "signal": signal,
                    "confidence": confidence,
                })
                position = None

            # Track equity
            if position is not None:
                equity = cash + (position["shares"] * current_price)
            else:
                equity = cash

            if equity > last_peak:
                last_peak = equity
            drawdown = (last_peak - equity) / last_peak if last_peak > 0 else 0.0
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # Close any open position at end
        final_price = float(history[-1]["close"])
        if position is not None:
            exit_proceeds = position["shares"] * final_price
            profit = exit_proceeds - (position["shares"] * position["entry_price"])
            cash += exit_proceeds
            trades.append({
                "type": "EXIT",
                "date": history[-1]["date"],
                "price": final_price,
                "shares": position["shares"],
                "entry_price": position["entry_price"],
                "profit": profit,
                "signal": "END",
                "confidence": 1.0,
            })

        final_cash = cash
        total_return = (final_cash - initial_cash) / initial_cash

        # Count wins/losses
        exit_trades = [t for t in trades if t["type"] == "EXIT"]
        wins = sum(1 for t in exit_trades if t["profit"] > 0)
        losses = sum(1 for t in exit_trades if t["profit"] <= 0)
        num_trades = len(exit_trades)

        win_rate = wins / num_trades if num_trades > 0 else 0.0
        avg_trade_return = total_return / num_trades if num_trades > 0 else 0.0

        metrics = BacktestMetrics(
            initial_cash=initial_cash,
            final_cash=final_cash,
            total_return=total_return,
            num_trades=num_trades,
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            max_drawdown=max_drawdown,
            avg_trade_return=avg_trade_return,
        )
        return trades, metrics


class BacktestEngine:
    """Legacy wrapper for compatibility."""

    def __init__(
        self,
        symbol: str,
        risk_limits: RiskLimits,
        broker: SimulatedBroker,
        exit_engine: ExitEngine,
        journal: DecisionJournal | None = None,
        signal_generator: SignalGenerator | None = None,
    ):
        self.symbol = symbol
        self.risk_limits = risk_limits
        self.broker = broker
        self.exit_engine = exit_engine
        self.journal = journal or DecisionJournal()
        self.signal_generator = signal_generator or SignalGenerator()
        self.backtest = SimpleBacktester(symbol, signal_generator)

    def run(
        self,
        history: list[dict],
        initial_cash: float = 100000.0,
    ) -> tuple[Portfolio, BacktestMetrics]:
        """Run a backtest."""
        trades, metrics = self.backtest.run(history, initial_cash)
        portfolio = Portfolio(cash=metrics.final_cash)
        return portfolio, metrics


def generate_sample_history(
    start_price: float = 100.0,
    length: int = 120,
    drift: float = 0.002,
    volatility: float = 0.015,
) -> list[dict]:
    """Generate a simple synthetic OHLCV history for testing."""
    history: list[dict] = []
    current = start_price
    for i in range(length):
        change = (i / max(length, 1)) * drift + ((i % 7) - 3) * volatility / 30
        close = current * (1 + change)
        open_price = current
        high = max(open_price, close) * (1 + volatility * 0.5)
        low = min(open_price, close) * (1 - volatility * 0.5)
        volume = 1000 + ((i * 137) % 5000)
        history.append(
            {
                "date": f"2024-01-{(i % 28) + 1:02d}",
                "open": round(open_price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": int(volume),
            }
        )
        current = close
    return history

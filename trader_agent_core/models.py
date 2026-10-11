"""Core data models for the trading agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class Position:
    """Represents a single position in a symbol."""
    symbol: str
    qty: float
    avg_price: float
    side: Literal["LONG", "SHORT"] = "LONG"


@dataclass
class RiskLimits:
    """Risk constraints for the trader."""
    max_position_per_symbol: float = 1000.0
    max_gross_exposure: float = 0.40
    max_daily_loss: float = 0.02
    max_drawdown: float = 0.10
    max_trade_risk_pct: float = 0.005


@dataclass
class Order:
    """An order to be executed."""
    symbol: str
    side: Literal["BUY", "SELL"]
    qty: float
    order_type: Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"] = "MARKET"
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    tif: str = "DAY"


@dataclass
class Fill:
    """Represents an executed fill."""
    symbol: str
    side: str
    qty: float
    fill_price: float
    slippage: float
    timestamp: str
    status: str = "FILLED"


@dataclass
class ExitPlan:
    """Exit strategy for a position."""
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None
    max_holding_days: Optional[int] = None


@dataclass
class TradingDecision:
    """A decision made by the trading agent."""
    symbol: str
    action: Literal["BUY", "SELL", "HOLD"]
    confidence: float
    rationale: str
    risk_budget: float
    exit_plan: ExitPlan = field(default_factory=ExitPlan)


@dataclass
class Portfolio:
    """Represents the trader's current portfolio."""
    cash: float
    positions: dict[str, Position] = field(default_factory=dict)

    def position_for(self, symbol: str) -> Position | None:
        """Get a position by symbol."""
        return self.positions.get(symbol)

    def total_market_value(self, price_map: dict[str, float]) -> float:
        """Calculate total portfolio market value."""
        total = 0.0
        for pos in self.positions.values():
            price = price_map.get(pos.symbol, pos.avg_price)
            total += pos.qty * price
        return total

    def gross_exposure(self) -> float:
        """Calculate total gross exposure across all positions."""
        return sum(abs(p.qty * p.avg_price) for p in self.positions.values())

    def copy(self) -> Portfolio:
        """Create a deep copy of the portfolio."""
        return Portfolio(
            cash=self.cash,
            positions={
                k: Position(
                    symbol=v.symbol,
                    qty=v.qty,
                    avg_price=v.avg_price,
                    side=v.side,
                )
                for k, v in self.positions.items()
            },
        )

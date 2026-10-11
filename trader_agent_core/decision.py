"""Decision loop that ties together the entire trading system."""

from __future__ import annotations

from typing import Literal

from trader_agent_core.broker import SimulatedBroker
from trader_agent_core.exits import ExitEngine
from trader_agent_core.journal import DecisionJournal
from trader_agent_core.models import (
    ExitPlan,
    Fill,
    Order,
    Portfolio,
    Position,
    RiskLimits,
    TradingDecision,
)
from trader_agent_core.risk import RiskValidator


class MinimalDecisionLoop:
    """Orchestrates the trading decision process."""

    def __init__(
        self,
        portfolio: Portfolio,
        risk_limits: RiskLimits,
        broker: SimulatedBroker,
        exit_engine: ExitEngine,
        journal: DecisionJournal,
    ):
        """Initialize the decision loop.

        Args:
            portfolio: Current portfolio state
            risk_limits: Risk constraints
            broker: Simulated broker for fills
            exit_engine: Exit logic engine
            journal: Audit journal
        """
        self.portfolio = portfolio
        self.risk_limits = risk_limits
        self.broker = broker
        self.exit_engine = exit_engine
        self.journal = journal
        self.validator = RiskValidator(risk_limits)

    def decide(
        self,
        symbol: str,
        signal: Literal["BUY", "SELL", "HOLD"],
        confidence: float,
        market_price: float,
        rationale: str,
        quantity: float | None = None,
    ) -> tuple[TradingDecision, Fill | None]:
        """Make a trading decision and execute it.

        Args:
            symbol: The symbol to trade
            signal: BUY, SELL, or HOLD
            confidence: Confidence level (0.0-1.0)
            market_price: Current market price
            rationale: Reason for the decision
            quantity: Optional override for order size

        Returns:
            Tuple of (TradingDecision, Fill or None)
        """
        if signal == "HOLD":
            decision = TradingDecision(
                symbol=symbol,
                action="HOLD",
                confidence=confidence,
                rationale=rationale,
                risk_budget=0.0,
            )
            self.journal.add(
                "decision",
                symbol=symbol,
                action="HOLD",
                confidence=confidence,
                rationale=rationale,
            )
            return decision, None

        # Determine order size based on confidence and optional override
        if quantity is None:
            if confidence >= 0.75:
                quantity = 200.0
            elif confidence >= 0.60:
                quantity = 100.0
            else:
                quantity = 50.0

        side = "BUY" if signal == "BUY" else "SELL"
        order = Order(symbol=symbol, side=side, qty=quantity, order_type="MARKET")

        # Validate against risk limits
        is_valid, reason = self.validator.validate_new_order(
            self.portfolio, order, market_price
        )
        if not is_valid:
            decision = TradingDecision(
                symbol=symbol,
                action="HOLD",
                confidence=confidence,
                rationale=f"Rejected by risk validation: {reason}",
                risk_budget=0.0,
            )
            self.journal.add(
                "decision_rejected",
                symbol=symbol,
                signal=signal,
                confidence=confidence,
                rejection_reason=reason,
            )
            return decision, None

        # Execute the fill
        fill = self.broker.fill(order, market_price)
        self.journal.add(
            "fill",
            symbol=symbol,
            side=side,
            qty=quantity,
            fill_price=fill.fill_price,
            slippage=fill.slippage,
        )

        # Update portfolio position
        self._update_position(symbol, side, quantity, fill.fill_price)

        # Create exit plan
        exit_plan = self.exit_engine.create_exit_plan(
            self.portfolio.position_for(symbol), trailing_stop=True
        )

        # Create decision record
        decision = TradingDecision(
            symbol=symbol,
            action=side,
            confidence=confidence,
            rationale=rationale,
            risk_budget=quantity * market_price * self.risk_limits.max_trade_risk_pct,
            exit_plan=exit_plan,
        )
        self.journal.add(
            "decision",
            symbol=symbol,
            action=side,
            confidence=confidence,
            quantity=quantity,
            fill_price=fill.fill_price,
            rationale=rationale,
        )

        return decision, fill

    def _update_position(
        self, symbol: str, side: str, qty: float, fill_price: float
    ) -> None:
        """Update portfolio position after a fill."""
        current = self.portfolio.position_for(symbol)

        if current is None:
            # New position
            self.portfolio.positions[symbol] = Position(
                symbol=symbol,
                qty=qty if side == "BUY" else -qty,
                avg_price=fill_price,
                side="LONG" if side == "BUY" else "SHORT",
            )
        else:
            # Update existing position
            if side == "BUY":
                new_qty = current.qty + qty
            else:
                new_qty = current.qty - qty

            # Calculate weighted average price
            if new_qty != 0:
                if side == "BUY":
                    weighted_avg = (
                        (current.qty * current.avg_price) + (qty * fill_price)
                    ) / new_qty
                else:
                    weighted_avg = (
                        (current.qty * current.avg_price) - (qty * fill_price)
                    ) / new_qty
            else:
                weighted_avg = fill_price

            self.portfolio.positions[symbol] = Position(
                symbol=symbol,
                qty=new_qty,
                avg_price=abs(weighted_avg),
                side="LONG" if new_qty >= 0 else "SHORT",
            )

    def check_exits(self, symbol: str, current_price: float) -> str:
        """Check if any positions should exit.

        Args:
            symbol: Symbol to check
            current_price: Current market price

        Returns:
            Exit signal ("HOLD", "STOP_LOSS", "TAKE_PROFIT")
        """
        pos = self.portfolio.position_for(symbol)
        if pos is None:
            return "HOLD"

        result = self.exit_engine.evaluate_exit(pos, current_price)
        self.journal.add(
            "exit_check",
            symbol=symbol,
            price=current_price,
            result=result,
            position_qty=pos.qty,
            avg_price=pos.avg_price,
        )
        return result

    def execute_exit(
        self,
        symbol: str,
        exit_price: float,
        rationale: str,
    ) -> tuple[TradingDecision, Fill | None]:
        """Execute an exit from a position.

        Args:
            symbol: Symbol to exit
            exit_price: Price at which to exit
            rationale: Reason for exiting

        Returns:
            Tuple of (TradingDecision, Fill)
        """
        pos = self.portfolio.position_for(symbol)
        if pos is None:
            raise ValueError(f"No position in {symbol} to exit")

        side = "SELL" if pos.side == "LONG" else "BUY"
        order = Order(symbol=symbol, side=side, qty=abs(pos.qty), order_type="MARKET")

        fill = self.broker.fill(order, exit_price)
        self.journal.add(
            "exit",
            symbol=symbol,
            exit_side=side,
            exit_qty=abs(pos.qty),
            exit_price=fill.fill_price,
            pnl_per_unit=(
                fill.fill_price - pos.avg_price
                if pos.side == "LONG"
                else pos.avg_price - fill.fill_price
            ),
            total_pnl=(
                (fill.fill_price - pos.avg_price) * abs(pos.qty)
                if pos.side == "LONG"
                else (pos.avg_price - fill.fill_price) * abs(pos.qty)
            ),
            rationale=rationale,
        )

        # Remove position from portfolio
        del self.portfolio.positions[symbol]

        decision = TradingDecision(
            symbol=symbol,
            action=side,
            confidence=1.0,
            rationale=f"Exit: {rationale}",
            risk_budget=0.0,
        )

        return decision, fill

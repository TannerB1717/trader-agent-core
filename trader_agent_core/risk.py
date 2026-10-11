"""Risk management and position validation."""

from __future__ import annotations

from trader_agent_core.models import Order, Portfolio, RiskLimits


class RiskValidator:
    """Validates orders against risk limits."""

    def __init__(self, limits: RiskLimits):
        self.limits = limits

    def validate_new_order(
        self, portfolio: Portfolio, order: Order, market_price: float
    ) -> tuple[bool, str]:
        """Validate an order against risk constraints.

        Returns:
            Tuple of (is_valid, reason)
        """
        current = portfolio.position_for(order.symbol)
        current_qty = current.qty if current else 0.0

        if order.side == "BUY":
            proposed_qty = current_qty + order.qty
        else:
            proposed_qty = current_qty - order.qty

        # Check position size limit
        if abs(proposed_qty) > self.limits.max_position_per_symbol:
            return False, f"Position cap exceeded for {order.symbol}: {abs(proposed_qty)} > {self.limits.max_position_per_symbol}"

        # Check gross exposure
        current_exposure = portfolio.gross_exposure()
        new_exposure = current_exposure + (order.qty * market_price)
        if new_exposure > self.limits.max_gross_exposure:
            return False, f"Gross exposure exceeded: {new_exposure} > {self.limits.max_gross_exposure}"

        # Check trade risk
        trade_risk = abs(order.qty) * market_price * self.limits.max_trade_risk_pct
        if trade_risk <= 0:
            return False, "Invalid trade risk calculation"

        return True, "OK"

    def check_daily_loss(
        self, realized_pnl: float, daily_loss_limit: float
    ) -> tuple[bool, str]:
        """Check if daily loss limit is breached."""
        if realized_pnl < -daily_loss_limit:
            return False, f"Daily loss limit exceeded: {realized_pnl} < {-daily_loss_limit}"
        return True, "OK"

    def check_drawdown(
        self, peak_equity: float, current_equity: float, drawdown_limit: float
    ) -> tuple[bool, str]:
        """Check if drawdown limit is breached."""
        if peak_equity <= 0:
            return True, "OK"
        drawdown = (peak_equity - current_equity) / peak_equity
        if drawdown > drawdown_limit:
            return False, f"Drawdown limit exceeded: {drawdown:.2%} > {drawdown_limit:.2%}"
        return True, "OK"

"""Simulated broker for realistic order fills."""

from __future__ import annotations

from datetime import datetime

from trader_agent_core.models import Fill, Order


class SimulatedBroker:
    """Simulates order execution with realistic fills."""

    def __init__(self, spread_bps: float = 8.0, slippage_bps: float = 2.0):
        """Initialize the broker.

        Args:
            spread_bps: Bid-ask spread in basis points
            slippage_bps: Additional slippage in basis points
        """
        self.spread_bps = spread_bps
        self.slippage_bps = slippage_bps

    def fill(self, order: Order, mid_price: float) -> Fill:
        """Execute an order and return a fill.

        Args:
            order: The order to fill
            mid_price: Current mid-market price

        Returns:
            Fill object representing the execution
        """
        spread = mid_price * (self.spread_bps / 10000.0)
        slippage = mid_price * (self.slippage_bps / 10000.0)

        if order.order_type == "MARKET":
            if order.side == "BUY":
                fill_price = mid_price + spread + slippage
            else:
                fill_price = mid_price - spread - slippage
        elif order.order_type == "LIMIT":
            if order.limit_price is None:
                raise ValueError("LIMIT order must have a limit_price")
            if order.side == "BUY":
                fill_price = min(order.limit_price, mid_price + spread)
            else:
                fill_price = max(order.limit_price, mid_price - spread)
        else:
            fill_price = mid_price

        actual_slippage = abs(fill_price - mid_price)

        return Fill(
            symbol=order.symbol,
            side=order.side,
            qty=order.qty,
            fill_price=fill_price,
            slippage=actual_slippage,
            timestamp=datetime.utcnow().isoformat(),
            status="FILLED",
        )

    def partial_fill(
        self, order: Order, mid_price: float, fill_ratio: float = 0.5
    ) -> Fill:
        """Execute a partial fill of an order.

        Args:
            order: The order to partially fill
            mid_price: Current mid-market price
            fill_ratio: Ratio of order to fill (0.0-1.0)

        Returns:
            Fill object representing the partial execution
        """
        partial_order = Order(
            symbol=order.symbol,
            side=order.side,
            qty=order.qty * fill_ratio,
            order_type=order.order_type,
            limit_price=order.limit_price,
            stop_price=order.stop_price,
        )
        return self.fill(partial_order, mid_price)

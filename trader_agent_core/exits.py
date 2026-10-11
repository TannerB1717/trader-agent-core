"""Exit logic and stop/profit target management."""

from __future__ import annotations

from trader_agent_core.models import ExitPlan, Position


class ExitEngine:
    """Evaluates and manages position exits."""

    def __init__(
        self,
        stop_loss_pct: float = 0.03,
        take_profit_pct: float = 0.08,
        trailing_stop_pct: float = 0.04,
    ):
        """Initialize the exit engine.

        Args:
            stop_loss_pct: Default stop-loss percentage (e.g., 0.03 for 3%)
            take_profit_pct: Default take-profit percentage (e.g., 0.08 for 8%)
            trailing_stop_pct: Default trailing stop percentage
        """
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.trailing_stop_pct = trailing_stop_pct

    def evaluate_exit(self, position: Position, current_price: float) -> str:
        """Evaluate if a position should exit.

        Returns:
            One of: "HOLD", "STOP_LOSS", "TAKE_PROFIT"
        """
        if position.side == "LONG":
            # For long positions
            if current_price <= position.avg_price * (1.0 - self.stop_loss_pct):
                return "STOP_LOSS"
            if current_price >= position.avg_price * (1.0 + self.take_profit_pct):
                return "TAKE_PROFIT"
        else:
            # For short positions
            if current_price >= position.avg_price * (1.0 + self.stop_loss_pct):
                return "STOP_LOSS"
            if current_price <= position.avg_price * (1.0 - self.take_profit_pct):
                return "TAKE_PROFIT"

        return "HOLD"

    def trailing_stop_trigger(
        self,
        position: Position,
        current_price: float,
        peak_price: float | None = None,
        trail_pct: float | None = None,
    ) -> bool:
        """Check if trailing stop is triggered.

        Args:
            position: The position to check
            current_price: Current market price
            peak_price: Highest price seen (for long) or lowest (for short)
            trail_pct: Override trailing stop percentage

        Returns:
            True if trailing stop should trigger
        """
        trail_pct = trail_pct or self.trailing_stop_pct

        if position.side == "LONG":
            peak = peak_price or position.avg_price
            return current_price <= peak * (1.0 - trail_pct)
        else:
            peak = peak_price or position.avg_price
            return current_price >= peak * (1.0 + trail_pct)

    def calculate_exit_price(self, position: Position, exit_type: str) -> float:
        """Calculate the exit price based on exit type.

        Args:
            position: The position to exit
            exit_type: "STOP_LOSS", "TAKE_PROFIT", or a custom exit

        Returns:
            The exit price
        """
        if position.side == "LONG":
            if exit_type == "STOP_LOSS":
                return position.avg_price * (1.0 - self.stop_loss_pct)
            elif exit_type == "TAKE_PROFIT":
                return position.avg_price * (1.0 + self.take_profit_pct)
        else:
            if exit_type == "STOP_LOSS":
                return position.avg_price * (1.0 + self.stop_loss_pct)
            elif exit_type == "TAKE_PROFIT":
                return position.avg_price * (1.0 - self.take_profit_pct)

        return position.avg_price

    def create_exit_plan(
        self, position: Position, stop_loss_pct: float | None = None,
        take_profit_pct: float | None = None, trailing_stop: bool = False
    ) -> ExitPlan:
        """Create an exit plan for a position.

        Args:
            position: The position
            stop_loss_pct: Optional stop-loss override
            take_profit_pct: Optional take-profit override
            trailing_stop: Whether to use trailing stop

        Returns:
            ExitPlan object
        """
        sl_pct = stop_loss_pct or self.stop_loss_pct
        tp_pct = take_profit_pct or self.take_profit_pct

        if position.side == "LONG":
            stop_loss = position.avg_price * (1.0 - sl_pct)
            take_profit = position.avg_price * (1.0 + tp_pct)
        else:
            stop_loss = position.avg_price * (1.0 + sl_pct)
            take_profit = position.avg_price * (1.0 - tp_pct)

        return ExitPlan(
            stop_loss=stop_loss,
            take_profit=take_profit,
            trailing_stop=self.trailing_stop_pct if trailing_stop else None,
        )

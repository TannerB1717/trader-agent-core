"""Example usage of the backtesting engine - with trade details."""

from trader_agent_core import (
    BacktestEngine,
    ExitEngine,
    RiskLimits,
    SimulatedBroker,
    generate_sample_history,
)
from trader_agent_core.backtester import SimpleBacktester


if __name__ == "__main__":
    print("=== Backtesting Engine Example ===\n")
    
    print("Generating 180 days of synthetic market data...")
    history = generate_sample_history(start_price=100.0, length=180, drift=0.005, volatility=0.08)
    print(f"Generated {len(history)} candles\n")
    
    closes = [c["close"] for c in history]
    print(f"Price range: ${min(closes):.2f} to ${max(closes):.2f}")
    print(f"Start: ${closes[0]:.2f}, End: ${closes[-1]:.2f}\n")

    risk_limits = RiskLimits(
        max_position_per_symbol=1000.0,
        max_gross_exposure=0.40,
        max_daily_loss=0.02,
        max_drawdown=0.10,
    )

    engine = BacktestEngine(
        symbol="AAPL",
        risk_limits=risk_limits,
        broker=SimulatedBroker(spread_bps=8.0, slippage_bps=2.0),
        exit_engine=ExitEngine(),
    )

    print("Running backtest...")
    portfolio, metrics = engine.run(history, initial_cash=100000.0)

    print("\n=== Backtest Results ===\n")
    print(f"Initial cash:       ${metrics.initial_cash:,.2f}")
    print(f"Final cash:         ${metrics.final_cash:,.2f}")
    print(f"Total return:       {metrics.total_return:.2%}")
    print(f"Number of trades:   {metrics.num_trades}")
    print(f"Wins:               {metrics.wins}")
    print(f"Losses:             {metrics.losses}")
    print(f"Win rate:           {metrics.win_rate:.2%}")
    print(f"Max drawdown:       {metrics.max_drawdown:.2%}")
    print(f"Avg return/trade:   {metrics.avg_trade_return:.2%}")
    
    # Show trade details
    print("\n=== Trade Details ===\n")
    backtest = SimpleBacktester("AAPL")
    trades, _ = backtest.run(history, initial_cash=100000.0)
    
    for trade in trades:
        if trade["type"] == "ENTRY":
            print(f"ENTRY  | {trade['date']} | Price: ${trade['price']:.2f} | Shares: {trade['shares']:.2f} | Confidence: {trade['confidence']:.2f}")
        else:
            print(f"EXIT   | {trade['date']} | Price: ${trade['price']:.2f} | Profit: ${trade['profit']:.2f} | ROI: {(trade['profit'] / (trade['shares'] * trade['entry_price']))*100:.2f}%")

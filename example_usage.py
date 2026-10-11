"""Example usage of trader-agent-core."""

from trader_agent_core import (
    DecisionJournal,
    ExitEngine,
    MinimalDecisionLoop,
    Portfolio,
    RiskLimits,
    SimulatedBroker,
)

# Initialize components
portfolio = Portfolio(cash=100000.0)
risk_limits = RiskLimits(
    max_position_per_symbol=1000.0,
    max_gross_exposure=50000.0,
    max_daily_loss=0.02,
    max_drawdown=0.10,
)
broker = SimulatedBroker(spread_bps=8.0, slippage_bps=2.0)
exit_engine = ExitEngine(stop_loss_pct=0.03, take_profit_pct=0.08)
journal = DecisionJournal()

# Create decision loop
loop = MinimalDecisionLoop(portfolio, risk_limits, broker, exit_engine, journal)

# Example 1: Make a BUY decision
print("\n=== Example 1: BUY Decision ===")
decision, fill = loop.decide(
    symbol="AAPL",
    signal="BUY",
    confidence=0.75,
    market_price=210.0,
    rationale="Strong bullish momentum and technical breakout",
)
print(f"Decision: {decision}")
print(f"Fill: {fill}")
print(f"Portfolio positions: {portfolio.positions}")
print(f"Journal entries: {len(journal.entries)}")

# Example 2: Check exits
print("\n=== Example 2: Check Exits ===")
exit_signal = loop.check_exits("AAPL", 214.0)
print(f"Exit signal at $214.0: {exit_signal}")

exit_signal = loop.check_exits("AAPL", 204.0)
print(f"Exit signal at $204.0: {exit_signal}")

# Example 3: Execute an exit
print("\n=== Example 3: Execute Exit ===")
decision, fill = loop.execute_exit(
    symbol="AAPL", exit_price=215.0, rationale="Take profit at resistance"
)
print(f"Exit decision: {decision}")
print(f"Exit fill: {fill}")
print(f"Portfolio positions: {portfolio.positions}")

# Example 4: HOLD decision
print("\n=== Example 4: HOLD Decision ===")
decision, fill = loop.decide(
    symbol="MSFT",
    signal="HOLD",
    confidence=0.50,
    market_price=420.0,
    rationale="Awaiting more data before deciding",
)
print(f"Decision: {decision}")
print(f"Fill: {fill}")

# Example 5: Save and summarize journal
print("\n=== Example 5: Journal Summary ===")
journal.save("decision_journal.json")
summary = journal.summarize()
print(f"Journal summary: {summary}")
print(f"\nEntries by type:")
for entry_type, count in summary["by_type"].items():
    print(f"  {entry_type}: {count}")

print("\nJournal saved to decision_journal.json")

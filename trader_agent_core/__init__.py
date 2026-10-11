"""Trader Agent Core package exports."""

from trader_agent_core.backtester import BacktestEngine, BacktestMetrics, generate_sample_history
from trader_agent_core.broker import SimulatedBroker
from trader_agent_core.decision import MinimalDecisionLoop
from trader_agent_core.exits import ExitEngine
from trader_agent_core.journal import DecisionJournal, JournalEntry
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
from trader_agent_core.signal import SignalGenerator

__version__ = "0.2.0"

__all__ = [
    "Position",
    "RiskLimits",
    "Order",
    "Fill",
    "ExitPlan",
    "TradingDecision",
    "Portfolio",
    "RiskValidator",
    "SimulatedBroker",
    "ExitEngine",
    "MinimalDecisionLoop",
    "DecisionJournal",
    "JournalEntry",
    "SignalGenerator",
    "BacktestEngine",
    "BacktestMetrics",
    "generate_sample_history",
]

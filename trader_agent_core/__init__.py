"""Trader Agent Core - A minimal trading system with risk management."""

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

__version__ = "0.1.0"

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
]

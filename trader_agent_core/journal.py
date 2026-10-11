"""Decision journal for audit trail and replay."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class JournalEntry:
    """A single journal entry."""
    timestamp: str
    entry_type: str
    data: dict[str, Any]


class DecisionJournal:
    """Audit trail for all trading decisions and executions."""

    def __init__(self, path: str | Path | None = None):
        """Initialize the journal.

        Args:
            path: Optional file path to persist journal
        """
        self.entries: list[JournalEntry] = []
        self.path = Path(path) if path else None

    def add(
        self, entry_type: str, data: dict[str, Any] | None = None, **kwargs
    ) -> None:
        """Add an entry to the journal.

        Args:
            entry_type: Type of entry ("decision", "fill", "exit", etc.)
            data: Dictionary of data to log
            **kwargs: Additional key-value pairs merged into data
        """
        merged_data = data or {}
        merged_data.update(kwargs)

        entry = JournalEntry(
            timestamp=datetime.utcnow().isoformat(),
            entry_type=entry_type,
            data=merged_data,
        )
        self.entries.append(entry)

    def latest(self) -> JournalEntry | None:
        """Get the most recent entry."""
        return self.entries[-1] if self.entries else None

    def entries_by_type(self, entry_type: str) -> list[JournalEntry]:
        """Get all entries of a specific type."""
        return [e for e in self.entries if e.entry_type == entry_type]

    def entries_for_symbol(self, symbol: str) -> list[JournalEntry]:
        """Get all entries related to a symbol."""
        return [e for e in self.entries if e.data.get("symbol") == symbol]

    def save(self, path: str | Path | None = None) -> None:
        """Save journal to a JSON file.

        Args:
            path: File path to save to (uses self.path if not provided)
        """
        target_path = Path(path or self.path)
        if not target_path:
            raise ValueError("No path provided for saving journal")

        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert entries to serializable format
        data = [
            {
                "timestamp": e.timestamp,
                "entry_type": e.entry_type,
                "data": e.data,
            }
            for e in self.entries
        ]

        with open(target_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    @staticmethod
    def load(path: str | Path) -> DecisionJournal:
        """Load journal from a JSON file.

        Args:
            path: File path to load from

        Returns:
            DecisionJournal instance
        """
        target_path = Path(path)
        if not target_path.exists():
            raise FileNotFoundError(f"Journal file not found: {path}")

        with open(target_path, "r") as f:
            data = json.load(f)

        journal = DecisionJournal(path=path)
        for entry_data in data:
            journal.entries.append(
                JournalEntry(
                    timestamp=entry_data["timestamp"],
                    entry_type=entry_data["entry_type"],
                    data=entry_data["data"],
                )
            )
        return journal

    def summarize(self) -> dict[str, Any]:
        """Provide a summary of journal contents."""
        type_counts = {}
        for entry in self.entries:
            type_counts[entry.entry_type] = type_counts.get(entry.entry_type, 0) + 1

        return {
            "total_entries": len(self.entries),
            "by_type": type_counts,
            "first_timestamp": self.entries[0].timestamp if self.entries else None,
            "last_timestamp": self.entries[-1].timestamp if self.entries else None,
        }

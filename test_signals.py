"""Debug signal generation."""

from trader_agent_core import SignalGenerator, generate_sample_history

history = generate_sample_history(start_price=100.0, length=180, drift=0.005, volatility=0.08)
generator = SignalGenerator()

print("Testing signal generation on sample history:\n")
print("Date      | Close   | Signal | Confidence | Rationale")
print("-" * 80)

for idx in range(20, min(60, len(history))):
    window = history[:idx+1]
    signal, confidence, rationale = generator.generate(window)
    print(f"{history[idx]['date']} | ${history[idx]['close']:6.2f} | {signal:6s} | {confidence:10.2f} | {rationale[:40]}")

from hermetic_alpha.analysis import summarize_event_study
from hermetic_alpha.astro import detect_aspect
from hermetic_alpha.labels import add_forward_returns

# Minimal synthetic example.
closes = [100, 110, 99, 120]
labels = add_forward_returns(closes, horizons=[1])

aspect = detect_aspect(
    body_a="sun",
    longitude_a=10,
    body_b="jupiter",
    longitude_b=12,
    aspect="conjunction",
    max_orb=3,
)

assert aspect is not None

# Assume the aspect event occurred at indexes 0 and 1 in this toy dataset.
result = summarize_event_study(labels, event_indexes=[0, 1], horizon=1)

print(aspect)
print(result)

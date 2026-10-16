"""Generate deterministic SYNTHETIC training data for the learning prototype.

These rows are invented for demonstrating an ML workflow. They are not crime,
police, or lived-experience data and must never be used to make real safety claims.
"""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "generated" / "synthetic_risk_demo.csv"


def make_dataset(rows: int = 3000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    hours = rng.integers(0, 24, size=rows)
    incidents = rng.poisson(lam=5.0, size=rows).clip(0, 30)
    lighting = rng.choice(["good", "fair", "poor"], size=rows, p=[0.45, 0.35, 0.20])
    crowd = rng.choice(["high", "medium", "low"], size=rows, p=[0.35, 0.45, 0.20])
    weather = rng.choice(["clear", "rain", "fog"], size=rows, p=[0.70, 0.23, 0.07])
    day = rng.choice(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        size=rows,
    )

    # This invented rule creates labels for a tutorial. It is not a validated
    # definition of personal safety or real-world risk.
    demo_score = (
        incidents * 2.2
        + np.where((hours >= 21) | (hours <= 4), 18, 0)
        + np.where(lighting == "poor", 17, np.where(lighting == "fair", 7, 0))
        + np.where(crowd == "low", 9, 0)
        + np.where(weather == "fog", 8, np.where(weather == "rain", 4, 0))
        + np.where(np.isin(day, ["Friday", "Saturday"]), 4, 0)
        + rng.normal(0, 7, size=rows)
    )
    labels = np.select(
        [demo_score < 27, demo_score < 52],
        ["low", "moderate"],
        default="high",
    )

    return pd.DataFrame(
        {
            "hour": hours,
            "day_of_week": day,
            "prior_incidents_30d": incidents,
            "lighting": lighting,
            "crowd_level": crowd,
            "weather": weather,
            "demo_risk_label": labels,
        }
    )


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    dataset = make_dataset()
    dataset.to_csv(OUTPUT, index=False)
    print(f"Created {len(dataset)} synthetic demo rows: {OUTPUT.relative_to(ROOT)}")
    print("Reminder: these invented labels teach the ML workflow; they are not real risk data.")
    print(dataset["demo_risk_label"].value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()

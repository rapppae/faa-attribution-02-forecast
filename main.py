#!/usr/bin/env python3
"""polymarket-faa-attribution-02 entry (Python 3.13, standard library only).

Forecasts the Yes price of every trading market of Polymarket's FAA outage
attribution family (Iran, foreign actor, hack, AI sandbox escape) at every
minute of the 4 hours after a checkpoint, as five quantiles (0.05, 0.25,
0.5, 0.75, 0.95) per minute.

Method (validated on the six practice cases, which are cut from Polymarket's
"Next CEO of NVIDIA?" event; practice pinball loss 0.277 vs the house
baseline's 0.364). Rebuilt fresh for attribution-02 after its 02:00Z
opening on 2026-11-14; the model is unchanged from the validated version,
only the competition slug in this header differs:
  - Median: the price at the checkpoint. Prediction-market prices are
    near-martingales, so no drift is estimated (every drift variant tested
    made the practice loss worse).
  - Spread: per market, from the recent 1-minute moves. The moves are mostly
    zero with rare jumps, so the scale is the 90th percentile of |1-min move|
    over the last 720 minutes, / 1.644854 (its normal-consistent scale),
    floored at 0.0005 and capped at 0.02. A jump-inflated standard deviation
    was far worse (loss 0.89-1.19): it makes the intervals far too wide at
    the quiet minutes that dominate the score.
  - Shape: Student-t with 4 degrees of freedom (fatter tails than normal,
    for the jumps), widening with horizon as h**0.40, not sqrt(h): the
    moves mean-revert, so the spread grows slower than a random walk's.
  - Quantiles are clamped to [0, 1] and rounded to 6 decimals.

Nearby settings all land within 0.276-0.279, so the parameters sit on a
flat, robust plateau rather than a sharp optimum tuned to one event --
which matters here, since the practice score is no guide to the final
(12 unseen cases, 48 hours of live FAA prices). Short histories are
handled naturally: the scale uses whatever moves exist in the last 720
minutes (the FAA markets are young, created 2026-11-13), and a market
with no moves at all falls back to the floor.

Reads every <id>.in in the input directory (default /input, or
MAKEFUN_INPUT_DIR) and writes <id>.out to the output directory (default
/output, or MAKEFUN_OUTPUT_DIR). Deterministic: no randomness, no clock.
"""
import json
import os
from pathlib import Path

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

QUANTILES = [0.05, 0.25, 0.5, 0.75, 0.95]
# Student-t (df=4) quantiles at the five levels, keyed by level so the
# columns follow whatever order the case asks for (the competition fixes
# the order above, but the code does not assume it).
Z_BY_TAU = {0.05: -2.131847, 0.25: -0.740697, 0.5: 0.0, 0.75: 0.740697,
            0.95: 2.131847}

SIG_WINDOW = 720          # minutes of recent moves used for the scale
SIG_FLOOR = 0.0005        # minimum per-minute scale (price units)
SIG_CAP = 0.02            # maximum per-minute scale
HEXP = 0.40               # spread grows as h**HEXP


def _pct(sorted_xs, q):
    if not sorted_xs:
        return 0.0
    i = q * (len(sorted_xs) - 1)
    lo = int(i)
    hi = min(lo + 1, len(sorted_xs) - 1)
    f = i - lo
    return sorted_xs[lo] * (1.0 - f) + sorted_xs[hi] * f


def _clip6(x):
    v = round(min(1.0, max(0.0, x)) * 1e6) / 1e6
    return v + 0.0  # never -0


def forecast_market(prices, horizon, z):
    """Return `horizon` rows of five quantiles for one market."""
    if not prices:
        return [[0.5, 0.5, 0.5, 0.5, 0.5] for _ in range(horizon)]
    x = prices[-1]
    diffs = [prices[i + 1] - prices[i] for i in range(len(prices) - 1)]
    w = diffs[-SIG_WINDOW:] if diffs else []
    if w:
        aw = sorted(abs(v) for v in w)
        s = _pct(aw, 0.90) / 1.644854
    else:
        s = 0.0
    s = min(max(s, SIG_FLOOR), SIG_CAP)
    rows = []
    for h in range(1, horizon + 1):
        scale = s * (h ** HEXP)
        row = [_clip6(x + zj * scale) for zj in z]
        for j in range(1, 5):
            if row[j] < row[j - 1]:
                row[j] = row[j - 1]
        rows.append(row)
    return rows


def main():
    in_dir = Path(INPUT_DIR)
    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    inputs = sorted(p for p in in_dir.iterdir() if p.name.endswith(".in"))
    for path in inputs:
        case = json.loads(path.read_text(encoding="utf-8"))
        horizon = int(case.get("horizon_minutes", 240))
        levels = case.get("quantiles", QUANTILES)
        z = [Z_BY_TAU.get(float(t), 0.0) for t in levels]
        forecasts = [
            {"id": m["id"], "q": forecast_market(m["prices"], horizon, z)}
            for m in case["markets"]
        ]
        out_path = out_dir / (path.name[: -len(".in")] + ".out")
        out_path.write_text(json.dumps({"forecasts": forecasts}) + "\n",
                            encoding="utf-8")


if __name__ == "__main__":
    main()

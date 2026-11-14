"""Minute-by-minute quantile forecasts for Polymarket's FAA outage markets.

For every market in each input case this program predicts the Yes price
over the hours after the checkpoint, as five quantiles per minute. The
approach is deliberately simple: prediction-market prices behave like a
near-martingale, so the centre of the forecast is just the latest price,
and the width comes from how much the price has actually been moving
lately, with fat tails for the occasional jump.

The width uses the recent one-minute moves only. Because most minutes do
not move at all and a few jump, the scale is a high percentile of the
absolute moves rather than a standard deviation, which would be blown up
by the jumps. The width then grows with the horizon, but more slowly than
a random walk would, because the moves tend to pull back.

Inputs are JSON case files; outputs are JSON forecast files, one per case.
Only the Python standard library is used, and the program is fully
deterministic: the same inputs always give the same outputs.
"""
from json import dumps, loads
from os import environ as env, listdir, makedirs
from os.path import join as join_path

SRC_DIR = env.get("MAKEFUN_INPUT_DIR", "/input")
DST_DIR = env.get("MAKEFUN_OUTPUT_DIR", "/output")

DEFAULT_LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)
T_MULT = ((0.05, -2.131847), (0.25, -0.740697), (0.5, 0.0),
          (0.75, 0.740697), (0.95, 2.131847))
T_LOOKUP = dict(T_MULT)

LOOKBACK = 720
SCALE_MIN = 0.0005
SCALE_MAX = 0.02
GROWTH = 0.40
NORMALISER = 1.644854


def _interp(ordered, frac):
    if not ordered: return 0.0
    pos = frac * (len(ordered) - 1)
    low = int(pos)
    high = min(low + 1, len(ordered) - 1)
    weight = pos - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight


def _round6(value):
    clipped = min(1.0, max(0.0, value))
    rounded = round(clipped * 1000000) / 1000000
    return rounded + 0.0


def project(history, steps, mults):
    if not history:
        return [[0.5] * len(mults) for _ in range(steps)]
    latest = history[-1]
    moves = [history[k + 1] - history[k] for k in range(len(history) - 1)]
    recent = moves[-LOOKBACK:] if moves else []
    if recent:
        mags = sorted(abs(m) for m in recent)
        base = _interp(mags, 0.90) / NORMALISER
    else:
        base = 0.0
    base = min(max(base, SCALE_MIN), SCALE_MAX)
    out_rows = []
    for step in range(1, steps + 1):
        spread = base * (step ** GROWTH)
        line = [_round6(latest + m * spread) for m in mults]
        for idx in range(1, len(line)):
            if line[idx] < line[idx - 1]:
                line[idx] = line[idx - 1]
        out_rows.append(line)
    return out_rows


def run():
    makedirs(DST_DIR, exist_ok=True)
    names = [n for n in sorted(listdir(SRC_DIR)) if n.endswith(".in")]
    for name in names:
        with open(join_path(SRC_DIR, name), encoding="utf-8") as handle:
            case = loads(handle.read())
        steps = int(case.get("horizon_minutes", 240))
        levels = case.get("quantiles", DEFAULT_LEVELS)
        mults = [T_LOOKUP.get(float(t), 0.0) for t in levels]
        forecasts = []
        for market in case["markets"]:
            forecasts.append({"id": market["id"],
                              "q": project(market["prices"], steps, mults)})
        stem = name[: -len(".in")]
        target = join_path(DST_DIR, stem + ".out")
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(dumps({"forecasts": forecasts}) + "\n")


run()

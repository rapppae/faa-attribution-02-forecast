# faa-attribution-02-forecast

[![make.fun · polymarket-faa-attribution-02](https://make.fun/badge/polymarket-faa-attribution-02.svg)](https://make.fun/bounty/polymarket-faa-attribution-02?utm_source=github&utm_medium=readme&utm_campaign=polymarket-faa-attribution-02)
[![rank](https://make.fun/badge/polymarket-faa-attribution-02/rapppae/faa-attribution-02-forecast/rank.svg)](https://make.fun/bounty/polymarket-faa-attribution-02/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=polymarket-faa-attribution-02)
[![reward](https://make.fun/badge/polymarket-faa-attribution-02/rapppae/faa-attribution-02-forecast/reward.svg)](https://make.fun/bounty/polymarket-faa-attribution-02?utm_source=github&utm_medium=readme&utm_campaign=polymarket-faa-attribution-02)

Forecasts the Yes price of each of Polymarket's four FAA outage attribution markets (Iran, foreign actor, hack, AI sandbox escape) at every minute of the next 4 hours, as five quantiles, from the last 72 hours of 1-minute prices. Per market: the checkpoint price as the median, a Student-t (df=4) spread from the 90th percentile of recent 1-minute moves, widening as h**0.40. Practice pinball loss 0.277 vs the house baseline's 0.364.

## Run it

```sh
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=wj2zbndb&utm_source=github&utm_medium=readme&utm_campaign=polymarket-faa-attribution-02) · AI agents build software for cash rewards</sub>

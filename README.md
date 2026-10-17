# Coffee Hedging Lab

An independent, AI-assisted educational Python project comparing a coffee buyer's procurement costs under three strategies: no hedge, fully matched futures, and purchased call options.

## Features

- Interactive Streamlit dashboard with Plotly charts.
- 101 hypothetical terminal-price scenarios and reproducible CSV export.
- Validated numeric inputs, model formulas and explicit limitations.
- Unit tests and Streamlit AppTest checks.

## Run

Use Python 3.12:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
python -m unittest discover -s tests -q
```

For Community Cloud deployment, choose `app.py` as the entry point and Python 3.12. Live deployment is pending.

## Model

Q: purchase quantity (lb); S: terminal coffee price (USD/lb); F: locked futures price; K: call strike; p: premium per pound.

- Unhedged cost = Q × S.
- Futures P&L = Q × (S − F); net cost = Q × F.
- Call payoff = Q × max(S − K, 0); net cost = Q × min(S, K) + Q × p.
- Current spot is a reference benchmark only, not a forecast or scenario-cost input.

Defaults: Q=1000, current spot=1.20, F=1.22, K=1.25, p=0.07; terminal prices 0.60–1.80 inclusive.

| Terminal price (USD/lb) | Unhedged (USD) | Futures hedge (USD) | Call hedge (USD) |
| --- | --- | --- | --- |
| 0.60 | 600 | 1220 | 670 |
| 1.80 | 1800 | 1220 | 1320 |

CSV records include input parameters, units, separate cashflows and costs. Values are not rounded before export; floating-point representation artefacts may occur.

## Limitations

Hypothetical inputs only: no live quotes, forecasts, option pricing or trade execution. Perfect matching of quantity, timing and price reference is assumed. Basis risk, contract sizing, margin funding, interest, fees, taxes, credit risk and delivery differences are excluded. Option premium is an undiscounted cash expenditure. This is not investment advice and is independent of Citi and Forage.

## Author and AI assistance

Built by Max (Ningyuan) Yao as a guided learning project. The author worked through the financial formulas, proposed Python expressions and explained sensitivity results. Codex assisted with implementation, validation, tests, numerical robustness, interface scaffolding and documentation. This is not a claim of unaided software development or professional trading experience.

## Local acceptance

83 tests passed in a fresh Python 3.12 environment on macOS ARM64. Actual browser CSV downloads matched all 101 rows and 13 fields at default and changed quantity. Responsive layouts checked at 390×844 and 320×740 in desktop Chrome; physical mobile devices and the eventual cloud runtime still require separate verification.

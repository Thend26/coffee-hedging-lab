# Coffee Hedging Lab

Independent educational scenario analyser for a coffee buyer. V2 compares unhedged procurement, partial futures and call hedges, analytical break-even and deterministic budget stress. Hypothetical inputs only; no live quotes, option pricing, forecasts or trade execution. This release upgrades the public app after deployment verification.

## Run locally

From this project directory, using Python 3.12:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

Open http://127.0.0.1:8501. Change inputs in the sidebar to recalculate. The page includes a shared hedge-ratio slider, budget input, interactive cost chart, break-even analysis, stress summary, 101 scenario records and CSV download.

## Tests

```sh
MPLCONFIGDIR=/private/tmp/coffee-mpl .venv/bin/python -m unittest discover -s tests -q
```

## Model and reproducible example

Let Q be quantity, S terminal coffee price, F locked futures price, K call strike, p premium per pound and h the shared hedge ratio in [0,1].

- Unhedged cost: Q × S.
- Futures P&L: h × Q × (S − F); net cost: Q × [(1 − h) × S + h × F].
- Call payoff: h × Q × max(S − K, 0); premium: h × Q × p; net cost: Q × [(1 − h) × S + h × min(S,K) + h × p].
- Current spot is a reference benchmark only, not an input to scenario costs.

Defaults: Q=1000 lb, current spot=1.20, F=1.22, K=1.25, p=0.07 USD/lb, h=1 and budget=$1300. Generate 101 equally spaced terminal prices from 0.60 to 1.80 inclusive. Headline metrics evaluate terminal S equal to current reference spot; this is a hypothetical scenario, not a forecast.

| Terminal price (USD/lb) | Unhedged (USD) | Futures hedge (USD) | Call hedge (USD) |
| --- | --- | --- | --- |
| 0.60 | 600 | 1220 | 670 |
| 1.80 | 1800 | 1220 | 1320 |

Run `.venv/bin/python export_example.py` to regenerate and verify the default CSV in `output/coffee_hedging_scenarios.csv`. CSV keeps unrounded floating-point values; minor decimal representation artefacts are normal. Reproduction also depends on using the same formulas and model assumptions, not parameters alone.

### V2 CSV schema (24 columns)

The original 13 columns retain their names and order, but cashflows and hedged costs now use the selected h. Appended inputs are `hedge_ratio` (fraction, not percent) and `budget_usd`. For each strategy prefix (`unhedged`, `futures_hedged`, `call_hedged`), appended fields are `_savings_vs_unhedged_usd` (unhedged minus cost), `_budget_gap_usd` (cost minus budget) and `_overspend_usd` (maximum of gap and zero). Current spot remains reference only. All amounts are USD and per-pound prices are USD/lb.

### Analytical interpretation

For h>0, futures break-even against unhedged is S=F. If p>0, call break-even is S=K+p. If p=0, call costs equal unhedged throughout [0,K] and are lower above K. If h=0, both strategies equal unhedged at every nonnegative S. These are analytical results, not grid searches.

Cost slopes with respect to S are Q (unhedged), Q(1-h) (futures), and Q below K / Q(1-h) above K (calls). At the strike the call cost is continuous but not differentiable when h>0. Neither partial hedge has a global cost cap when h<1.

Worked half-hedge example: Q=1000,h=.5,F=1.22,K=1.25,p=.07,S=1.5 gives costs $1500/$1360/$1410. Against budget $1300, overspends are $200/$60/$110. Across the default [.6,1.8] interval, half-hedge overspend counts are 42/35/44 out of 101, and interval maximum costs $1800/$1510/$1560. Counts are NOT probabilities: no distribution or likelihood weights are assumed. Equality with budget is not overspending. Interval maxima are not unrestricted worst-case costs.

## Learning and AI assistance

Built by Max (Ningyuan) Yao as a guided learning project. The author worked through the core financial formulas, proposed Python expressions and explained scenario/sensitivity results. Codex assisted with implementation, input validation, tests, numerical robustness, interface scaffolding and documentation. This is an AI-assisted independent educational project, not a claim of unaided software development or professional trading experience.

## Deployment status

Public app: https://max-yao-coffee-hedging-lab.streamlit.app/

Source: https://github.com/Thend26/coffee-hedging-lab

V1 deployed on Streamlit Community Cloud using main/app.py and Python 3.12 on 17 October 2026. Its live checks covered default metrics, quantity update, invalid-bound protection and CSV download (1,313 values). V1 local acceptance passed 83 tests and fresh-environment installation. V2 adds partial hedging, analytical break-even and budget stress testing. Its release checks include 127 automated tests, a 24-column CSV and live verification after deployment. V1 acceptance does not certify v2. No user accounts, personal data or API credentials are required by the app.

Prices and premiums are USD per pound; quantity is pounds; costs are USD. Perfect matching is assumed. Basis risk, contract sizing, margin funding, interest, fees, taxes and counterparty risk are excluded. Premium is undiscounted. This is not investment advice and is independent of Citi and Forage.

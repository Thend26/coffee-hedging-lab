# Coffee Hedging Lab

Independent educational scenario analyser for a coffee buyer. V2 compares unhedged procurement, partial futures and call hedges, analytical break-even and deterministic budget stress. The local Black–76 laboratory adds European futures-call model pricing and controlled sensitivities. Hypothetical inputs only; no live quotes, forecasts or trade execution. The public deployment remains V2, verified on 17 October 2026; the laboratory is local only.

## Run locally

From this project directory, using Python 3.12:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

Open http://127.0.0.1:8501. Change inputs in the sidebar to recalculate. The local page includes a shared hedge-ratio slider, budget input, interactive cost chart, break-even analysis, stress summary, 101 scenario records and CSV download.

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

## Black–76 laboratory (local only)

Choose **Analysis mode → Black–76 laboratory** in the sidebar. V2 remains the default, retaining its manually entered premium and 24-column export. Only the selected mode executes. Defaults: Q=1000 lb, reference spot=1.20, current futures F0=1.22, strike K=1.25 USD/lb, sigma=30%, T=0.5 years, continuous pricing/financing rate r=3%, h=1, budget at T=USD1300, scenario interval [0.6,1.8]. Enter UI percentages as30 and3, not .30 and .03.

### Pricing and cashflow basis

Under the risk-neutral model FT=F0 exp(-sigma²T/2 + sigma sqrt(T) Z), Z is standard normal. For positive sigma,T:

```text
d1 = [ln(F0/K) + sigma²T/2] / [sigma sqrt(T)]
d2 = d1 - sigma sqrt(T)
U  = F0 N(d1) - K N(d2)
c0 = exp(-rT) U     # today's premium, USD/lb
pT = U             # funded premium at T, USD/lb
```

Zero volatility/expiry uses U=max(F0-K,0) and the applicable discount factor. Inputs must be finite numbers (not booleans), F0,K>0 and sigma,T>=0. Negative rates are allowed. Unrepresentable calculations are rejected; very small values may round to zero. Stable tails and an ATM identity reduce cancellation, but this is not arbitrary-precision pricing.

At time0 finance c0 on hQ pounds; at T pay procurement costs, receive the option payoff and repay hQ pT. Laboratory procurement costs and budgets are all at T:

```text
Call cost at T = Q [(1-h) ST + h min(ST,K) + h pT]
```

At fixed F0,K,sigma,T, the same pricing/financing rate cancels: r changes c0 but not pT or terminal costs. For h>0,pT>0, call break-even versus unhedged is K+pT, not K+c0. With zero premium equality holds on [0,K]; with h=0 all nonnegative prices give equal costs.

Assumptions: hypothetical European cash settlement, constant volatility, deterministic rates, matched purchase/expiry dates and ST=FT. Excludes basis risk, contract lots, margin funding, fees, tax, credit risk and delivery differences. Actual ICE Coffee C options are American-style; this is a European teaching benchmark, not their market pricer. Risk-neutral pricing is not a real-world forecast.

References: [LME formula](https://www.lme.com/Trading/Contract-types/Options/Black-Scholes-76-Formula), [ICE specifications](https://www.ice.com/products/14/coffee-c-).

### Controlled sensitivities and export

Volatility curve:21 points0–100%, fixing selected T. Maturity curve:21 points0–2 years, fixing selected sigma. Both fix F0,K,r. The heatmap uses441 sigma/T pairs. Plots show c0, with labelled pT hover/table data. Fixed-F0 maturity sensitivity is not a market term structure; discounted prices need not always increase with T. The101 procurement scenarios have no probability weights: exceedance counts are not probabilities.

Use **Download Black–76 terminal scenarios CSV** for `coffee_black76_terminal_scenarios.csv`:101 rows,32 unrounded numeric columns. First24 names/order match V2, but `premium_usd_per_lb` and `option_premium_usd` mean TERMINAL amounts in this lab file. Preserve valuation basis when comparing exports. Eight appended fields, in order:

```text
volatility_annual
time_to_expiry_years
risk_free_rate_annual
model_premium_today_usd_per_lb
model_premium_terminal_usd_per_lb
total_premium_today_usd
total_premium_terminal_usd
discount_factor
```

Per-lb model quotes remain at h=0, but total premiums are zero. Total terminal premium equals `option_premium_usd`. Defaults give c0≈0.088661, pT≈0.090001 USD/lb, total premiums today/at T≈USD88.66/USD90.00; full-call ceiling≈USD1340.00 and break-even≈1.340001 USD/lb. Display rounding does not change CSV values.

Local browser acceptance on18 October2026 checked two actual downloads (sigma30% and60%): all3232 cells in each matched fresh calculations. Mode switches restored V2 reference costs1200/1220/1270. Checked390×844 and320×740 views were readable with no document-wide horizontal overflow; wide tables scroll internally. Invalid minimum2 above maximum1.8 removed outputs/downloads. Inputs and viewport restored. This is browser emulation, not physical-device certification. Full suite176 tests passed. Evidence: `docs/acceptance-black76-2026-10-18.md`. No public release was made.

## Learning and AI assistance

Built by Max (Ningyuan) Yao as a guided learning project. The author worked through the core financial formulas, proposed Python expressions and explained scenario/sensitivity results. Codex assisted with implementation, input validation, tests, numerical robustness, interface scaffolding and documentation. This is an AI-assisted independent educational project, not a claim of unaided software development or professional trading experience.

## Deployment status

Public app: https://max-yao-coffee-hedging-lab.streamlit.app/

Source: https://github.com/Thend26/coffee-hedging-lab

V2 deployed on Streamlit Community Cloud using main/app.py and Python 3.12 on 17 October 2026, repository commit 5628bd2. Actual remote source passed 127 tests. Live checks covered default and half-hedge reference costs, budget changes, zero hedge, zero premium and invalid-range protection. Two actual cloud CSV downloads each matched all 2,424 numeric values. The 390px browser viewport was visually checked; physical mobile hardware testing is separate. See `docs/acceptance-v2-2026-10-17.md` for local acceptance and `docs/release-v2-2026-10-17.md` for release evidence. No user accounts, personal data or API credentials are required by the app.

Prices and premiums are USD per pound; quantity is pounds; costs are USD. Perfect matching is assumed. V2 excludes interest and uses undiscounted premium cashflows; the local laboratory instead includes the explicitly matched premium-financing convention described above. Both exclude basis risk, contract sizing, margin funding, fees, taxes and counterparty risk. This is not investment advice and is independent of Citi and Forage.

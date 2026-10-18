# Black–76 release verification — 18 October 2026

Application: https://max-yao-coffee-hedging-lab.streamlit.app/

Repository: https://github.com/Thend26/coffee-hedging-lab

Application commit:51e97eeddd57debc44a24c2584a6fe5a6c17f24b. Test commit:80f80af8afafae91c7d1c0a1d7a349ec08537d85. Documentation is committed separately after verification.

## Verification

- Retrieved the actual public Git tree into a separate directory. Application modules matched local accepted source. All176 tests passed in both the project environment and an existing independently installed Python environment. This was not a new clean installation. pip check reported no broken requirements. Streamlit bare-mode warnings were expected in tests.
- Streamlit pulled GitHub changes automatically. Rebooted through Manage app to initialise the updated process. No new permissions, secrets or dependencies were added by this feature.
- Cloud V2 default reference metrics1200/1220/1270 USD. Selected Black–76: current/funded per-lb premiums.088661/.090001 and total88.66/90.00 USD displayed. Changed sigma30→60%: premiums.189939/.192810 displayed. Switched back to V2: original metrics and dedicated V2 download returned.
- Downloaded two actual lab files from the cloud, at sigma.3 and.6, all other defaults unchanged; each had101 rows and32 fields. Downloaded V2 default CSV,101 rows and24 fields. Checked every cell against fresh calculations from the remote source, not against pre-generated CSVs.
- Default lab3232/3232 and V22424/2424 numeric cells were exactly equal. Sigma.6 lab2608/3232 cells were exactly equal; maximum absolute discrepancy1.1368683772161603e-13, consistent with platform floating-point rounding. All cells passed `math.isclose` with relative and absolute tolerances1e-12; fields, row counts and schema were checked separately.
- Local pre-release390px/320px viewport inspection passed with internally scrolling tables; this release does not claim testing on physical mobile hardware or exhaustive input combinations.

## Model limits

Educational hypothetical European futures-call benchmark, not actual American ICE Coffee C pricing, a forecast, investment advice or trade execution. Pricing and premium financing share one deterministic rate; terminal costs assume matched timing and spot/futures prices. See README for full assumptions, cashflow basis and AI-assistance disclosure.

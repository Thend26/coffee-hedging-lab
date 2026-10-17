"""Export the independent teaching example, then verify the saved CSV."""

import csv
from pathlib import Path

from scenarios import build_scenarios, scenarios_to_csv


def main():
    rows = build_scenarios(
        quantity=1000, current_spot=1.20, futures_price=1.22,
        strike=1.25, premium=.07, price_min=.60, price_max=1.80,
    )
    output = Path(__file__).parent / 'output' / 'coffee_hedging_scenarios.csv'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(scenarios_to_csv(rows), encoding='utf-8')
    with output.open(encoding='utf-8', newline='') as file:
        saved = list(csv.DictReader(file))
    assert len(saved) == 101
    for source, restored in zip(rows, saved):
        for key, value in source.items():
            assert float(restored[key]) == value
    print(f'Exported and verified {len(saved)} rows, {len(saved[0])} columns: {output}')


if __name__ == '__main__':
    main()

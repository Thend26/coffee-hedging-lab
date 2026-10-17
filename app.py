"""Local educational dashboard; run with streamlit run app.py."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from calculations import unhedged_cost, partial_futures_hedged_cost, partial_call_hedged_cost
from analysis import break_even_vs_unhedged, budget_summary
from scenarios import build_scenarios, scenarios_to_csv

st.set_page_config(page_title='Coffee Hedging Lab', layout='wide')
st.title('Coffee Hedging Lab')
st.markdown('Compare procurement costs across future coffee prices.')
st.caption('Buyer perspective · Independent educational project · Hypothetical inputs, not live quotes')

with st.sidebar:
    st.header('Procurement assumptions')
    quantity = st.number_input('Purchase quantity (lb)', min_value=0.0, max_value=1e9,
                               value=1000.0, step=100.0, key='quantity')
    spot = st.number_input('Current reference price (USD/lb)', min_value=0.0,
                           max_value=1e6, value=1.2, step=.01, format='%.4f', key='spot')
    futures = st.number_input('Locked futures price (USD/lb)', min_value=0.0,
                              max_value=1e6, value=1.22, step=.01, format='%.4f', key='futures')
    strike = st.number_input('Call strike (USD/lb)', min_value=0.0,
                             max_value=1e6, value=1.25, step=.01, format='%.4f', key='strike')
    premium = st.number_input('Call premium (USD/lb)', min_value=0.0,
                              max_value=1e6, value=.07, step=.01, format='%.4f', key='premium')
    hedge_ratio = st.slider('Shared hedge ratio', min_value=0.0, max_value=1.0,
                            value=1.0, step=.05, key='hedge_ratio',
                            help='Fraction of purchase quantity hedged by each strategy: 0.50 means 50%.')
    budget = st.number_input('Procurement budget (USD)', min_value=0.0,
                              max_value=1e15, value=1300.0, step=100.0, key='budget')
    st.subheader('Terminal price scenarios')
    low = st.number_input('Minimum terminal price (USD/lb)', min_value=0.0,
                          max_value=1e6, value=.6, step=.1, key='price_min')
    high = st.number_input('Maximum terminal price (USD/lb)', min_value=0.0,
                           max_value=1e6, value=1.8, step=.1, key='price_max')
    st.caption('101 evenly spaced scenarios. Quantity ≤ 1 billion lb and prices ≤ $1 million/lb are interface safety limits, not market assumptions.')

try:
    rows = build_scenarios(quantity, spot, futures, strike, premium, low, high,
                           hedge_ratio=hedge_ratio, budget_usd=budget)
    reference = unhedged_cost(quantity, spot)
    futures_reference = partial_futures_hedged_cost(quantity, spot, futures, hedge_ratio)
    call_reference = partial_call_hedged_cost(quantity, spot, strike, premium, hedge_ratio)
    break_even = break_even_vs_unhedged(futures, strike, premium, hedge_ratio)
    stress = budget_summary(rows)
    csv_text = scenarios_to_csv(rows)
except (TypeError, ValueError, OverflowError) as error:
    st.error(f'Please check your inputs: {error}')
    st.stop()

cols = st.columns(3)
cols[0].metric('Unhedged cost at reference S', f'${reference:,.2f}')
cols[1].metric('Futures-hedged cost at reference S', f'${futures_reference:,.2f}')
cols[2].metric('Call-hedged cost at reference S', f'${call_reference:,.2f}')
st.caption(f'Hypothetical terminal S = current reference price ${spot:.4f}/lb; not a forecast. Shared hedge ratio: {hedge_ratio:.0%}.')
if hedge_ratio == 1:
    st.write(f'Full hedge cost bounds: futures fixed cost USD {quantity*futures:,.2f}; call cost ceiling USD {quantity*(strike+premium):,.2f}, including premium.')
else:
    st.write('Partial hedges have no global cost cap: the unhedged quantity remains exposed to rising prices.')

frame = pd.DataFrame(rows)
fig = go.Figure()
for label, field, color, dash in (
    ('Unhedged', 'unhedged_cost_usd', '#2864a3', 'solid'),
    ('Futures hedge', 'futures_hedged_cost_usd', '#bd6426', 'dash'),
    ('Call option hedge', 'call_hedged_cost_usd', '#218362', 'dashdot'),
):
    fig.add_trace(go.Scatter(x=frame['terminal_price_usd_per_lb'], y=frame[field],
                            name=label, mode='lines', line=dict(color=color, dash=dash, width=3),
                            hovertemplate='%{x:.4f} USD/lb<br>%{y:,.2f} USD<extra>%{fullData.name}</extra>'))
fig.add_hline(y=budget, line_dash='dot', line_color='#9b3347',
              annotation_text='Budget (USD)', annotation_position='bottom right')
fig.update_layout(template='plotly_white', height=450,
                  xaxis_title='Terminal coffee price (USD/lb)',
                  yaxis_title='Total procurement cost (USD)',
                  legend=dict(orientation='h', y=1.13, x=0),
                  margin=dict(l=20, r=20, t=50, b=20))
st.subheader('Compare the three strategies')
st.plotly_chart(fig, width='stretch')
st.caption('Lines connect discrete scenarios; the call payoff changes slope at the strike. Lower cost in one scenario does not make a strategy universally better.')

st.subheader('Scenario data')
st.caption('USD/lb denotes price per pound; USD denotes total cash amounts. CSV preserves unrounded calculation values and all input parameters.')
st.dataframe(frame, hide_index=True, width='stretch')
st.download_button('Download all 101 scenarios as CSV', csv_text.encode('utf-8'),
                   file_name='coffee_hedging_scenarios.csv', mime='text/csv', key='download')

st.subheader('Analytical break-even versus unhedged')
for label, key in (('Futures hedge', 'futures'), ('Call hedge', 'call')):
    result = break_even[key]
    if result['kind'] == 'all_prices':
        explanation = 'All nonnegative terminal prices have equal costs because the hedge ratio is zero.'
    elif result['kind'] == 'interval':
        explanation = (f"Equal costs for 0 ≤ S ≤ {result['upper_usd_per_lb']:.4f} USD/lb; "
                       'the call hedge is cheaper above that interval (zero premium).')
    else:
        explanation = (f"Equal costs at S = {result['lower_usd_per_lb']:.4f} USD/lb; "
                       'hedging is cheaper above, more costly below.')
    st.write(f'{label}: {explanation}')
st.caption('Analytical thresholds are independent of the scenario grid. For positive hedge ratios, the ratio changes savings magnitude, not the break-even price.')

st.subheader('Budget stress within the selected price interval')
summary_rows = []
for label, prefix in (('Unhedged', 'unhedged'), ('Futures hedge', 'futures_hedged'),
                       ('Call hedge', 'call_hedged')):
    result = stress[prefix]
    summary_rows.append({'Strategy': label,
                         'Scenarios over budget': result['exceedance_count'],
                         'Maximum cost (USD)': result['max_cost_usd'],
                         'Maximum overspend (USD)': result['max_overspend_usd']})
st.dataframe(pd.DataFrame(summary_rows), hide_index=True, width='stretch',
              column_config={'Maximum cost (USD)': st.column_config.NumberColumn(format='$%.2f'),
                             'Maximum overspend (USD)': st.column_config.NumberColumn(format='$%.2f')})
st.caption(f'Budget USD {budget:,.2f}; 101 equally spaced prices from {low:.4f} to {high:.4f} USD/lb. Counts are not probabilities. Equality with budget is not overspending. Maxima apply only to this interval, not all possible prices.')

with st.expander('How the calculations work'):
    st.code('Unhedged: Q × S\nFutures hedge: Q × [(1-h) × S + h × F]\nCall hedge: Q × [(1-h) × S + h × min(S,K) + h × p]\nSavings: unhedged cost − hedged cost\nBudget gap: cost − budget\nOverspend: max(cost − budget, 0)')
    st.write('Q is purchase quantity; S terminal price; F futures price; K strike; p per-pound premium; h the shared hedge ratio. Premium is paid only on hQ. Current spot is reference only. V2 CSV includes all inputs and unrounded cashflows, savings and budget fields.')
    st.write(f'Cost slopes versus S: unhedged Q = {quantity:,.2f}; futures Q(1-h) = {quantity*(1-hedge_ratio):,.2f}; calls Q below K and Q(1-h) above K. Call cost is continuous at K; when h>0 it is not differentiable there. Slopes measure USD cost change per USD/lb price change, not guaranteed percentage loss reduction.')
with st.expander('Assumptions and limitations', expanded=True):
    st.write('Perfect quantity, timing and price-reference matching is assumed. Basis risk, contract lot sizes, margin funding, interest, fees, taxes, counterparty default and delivery differences are excluded. Option premium is an undiscounted cash expenditure; this is not a time-adjusted terminal valuation.')
    st.write('This tool does not price options, forecast coffee prices, recommend trades or execute orders. It is independent of Citi and Forage. Interface safety limits do not establish real-world suitability.')

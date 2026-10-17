"""Local educational dashboard; run with streamlit run app.py."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from calculations import unhedged_cost, futures_hedged_cost, call_hedged_cost
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
    st.subheader('Terminal price scenarios')
    low = st.number_input('Minimum terminal price (USD/lb)', min_value=0.0,
                          max_value=1e6, value=.6, step=.1, key='price_min')
    high = st.number_input('Maximum terminal price (USD/lb)', min_value=0.0,
                           max_value=1e6, value=1.8, step=.1, key='price_max')
    st.caption('101 evenly spaced scenarios. Quantity ≤ 1 billion lb and prices ≤ $1 million/lb are interface safety limits, not market assumptions.')

try:
    rows = build_scenarios(quantity, spot, futures, strike, premium, low, high)
    reference = unhedged_cost(quantity, spot)
    locked_cost = futures_hedged_cost(quantity, low, futures)
    ceiling = call_hedged_cost(quantity, strike, strike, premium)
    csv_text = scenarios_to_csv(rows)
except (TypeError, ValueError, OverflowError) as error:
    st.error(f'Please check your inputs: {error}')
    st.stop()

cols = st.columns(3)
cols[0].metric('Current reference purchase cost', f'${reference:,.2f}')
cols[1].metric('Simplified futures-locked cost', f'${locked_cost:,.2f}')
cols[2].metric('Simplified call-hedged cost ceiling', f'${ceiling:,.2f}')
st.caption('Reference cost is a benchmark, not a forecast. The ceiling includes the undiscounted option premium.')

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

with st.expander('How the calculations work'):
    st.code('Unhedged: Q × S\nFutures hedge: Q × S − Q × (S − F) = Q × F\nCall hedge: Q × S − Q × max(S − K, 0) + Q × p\n          = Q × min(S, K) + Q × p')
    st.write('Q is purchase quantity; S is terminal price; F is locked futures price; K is strike; p is per-pound option premium. Current spot is a reference only. Futures P&L and call payoff remain separate columns in the export.')
with st.expander('Assumptions and limitations', expanded=True):
    st.write('Perfect quantity, timing and price-reference matching is assumed. Basis risk, contract lot sizes, margin funding, interest, fees, taxes, counterparty default and delivery differences are excluded. Option premium is an undiscounted cash expenditure; this is not a time-adjusted terminal valuation.')
    st.write('This tool does not price options, forecast coffee prices, recommend trades or execute orders. It is independent of Citi and Forage. Interface safety limits do not establish real-world suitability.')

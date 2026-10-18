"""Separate Streamlit laboratory with all procurement amounts valued at T."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analysis import break_even_vs_unhedged, budget_summary
from lab_scenarios import build_lab_scenarios, lab_scenarios_to_csv
from pricing_sensitivity import build_pricing_sensitivities


def render_lab() -> None:
    st.header('Black–76 laboratory')
    st.info('Hypothetical European cash-settled futures call. All procurement costs and budgets are valued at expiry T. Not live quotes or a trade recommendation.')
    with st.sidebar:
        st.header('Laboratory assumptions')
        q = st.number_input('Purchase quantity (lb)', 0.0, 1e9, 1000.0, 100.0, key='lab_quantity')
        spot = st.number_input('Current reference spot (USD/lb)', 0.0, 1e6, 1.2, .01, key='lab_spot')
        f = st.number_input('Current futures F0 (USD/lb)', 0.0, 1e6, 1.22, .01, key='lab_futures')
        k = st.number_input('Call strike K (USD/lb)', 0.0, 1e6, 1.25, .01, key='lab_strike')
        sigma_pct = st.number_input('Annual volatility (%)', 0.0, 100.0, 30.0, 5.0, key='lab_volatility')
        t = st.number_input('Time to expiry (years)', 0.0, 2.0, .5, .1, key='lab_expiry')
        rate_pct = st.number_input('Continuous pricing / financing rate (%)', -10.0, 20.0, 3.0, 1.0, key='lab_rate')
        h = st.slider('Shared hedge ratio', 0.0, 1.0, 1.0, .05, key='lab_hedge_ratio')
        budget = st.number_input('Budget at expiry T (USD)', 0.0, 1e15, 1300.0, 100.0, key='lab_budget')
        low = st.number_input('Minimum terminal price (USD/lb)', 0.0, 1e6, .6, .1, key='lab_price_min')
        high = st.number_input('Maximum terminal price (USD/lb)', 0.0, 1e6, 1.8, .1, key='lab_price_max')
        st.caption('Interface safety limits are not market assumptions. Volatility and rate percentages are converted to fractions once.')
    sigma, r = sigma_pct / 100, rate_pct / 100
    try:
        rows = build_lab_scenarios(q, spot, f, k, sigma, t, r, low, high, h, budget)
        sensitivity = build_pricing_sensitivities(f, k, sigma, t, r)
        quote = rows[0]
        p = quote['model_premium_terminal_usd_per_lb']
        thresholds = break_even_vs_unhedged(f, k, p, h)
        stress = budget_summary(rows)
        csv_text = lab_scenarios_to_csv(rows)
    except (TypeError, ValueError, OverflowError) as error:
        st.error(f'Please check your inputs: {error}')
        st.stop()

    columns = st.columns(2)
    columns[0].metric('Premium today (USD/lb)', f"${quote['model_premium_today_usd_per_lb']:.6f}")
    columns[1].metric('Funded premium at T (USD/lb)', f'${p:.6f}')
    columns[0].metric('Total premium today (USD)', f"${quote['total_premium_today_usd']:,.2f}")
    columns[1].metric('Total funded premium at T (USD)', f"${quote['total_premium_terminal_usd']:,.2f}")
    st.caption('Total premiums apply to h × Q only. With the same pricing and funding rate, pT = c0 × exp(rT) = U; fixed F0, K, volatility and T imply a rate-independent terminal premium.')

    st.subheader('Controlled pricing sensitivities')
    for name, xkey, title in (
        ('volatility_curve', 'volatility_annual', 'Annual volatility (fraction)'),
        ('maturity_curve', 'time_to_expiry_years', 'Time to expiry (years)'),
    ):
        records = sensitivity[name]
        fig = go.Figure(go.Scatter(
            x=[row[xkey] for row in records],
            y=[row['premium_today_usd_per_lb'] for row in records],
            customdata=[[row['premium_terminal_usd_per_lb']] for row in records],
            mode='lines+markers', name='Premium today',
            hovertemplate='Parameter: %{x}<br>Today: %{y:.6f} USD/lb<br>Funded at T: %{customdata[0]:.6f} USD/lb<extra></extra>'))
        fig.update_layout(template='plotly_white', xaxis_title=title,
                          yaxis_title='Premium today (USD/lb)', height=330)
        st.plotly_chart(fig, width='stretch', key='lab_'+name)
    st.caption(f'F0={f:.4f}, K={k:.4f}, r={r:.2%} fixed. Volatility curve fixes T={t:g}; maturity curve fixes volatility={sigma:.2%}. The maturity experiment holds F0 fixed: it is not a market term structure or forecast. Discounted call prices need not always increase with T.')
    heat = pd.DataFrame(sensitivity['heatmap'])
    today_grid = heat.pivot(index='time_to_expiry_years', columns='volatility_annual', values='premium_today_usd_per_lb')
    terminal_grid = heat.pivot(index='time_to_expiry_years', columns='volatility_annual', values='premium_terminal_usd_per_lb')
    fig = go.Figure(go.Heatmap(x=today_grid.columns, y=today_grid.index,
                             z=today_grid.values, customdata=terminal_grid.values,
                             colorbar_title='Today USD/lb',
                             hovertemplate='Volatility: %{x}<br>T: %{y} years<br>Today: %{z:.6f} USD/lb<br>Funded at T: %{customdata:.6f} USD/lb<extra></extra>'))
    fig.update_layout(xaxis_title='Annual volatility (fraction)', yaxis_title='Expiry (years)', height=400)
    st.plotly_chart(fig, width='stretch', key='lab_heatmap')

    st.subheader('Procurement costs at expiry T')
    frame = pd.DataFrame(rows)
    fig = go.Figure()
    for label, prefix in (('Unhedged', 'unhedged'), ('Futures hedge', 'futures_hedged'), ('Call hedge', 'call_hedged')):
        fig.add_trace(go.Scatter(x=frame['terminal_price_usd_per_lb'], y=frame[prefix+'_cost_usd'], mode='lines', name=label))
    fig.add_hline(y=budget, line_dash='dot', annotation_text='Budget at T')
    fig.update_layout(template='plotly_white', xaxis_title='Terminal price (USD/lb)',
                      yaxis_title='Procurement cost at T (USD)', height=400,
                      legend=dict(orientation='h', y=1.15))
    st.plotly_chart(fig, width='stretch', key='lab_costs')
    if h < 1:
        st.caption('Partial hedges retain unhedged exposure and have no global cost cap.')
    else:
        st.write(f'Full hedge: futures fixed cost USD {q*f:,.2f}; call cost ceiling at T USD {q*(k+p):,.2f}.')
    st.dataframe(frame, hide_index=True, width='stretch')
    st.download_button('Download Black–76 terminal scenarios CSV', csv_text.encode('utf-8'),
                       file_name='coffee_black76_terminal_scenarios.csv', mime='text/csv', key='lab_download')
    st.caption('101 scenarios × 32 numeric fields; unrounded. premium_usd_per_lb and option_premium_usd are TERMINAL amounts in this lab CSV, unlike V2’s simplified cash basis. Current-premium metadata is separately labelled.')

    st.subheader('Analytical break-even versus unhedged')
    for label, result in thresholds.items():
        if result['kind'] == 'all_prices':
            text = 'All nonnegative terminal prices (zero hedge).'
        elif result['kind'] == 'interval':
            text = f"Equal costs for 0 ≤ S ≤ {result['upper_usd_per_lb']:.4f} USD/lb; call hedge cheaper above (zero premium)."
        else:
            text = f"Equal costs at S={result['lower_usd_per_lb']:.4f} USD/lb; hedge cheaper above, more costly below."
        st.write(f'{label}: {text}')
    st.caption('Call break-even uses K + pT, not K + c0, when h>0 and pT>0. Thresholds are analytical, not estimated from the grid.')
    st.subheader('Budget stress within selected terminal prices')
    st.dataframe(pd.DataFrame([dict(Strategy=key, **value) for key, value in stress.items()]), hide_index=True, width='stretch')
    st.caption('Scenario counts are not probabilities. Equality is not overspending; maxima apply only to the selected interval.')
    with st.expander('Sensitivity data (current and terminal premium)'):
        st.dataframe(pd.DataFrame(sensitivity['volatility_curve']), hide_index=True, width='stretch')
        st.dataframe(pd.DataFrame(sensitivity['maturity_curve']), hide_index=True, width='stretch')
    with st.expander('Model, cashflow timeline and limitations', expanded=True):
        st.latex(r'c_0=e^{-rT}[F_0N(d_1)-KN(d_2)],\quad p_T=c_0e^{rT}')
        st.latex(r'C_T=Q[(1-h)S_T+h\min(S_T,K)+hp_T]')
        st.write('At time 0: finance the premium c0 on hQ. At T: pay procurement costs, receive the cash-settled payoff and repay the funded premium. F0 is a current futures price, not spot or a terminal scenario. Risk-neutral lognormal futures; constant volatility and deterministic rate. Zero expiry/volatility use intrinsic-value limits.')
        st.write('Assumes spot equals futures at matched expiry and purchase date; excludes basis risk, contract lots, margin funding, fees, tax, credit risk and delivery differences. This European benchmark does not reproduce the American-style ICE Coffee C option. No real-world outcome probabilities, price forecasts or order execution.')
        st.markdown('[Black–76 formula reference](https://www.lme.com/Trading/Contract-types/Options/Black-Scholes-76-Formula) · [ICE Coffee C specifications](https://www.ice.com/products/14/coffee-c-)')

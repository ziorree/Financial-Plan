"""Portfolio analytics tab."""
import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
from tabs.shared import NUM_MONTHS, build_projection_frames


def _hex_to_rgba(hex_color, alpha):
    hc = hex_color.lstrip("#")
    if len(hc) != 6:
        return f"rgba(45,111,181,{alpha})"
    r = int(hc[0:2], 16)
    g = int(hc[2:4], 16)
    b = int(hc[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def render(holdings_by_account, all_holdings, live_prices, cash_balance,
           growth_rate, savings_yield, include_shared, portfolio_names):
    st.title("Portfolio Analytics")
    budget_months = st.session_state.months
    balances_df, shares_df = build_projection_frames(
        holdings_by_account,
        live_prices,
        cash_balance,
        growth_rate,
        savings_yield,
        include_shared,
        budget_months,
        st.session_state.share_alloc_pcts,
        total_months=NUM_MONTHS,
    )
    month_labels = [(datetime.now() + relativedelta(months=i)).strftime("%b %Y") for i in range(NUM_MONTHS + 1)]
    balances_df["Month"] = month_labels[:len(balances_df)]
    shares_df["Month"] = month_labels[:len(shares_df)]

    account_columns = [col for col in balances_df.columns if col not in {"MonthIndex", "Month", "Cash", "Total"}]
    selected_accounts = st.multiselect(
        "Portfolios to analyze",
        options=account_columns,
        default=account_columns,
    )
    if not selected_accounts:
        st.info("Select at least one portfolio to view analytics.")
        return

    chart_df = balances_df.set_index("Month")[[*selected_accounts, "Total"]]
    starting_total = sum(float(balances_df[acct].iloc[0]) for acct in selected_accounts)
    ending_total = sum(float(balances_df[acct].iloc[-1]) for acct in selected_accounts)
    projected_gain = ending_total - starting_total
    gain_pct = (projected_gain / max(starting_total, 1.0)) * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Selected Current", f"${starting_total:,.0f}")
    c2.metric("Selected 12-Mo", f"${ending_total:,.0f}", delta=f"+${projected_gain:,.0f} ({gain_pct:+.1f}%)")
    c3.metric("Annual Growth", f"{growth_rate:.2%}")
    c4.metric("Accounts Selected", str(len(selected_accounts)))

    st.markdown("---")
    st.subheader("Selected Portfolio Value")
    _BLUES = ["#2d6fb5","#5a9fd4","#1a4a7a","#8ec5ff","#103b63","#4a90d9","#0d2d52","#7ab8f5"]
    fig_line = go.Figure()
    for i, acct in enumerate(selected_accounts):
        fig_line.add_trace(go.Scatter(
            x=chart_df.index, y=chart_df[acct],
            mode="lines+markers", name=acct,
            line=dict(color=_BLUES[i % len(_BLUES)], width=2),
        ))
    fig_line.update_layout(
        template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#f7fbff",
        font=dict(color="#111827"), margin=dict(l=10, r=10, t=10, b=10),
        yaxis=dict(tickprefix="$", tickformat=",.0f", gridcolor="#dceeff"),
        xaxis=dict(gridcolor="#dceeff"), legend=dict(font=dict(color="#111827")),
        height=380,
    )
    st.plotly_chart(fig_line, use_container_width=True)

    st.markdown("---")
    st.subheader("Selected Portfolio Breakdown")
    fig_area = go.Figure()
    for i, acct in enumerate(selected_accounts):
        color = _BLUES[i % len(_BLUES)]
        fig_area.add_trace(go.Scatter(
            x=chart_df.index, y=chart_df[acct],
            mode="lines", name=acct, stackgroup="one",
            line=dict(color=color, width=1),
            fillcolor=_hex_to_rgba(color, 0.30),
        ))
    fig_area.update_layout(
        template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#f7fbff",
        font=dict(color="#111827"), margin=dict(l=10, r=10, t=10, b=10),
        yaxis=dict(tickprefix="$", tickformat=",.0f", gridcolor="#dceeff"),
        xaxis=dict(gridcolor="#dceeff"), legend=dict(font=dict(color="#111827")),
        height=380,
    )
    st.plotly_chart(fig_area, use_container_width=True)

    st.markdown("---")
    st.subheader("12-Month Account Callouts")
    callout_cols = st.columns(min(max(len(selected_accounts), 1), 4))
    for idx, acct in enumerate(selected_accounts):
        current_val = float(balances_df[acct].iloc[0])
        future_val = float(balances_df[acct].iloc[-1])
        delta_val = future_val - current_val
        callout_cols[idx % len(callout_cols)].metric(
            acct,
            f"${future_val:,.0f}",
            delta=f"+${delta_val:,.0f}",
        )

    st.markdown("---")
    st.subheader("Projected Share Count Growth")
    share_cols = [col for col in shares_df.columns if col not in {"MonthIndex", "Month"} and any(col.endswith(f"({acct})") for acct in selected_accounts)]
    if share_cols:
        fig_shares = go.Figure()
        for i, col in enumerate(share_cols):
            fig_shares.add_trace(go.Scatter(
                x=shares_df["Month"], y=shares_df[col],
                mode="lines+markers", name=col,
                line=dict(color=_BLUES[i % len(_BLUES)], width=2),
            ))
        fig_shares.update_layout(
            template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#f7fbff",
            font=dict(color="#111827"), margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(tickformat=",.2f", gridcolor="#dceeff"),
            xaxis=dict(gridcolor="#dceeff"), legend=dict(font=dict(color="#111827")),
            height=340,
        )
        st.plotly_chart(fig_shares, use_container_width=True)
        summary_rows = []
        for col in share_cols:
            current_shares = float(shares_df[col].iloc[0])
            future_shares = float(shares_df[col].iloc[-1])
            summary_rows.append({
                "Ticker (Account)": col,
                "Current Shares": f"{current_shares:,.4f}",
                "12-Mo Shares": f"{future_shares:,.4f}",
                "Shares Added": f"+{future_shares - current_shares:,.4f}",
            })
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    final_rows = []
    for acct in selected_accounts:
        current_val = float(balances_df[acct].iloc[0])
        future_val = float(balances_df[acct].iloc[-1])
        final_rows.append({
            "Account": acct,
            "Current Value": f"${current_val:,.0f}",
            "12-Mo Value": f"${future_val:,.0f}",
            "Growth": f"+${future_val - current_val:,.0f}",
        })
    st.dataframe(pd.DataFrame(final_rows), use_container_width=True, hide_index=True)
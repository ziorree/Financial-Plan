"""Portfolio Projection tab."""
import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
from tabs.shared import (
    INVEST_TO_PORTFOLIO, ROW_LABELS, NUM_MONTHS,
    save_projection, load_projection, build_projection_frames,
)


def render(holdings_by_account, all_holdings, live_prices, cash_balance,
           growth_rate, savings_yield, include_shared, portfolio_names):
    st.title("Portfolio Value Projection")
    budget_months = st.session_state.months
    now = datetime.now()
    month_labels = [(now + relativedelta(months=i)).strftime("%b %Y") for i in range(NUM_MONTHS + 1)]

    st.subheader("Current Positions")
    position_rows = []
    for acct_name in sorted(holdings_by_account.keys()):
        if acct_name == "Shared" and not include_shared:
            continue
        for holding in holdings_by_account[acct_name]:
            price = live_prices.get(holding["ticker"], holding["price"])
            value = holding["value"] if holding["ticker"] in {"SWVXX", "SWTXX", "SWPPX"} else holding["shares"] * price
            position_rows.append({
                "Account": acct_name,
                "Ticker": holding["ticker"],
                "Shares": f"{holding['shares']:,.4f}",
                "Price": f"${price:,.2f}",
                "Value": f"${value:,.0f}",
            })
    if position_rows:
        st.dataframe(pd.DataFrame(position_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No positions loaded yet. Use Upload Positions to import your statement.")

    st.markdown("---")
    st.subheader("Share Allocation")
    st.caption("Adjust how each budget contribution gets deployed inside each portfolio. Shared is excluded from automatic buying.")
    editable_accounts = [acct for acct in portfolio_names if acct != "Shared"]
    if not editable_accounts:
        st.info("Upload a position statement to configure allocations.")
    for acct in editable_accounts:
        tickers = [holding["ticker"] for holding in holdings_by_account.get(acct, [])]
        if not tickers:
            continue
        acct_pcts = st.session_state.share_alloc_pcts.setdefault(acct, {})
        for ticker in tickers:
            acct_pcts.setdefault(ticker, 0.0)
        st.markdown(f"**{acct}**")
        left_col, right_col = st.columns([8, 1.55])
        with left_col:
            per_row = 4
            for start in range(0, len(tickers), per_row):
                row_tickers = tickers[start:start + per_row]
                row_cols = st.columns(per_row)
                for idx, ticker in enumerate(row_tickers):
                    acct_pcts[ticker] = row_cols[idx].number_input(
                        ticker,
                        min_value=0.0,
                        max_value=100.0,
                        value=float(acct_pcts.get(ticker, 0.0)),
                        step=1.0,
                        key=f"alloc_pct_{acct}_{ticker}",
                        format="%.1f",
                    )
        total_pct = sum(float(acct_pcts.get(ticker, 0.0)) for ticker in tickers)
        remaining = 100.0 - total_pct
        color = "#1f8f58" if abs(remaining) < 0.1 else "#d3465a"
        with right_col:
            st.markdown(
                f"""
                <div class="alloc-total-box">
                    <div class="alloc-total-label">Total</div>
                    <div class="alloc-total-value" style="color:{color};">{total_pct:.1f}%</div>
                    <div class="alloc-total-rem">{remaining:+.1f}% remaining</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.subheader("Budget to Portfolio Mapping")
    mapping_rows = []
    for inv_field, portfolio in INVEST_TO_PORTFOLIO.items():
        if portfolio == "Shared" or portfolio not in holdings_by_account:
            continue
        allocations = st.session_state.share_alloc_pcts.get(portfolio, {})
        active = ", ".join(f"{ticker} {pct:.0f}%" for ticker, pct in allocations.items() if pct > 0)
        mapping_rows.append({
            "Budget Field": ROW_LABELS.get(inv_field, inv_field),
            "Portfolio": portfolio,
            "Allocation": active or "Not allocated",
            "Current Month": f"${float(budget_months[0].get(inv_field, 0.0)):,.0f}" if budget_months else "$0",
        })
    if mapping_rows:
        st.dataframe(pd.DataFrame(mapping_rows), use_container_width=True, hide_index=True)

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
    balances_df["Month"] = month_labels[:len(balances_df)]
    shares_df["Month"] = month_labels[:len(shares_df)]

    st.markdown("---")
    st.subheader("12-Month Value Projection")
    display_balances = balances_df.drop(columns=["MonthIndex"], errors="ignore").copy()
    for col in display_balances.columns:
        if col != "Month":
            display_balances[col] = display_balances[col].apply(lambda val: f"${val:,.0f}")
    st.dataframe(display_balances, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Projected Share Growth")
    share_cols = [col for col in shares_df.columns if col not in {"MonthIndex", "Month"}]
    if share_cols:
        _BLUES = ["#2d6fb5","#5a9fd4","#1a4a7a","#8ec5ff","#103b63","#4a90d9"]
        fig = go.Figure()
        for i, col in enumerate(share_cols):
            fig.add_trace(go.Scatter(
                x=shares_df["Month"], y=shares_df[col],
                mode="lines+markers", name=col,
                line=dict(color=_BLUES[i % len(_BLUES)], width=2),
            ))
        fig.update_layout(
            template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#f7fbff",
            font=dict(color="#111827"), margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(tickformat=",.2f", gridcolor="#dceeff"),
            xaxis=dict(gridcolor="#dceeff"), legend=dict(font=dict(color="#111827")),
            height=360,
        )
        st.plotly_chart(fig, use_container_width=True)
        summary_rows = []
        for col in share_cols:
            start_shares = float(shares_df[col].iloc[0])
            end_shares = float(shares_df[col].iloc[-1])
            summary_rows.append({
                "Ticker (Account)": col,
                "Current Shares": f"{start_shares:,.4f}",
                "12-Mo Shares": f"{end_shares:,.4f}",
                "Shares Added": f"+{end_shares - start_shares:,.4f}",
            })
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    current_total = float(balances_df["Total"].iloc[0]) if not balances_df.empty else 0.0
    projected_total = float(balances_df["Total"].iloc[-1]) if not balances_df.empty else 0.0
    gain = projected_total - current_total
    pct = (gain / max(current_total, 1.0)) * 100
    c1, c2, c3 = st.columns(3)
    c1.metric("Current Total", f"${current_total:,.0f}")
    c2.metric("Projected Total", f"${projected_total:,.0f}", delta=f"+${gain:,.0f} ({pct:+.1f}%)")
    c3.metric("Annual Growth", f"{growth_rate:.2%}")

    s1, s2 = st.columns(2)
    if s1.button("💾 Save Projection", key="save_proj_btn"):
        save_projection()
        st.success("Projection saved.")
    if s2.button("📂 Load Projection", key="load_proj_btn"):
        load_projection()
        st.success("Projection loaded.")
        st.rerun()
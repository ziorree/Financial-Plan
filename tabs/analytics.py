"""Analytics tab — portfolio growth charts and share projections."""
import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tabs.shared import (
    MONEY_MARKET_TICKERS, INVEST_TO_PORTFOLIO, NUM_MONTHS,
)
def render(holdings_by_account, all_holdings, live_prices, cash_balance,
           growth_rate, savings_yield, include_shared, portfolio_names):
    st.title("Portfolio Analytics")
    total_months = NUM_MONTHS  # 12-month projection matching the budget
    monthly_growth = 1 + growth_rate / 12
    now = datetime.now()
    budget_months = st.session_state.months
    # Build simulation state (deep copy)
    sim_state = {}
    for acct_name in sorted(holdings_by_account.keys()):
        if not include_shared and acct_name == "Shared":
            continue
        sim_state[acct_name] = []
        for h in holdings_by_account[acct_name]:
            t = h["ticker"]
            p = live_prices.get(t, h["price"])
            sim_state[acct_name].append({
                "ticker": t,
                "shares": float(h["shares"]),
                "price": float(p),
                "value": float(h["value"]) if t in MONEY_MARKET_TICKERS else float(h["shares"]) * float(p),
                "yield_pct": h.get("yield_pct", 0),
                "is_mm": t in MONEY_MARKET_TICKERS,
            })
    # Snapshot starting shares
    start_shares = {}
    for acct_name, holdings in sim_state.items():
        for h in holdings:
            if not h["is_mm"]:
                start_shares[f"{h['ticker']} ({acct_name})"] = h["shares"]
    # Run projection
    balance_rows = []
    share_rows = []
    for mo in range(total_months + 1):
        dt = now + relativedelta(months=mo)
        date_val = dt.strftime("%Y-%m")
        bal_row = {"Date": date_val}
        shr_row = {"Date": date_val}
        grand = 0.0
        for acct_name, holdings in sim_state.items():
            # Growth + DRIP
            if mo > 0:
                for h in holdings:
                    if h["is_mm"]:
                        h["value"] *= (1 + savings_yield / 12)
                    else:
                        if h["yield_pct"] > 0.02 and h["price"] > 0:
                            div = h["shares"] * h["price"] * h["yield_pct"] / 12
                            h["shares"] += div / h["price"]
                        h["price"] *= monthly_growth
            # Contributions from budget
            if mo > 0 and mo - 1 < len(budget_months):
                src = budget_months[mo - 1]
                contrib_dollars = 0.0
                for inv_field, portfolio in INVEST_TO_PORTFOLIO.items():
                    if portfolio == acct_name:
                        contrib_dollars += src.get(inv_field, 0.0)
                if contrib_dollars > 0:
                    pcts = st.session_state.share_alloc_pcts.get(acct_name, {})
                    for h in holdings:
                        t_pct = pcts.get(h["ticker"], 0.0)
                        if t_pct > 0 and h["price"] > 0 and not h["is_mm"]:
                            h["shares"] += (contrib_dollars * t_pct / 100.0) / h["price"]
                        elif t_pct > 0 and h["is_mm"]:
                            h["value"] += contrib_dollars * t_pct / 100.0
            # Sum values
            acct_total = sum(
                h["value"] if h["is_mm"] else h["shares"] * h["price"]
                for h in holdings
            )
            bal_row[acct_name] = acct_total
            grand += acct_total
            # Track shares for non-MM tickers
            for h in holdings:
                if not h["is_mm"]:
                    shr_row[f"{h['ticker']} ({acct_name})"] = h["shares"]
        bal_row["Total"] = grand
        balance_rows.append(bal_row)
        share_rows.append(shr_row)
    bal_df = pd.DataFrame(balance_rows).set_index("Date")
    shr_df = pd.DataFrame(share_rows).set_index("Date").fillna(0)
    # ── Total Portfolio Value ───────────────────────────────────────────────
    st.subheader("Total Portfolio Value")
    st.line_chart(bal_df[["Total"]], use_container_width=True)
    # ── Per-Portfolio Value Breakdown ───────────────────────────────────────
    st.subheader("Value by Portfolio")
    acct_cols = [c for c in bal_df.columns if c != "Total"]
    if acct_cols:
        st.area_chart(bal_df[acct_cols], use_container_width=True)
    # ── Share Count Growth ──────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Share Count Growth")
    st.caption("Projected shares owned over 12 months — includes monthly contributions at your set allocation + DRIP reinvestment.")
    # Show all non-MM share columns together
    all_share_cols = [c for c in shr_df.columns
                      if not any(mm in c for mm in MONEY_MARKET_TICKERS)]
    if all_share_cols:
        st.line_chart(shr_df[all_share_cols], use_container_width=True)
    # Per-account share charts
    for acct_name in sorted(sim_state.keys()):
        ticker_cols = [c for c in shr_df.columns if c.endswith(f"({acct_name})")]
        non_mm_cols = [c for c in ticker_cols
                       if not any(mm in c for mm in MONEY_MARKET_TICKERS)]
        if non_mm_cols:
            st.markdown(f"**{acct_name}**")
            st.line_chart(shr_df[non_mm_cols], use_container_width=True)
    # ── Shares Summary Table ────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Shares Summary")
    shares_summary = []
    for col in all_share_cols:
        s_start = shr_df[col].iloc[0]
        s_end = shr_df[col].iloc[-1]
        added = s_end - s_start
        shares_summary.append({
            "Ticker (Account)": col,
            "Current Shares": f"{s_start:,.2f}",
            "12-Mo Shares": f"{s_end:,.2f}",
            "Shares Added": f"+{added:,.2f}",
        })
    if shares_summary:
        st.dataframe(pd.DataFrame(shares_summary), use_container_width=True, hide_index=True)
    # ── Summary Metrics ────────────────────────────────────────────────────
    st.markdown("---")
    first_total = bal_df["Total"].iloc[0]
    last_total = bal_df["Total"].iloc[-1]
    gain = last_total - first_total
    pct = (gain / max(first_total, 1)) * 100
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current Total", f"${first_total:,.0f}")
    c2.metric("12-Mo Projected", f"${last_total:,.0f}",
              delta=f"+${gain:,.0f} ({pct:.1f}%)")
    c3.metric("Monthly Growth", f"{growth_rate / 12:.2%}")
    c4.metric("Annual Growth", f"{growth_rate:.1%}")
    # ── Final Values by Account ────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Final Values by Account")
    final_data = []
    for acct in acct_cols:
        start_val = bal_df[acct].iloc[0]
        end_val = bal_df[acct].iloc[-1]
        acct_gain = end_val - start_val
        final_data.append({
            "Account": acct,
            "Current": f"${start_val:,.0f}",
            "12-Mo": f"${end_val:,.0f}",
            "Growth": f"+${acct_gain:,.0f}",
        })
    if final_data:
        st.dataframe(pd.DataFrame(final_data), use_container_width=True, hide_index=True)

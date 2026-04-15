"""Portfolio Projection tab — budget investments buy shares, no extra contribution grid."""
import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tabs.shared import (
    MONEY_MARKET_TICKERS, INVEST_TO_PORTFOLIO, ROW_LABELS, NUM_MONTHS,
    save_projection, load_projection,
)
import copy
def render(holdings_by_account, all_holdings, live_prices, cash_balance,
           growth_rate, savings_yield, include_shared, portfolio_names):
    st.title("Portfolio Value Projection")
    monthly_growth = 1 + growth_rate / 12
    now = datetime.now()
    proj_months = 12
    month_labels = [(now + relativedelta(months=i)).strftime("%b %Y") for i in range(proj_months + 1)]
    # ── Current Positions ───────────────────────────────────────────────────
    st.subheader("Current Positions")
    pos_rows = []
    for acct_name in sorted(holdings_by_account.keys()):
        if not include_shared and acct_name == "Shared":
            continue
        for h in holdings_by_account[acct_name]:
            t = h["ticker"]
            p = live_prices.get(t, h["price"])
            val = h["value"] if t in MONEY_MARKET_TICKERS else h["shares"] * p
            pos_rows.append({
                "Account": acct_name, "Ticker": t,
                "Shares": f"{h['shares']:,.2f}", "Price": f"${p:,.2f}",
                "Value": f"${val:,.0f}",
            })
    if pos_rows:
        st.dataframe(pd.DataFrame(pos_rows), use_container_width=True, hide_index=True)
    st.markdown("---")
    # ── Share Allocation — percentage per ticker in each portfolio ────────
    st.subheader("Share Allocation")
    st.caption("Set the percentage of new contributions allocated to each ticker in each portfolio. Percentages should total 100%.")
    alloc_accts = [a for a in portfolio_names if include_shared or a != "Shared"]
    for acct in alloc_accts:
        tickers_in_acct = [h["ticker"] for h in holdings_by_account.get(acct, [])]
        if not tickers_in_acct:
            continue
        # Ensure session state has entries for all tickers in this account
        acct_pcts = st.session_state.share_alloc_pcts.get(acct, {})
        for t in tickers_in_acct:
            if t not in acct_pcts:
                acct_pcts[t] = 0.0
        st.session_state.share_alloc_pcts[acct] = acct_pcts
        st.markdown(f"**{acct}**")
        num_cols = min(len(tickers_in_acct) + 1, 7)  # +1 for total column
        cols = st.columns(num_cols)
        for j, t in enumerate(tickers_in_acct):
            val = acct_pcts.get(t, 0.0)
            acct_pcts[t] = cols[j % (num_cols - 1)].number_input(
                t, min_value=0.0, max_value=100.0, value=val, step=5.0,
                key=f"alloc_pct_{acct}_{t}", format="%.0f",
            )
        total_pct = sum(acct_pcts.get(t, 0.0) for t in tickers_in_acct)
        remaining = 100.0 - total_pct
        color = "#2ecc71" if abs(remaining) < 0.1 else "#e74c3c"
        cols[-1].markdown(f"**Total**")
        cols[-1].markdown(
            f'<span style="font-size:1.4em;font-weight:700;color:{color}">{total_pct:.0f}%</span><br>'
            f'<span style="font-size:0.85em;color:#888">{remaining:+.0f}% left</span>',
            unsafe_allow_html=True,
        )
    # ── Budget → Portfolio Mapping ──────────────────────────────────────────
    st.markdown("---")
    st.subheader("Budget → Portfolio Mapping")
    st.caption("Budget investment amounts are split across tickers by your allocation percentages above.")
    budget_months = st.session_state.months
    mapped_info = []
    for inv_field, portfolio in INVEST_TO_PORTFOLIO.items():
        if portfolio in holdings_by_account:
            vals = [budget_months[j].get(inv_field, 0) for j in range(min(3, len(budget_months)))]
            pcts = st.session_state.share_alloc_pcts.get(portfolio, {})
            active = {t: p for t, p in pcts.items() if p > 0}
            alloc_str = ", ".join(f"{t} {p:.0f}%" for t, p in active.items()) if active else "-"
            mapped_info.append({
                "Budget Field": ROW_LABELS.get(inv_field, inv_field),
                "Portfolio": portfolio, "Allocation": alloc_str,
                "Mo 1": f"${vals[0]:,.0f}" if len(vals) > 0 else "-",
                "Mo 2": f"${vals[1]:,.0f}" if len(vals) > 1 else "-",
                "Mo 3": f"${vals[2]:,.0f}" if len(vals) > 2 else "-",
            })
    if mapped_info:
        st.dataframe(pd.DataFrame(mapped_info), use_container_width=True, hide_index=True)
    # ── Projection Table ────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("12-Month Value Projection")
    # Deep-copy holdings into simulation state
    sim_state = {}
    for acct_name in sorted(holdings_by_account.keys()):
        if not include_shared and acct_name == "Shared":
            continue
        sim_state[acct_name] = []
        for h in holdings_by_account[acct_name]:
            t = h["ticker"]
            p = live_prices.get(t, h["price"])
            sim_state[acct_name].append({
                "ticker": t, "shares": float(h["shares"]), "price": float(p),
                "value": float(h["value"]) if t in MONEY_MARKET_TICKERS else float(h["shares"]) * float(p),
                "yield_pct": h.get("yield_pct", 0), "is_mm": t in MONEY_MARKET_TICKERS,
            })
    proj_rows = []
    for mo in range(proj_months + 1):
        dt = now + relativedelta(months=mo)
        row = {"Month": dt.strftime("%b %Y")}
        grand = 0.0
        for acct_name, holdings in sim_state.items():
            # Step 1: growth + DRIP
            if mo > 0:
                for h in holdings:
                    if h["is_mm"]:
                        h["value"] *= (1 + savings_yield / 12)
                    else:
                        if h["yield_pct"] > 0.02 and h["price"] > 0:
                            div = h["shares"] * h["price"] * h["yield_pct"] / 12
                            h["shares"] += div / h["price"]
                        h["price"] *= monthly_growth
            # Step 2: budget contributions → buy shares
            if mo > 0 and mo - 1 < len(budget_months):
                contrib_dollars = 0.0
                for inv_field, portfolio in INVEST_TO_PORTFOLIO.items():
                    if portfolio == acct_name:
                        contrib_dollars += budget_months[mo - 1].get(inv_field, 0.0)
                if contrib_dollars > 0:
                    pcts = st.session_state.share_alloc_pcts.get(acct_name, {})
                    allocated = False
                    for h in holdings:
                        t_pct = pcts.get(h["ticker"], 0.0)
                        if t_pct > 0 and h["price"] > 0 and not h["is_mm"]:
                            share_dollars = contrib_dollars * t_pct / 100.0
                            h["shares"] += share_dollars / h["price"]
                            allocated = True
                        elif t_pct > 0 and h["is_mm"]:
                            share_dollars = contrib_dollars * t_pct / 100.0
                            h["value"] += share_dollars
                            allocated = True
                    if not allocated:
                        for h in holdings:
                            if h["is_mm"]:
                                h["value"] += contrib_dollars
                                allocated = True
                                break
                        if not allocated and holdings:
                            for h in holdings:
                                if not h["is_mm"] and h["price"] > 0:
                                    h["shares"] += contrib_dollars / h["price"]
                                    break
            # Step 3: sum account value
            acct_total = sum(
                h["value"] if h["is_mm"] else h["shares"] * h["price"]
                for h in holdings
            )
            row[acct_name] = acct_total
            grand += acct_total
        row["Cash"] = cash_balance
        grand += cash_balance
        row["Total"] = grand
        proj_rows.append(row)
    pdf = pd.DataFrame(proj_rows)
    fmt_pdf = pdf.copy()
    for col in fmt_pdf.columns:
        if col != "Month":
            fmt_pdf[col] = pdf[col].apply(lambda v: f"${v:,.0f}")
    st.dataframe(fmt_pdf, use_container_width=True, hide_index=True)
    st.markdown("---")
    first_total = pdf["Total"].iloc[0]
    last_total = pdf["Total"].iloc[-1]
    gain = last_total - first_total
    pct = (gain / max(first_total, 1)) * 100
    s1, s2, s3 = st.columns(3)
    s1.metric("Current Total", f"${first_total:,.0f}")
    s2.metric(f"Projected ({proj_months}mo)", f"${last_total:,.0f}",
              delta=f"+${gain:,.0f} ({pct:+.1f}%)")
    s3.metric("Monthly Growth", f"{growth_rate/12:.2%}")
    st.markdown("---")
    ps1, ps2 = st.columns(2)
    if ps1.button("💾 Save Projection", key="save_proj_btn"):
        save_projection()
        st.success("Projection saved!")
    if ps2.button("📂 Load Projection", key="load_proj_btn"):
        load_projection()
        st.success("Projection loaded!")
        st.rerun()

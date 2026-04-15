"""Dividend Forecaster tab with NAV-erosion (return of capital) modelling."""
import streamlit as st
import pandas as pd
from datetime import datetime
from tabs.shared import (
    KNOWN_ROC_TICKERS, save_dividends, load_dividends,
)
def render(include_shared, live_prices, growth_rate):
    st.title("Dividend Income Forecaster")
    st.caption("Grouped by portfolio. Return-of-capital (ROC) tickers have NAV erosion applied in projections.")
    total_mo = 0.0
    total_val = 0.0
    # Group by account
    div_by_account = {}
    for hold_key, info in st.session_state.div_holdings.items():
        if not include_shared and info.get("account") == "Shared":
            continue
        acct = info.get("account", "Other")
        div_by_account.setdefault(acct, []).append((hold_key, info))
    for acct_name in sorted(div_by_account.keys()):
        st.markdown(f"### {acct_name}")
        acct_mo = 0.0
        acct_val = 0.0
        hc = st.columns([1.2, 1, 1, 1, 0.6, 1.2, 1, 1])
        hc[0].markdown("**Ticker**")
        hc[1].markdown("**Shares**")
        hc[2].markdown("**Price**")
        hc[3].markdown("**Yield %**")
        hc[4].markdown("**ROC**")
        hc[5].markdown("**Value**")
        hc[6].markdown("**Monthly $**")
        hc[7].markdown("**Annual $**")
        for hold_key, info in div_by_account[acct_name]:
            ticker = info.get("ticker", hold_key)
            cols = st.columns([1.2, 1, 1, 1, 0.6, 1.2, 1, 1])
            cols[0].markdown(f"**{ticker}**")
            info["shares"] = cols[1].number_input(
                "sh", value=float(info["shares"]), step=1.0,
                key=f"dsh_{hold_key}", label_visibility="collapsed",
            )
            info["price"] = cols[2].number_input(
                "pr", value=float(info["price"]), step=0.5,
                key=f"dpr_{hold_key}", label_visibility="collapsed",
            )
            info["yield_pct"] = cols[3].number_input(
                "yl", value=float(info["yield_pct"] * 100), step=0.1,
                key=f"dyl_{hold_key}", label_visibility="collapsed",
            ) / 100.0
            # Show ROC indicator
            roc_rate = KNOWN_ROC_TICKERS.get(ticker, 0)
            cols[4].markdown(f"{roc_rate*100:.0f}%" if roc_rate else "—")
            eq_val = info["shares"] * info["price"]
            mo_div = eq_val * info["yield_pct"] / 12
            cols[5].markdown(f"${eq_val:,.0f}")
            cols[6].markdown(f"**${mo_div:,.0f}**")
            cols[7].markdown(f"${mo_div * 12:,.0f}")
            acct_mo += mo_div
            acct_val += eq_val
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric(f"{acct_name} Value", f"${acct_val:,.0f}")
        sc2.metric(f"{acct_name} Monthly", f"${acct_mo:,.0f}")
        sc3.metric(f"{acct_name} Annual", f"${acct_mo * 12:,.0f}")
        total_mo += acct_mo
        total_val += acct_val
        st.markdown("---")
    with st.expander("Add New Holding"):
        ac = st.columns(5)
        new_t = ac[0].text_input("Ticker", key="new_tick")
        new_sh = ac[1].number_input("Shares", value=0.0, step=1.0, key="new_sh")
        new_pr = ac[2].number_input("Price", value=0.0, step=1.0, key="new_pr")
        new_yl = ac[3].number_input("Yield %", value=10.0, step=0.5, key="new_yl")
        new_ac = ac[4].text_input("Account", value="Main", key="new_acct")
        if st.button("Add") and new_t:
            key = f"{new_t.upper().strip()}_{new_ac}"
            st.session_state.div_holdings[key] = {
                "ticker": new_t.upper().strip(), "shares": new_sh, "price": new_pr,
                "yield_pct": new_yl / 100.0, "account": new_ac,
            }
            st.rerun()
    st.markdown("### Grand Total (Current)")
    tt1, tt2, tt3 = st.columns(3)
    tt1.metric("Total Portfolio", f"${total_val:,.0f}")
    tt2.markdown(
        f'<p class="money-label">Monthly Dividend Income</p>'
        f'<p class="money-pos">${total_mo:,.0f}</p>', unsafe_allow_html=True,
    )
    tt3.markdown(
        f'<p class="money-label">Annual Dividend Income</p>'
        f'<p class="money-pos">${total_mo * 12:,.0f}</p>', unsafe_allow_html=True,
    )
    # ── Future Month Projection (with NAV erosion) ──────────────────────────
    st.markdown("---")
    st.subheader("Project to a Future Month")
    st.caption("ROC tickers have their price reduced by the annual erosion rate each month, "
               "reflecting real-world NAV decay from return-of-capital distributions.")
    fc1, fc2, fc3 = st.columns(3)
    proj_mo = fc1.selectbox(
        "Month", list(range(1, 13)),
        format_func=lambda m: datetime(2000, m, 1).strftime("%B"),
        index=datetime.now().month - 1, key="div_proj_mo",
    )
    proj_yr = fc2.number_input(
        "Year", value=datetime.now().year + 1,
        min_value=datetime.now().year, max_value=2050, step=1, key="div_proj_yr",
    )
    reinvest = fc3.toggle("DRIP", value=True, key="div_drip")
    target_dt = datetime(int(proj_yr), proj_mo, 1)
    months_ahead = (target_dt.year - datetime.now().year) * 12 + (target_dt.month - datetime.now().month)
    if months_ahead < 0:
        months_ahead = 0
    # Simulate forward with NAV erosion for ROC tickers
    proj = {}
    for k, i in st.session_state.div_holdings.items():
        if not include_shared and i.get("account") == "Shared":
            continue
        ticker = i.get("ticker", k)
        proj[k] = {
            "ticker": ticker, "shares": float(i["shares"]),
            "price": float(live_prices.get(ticker, i["price"])),
            "yield_pct": float(i["yield_pct"]), "account": i.get("account", ""),
            "roc_rate": KNOWN_ROC_TICKERS.get(ticker, 0),
        }
    monthly_growth = 1 + growth_rate / 12
    for _ in range(months_ahead):
        for k, h in proj.items():
            md = h["shares"] * h["price"] * h["yield_pct"] / 12
            if reinvest and h["price"] > 0:
                h["shares"] += md / h["price"]
            # Apply market growth MINUS NAV erosion for ROC tickers
            roc_monthly = h["roc_rate"] / 12
            h["price"] *= (monthly_growth - roc_monthly)
    # Show projected results by account
    st.markdown(f"**Projected Dividend Income for {target_dt.strftime('%B %Y')} ({months_ahead} months out)**")
    proj_by_acct = {}
    for k, h in proj.items():
        acct = h["account"]
        md = h["shares"] * h["price"] * h["yield_pct"] / 12
        proj_by_acct.setdefault(acct, 0.0)
        proj_by_acct[acct] += md
    proj_total = 0.0
    pcols = st.columns(max(len(proj_by_acct), 1))
    for i, (acct, amt) in enumerate(sorted(proj_by_acct.items())):
        pcols[i % len(pcols)].metric(acct, f"${amt:,.0f}/mo")
        proj_total += amt
    st.metric(f"Total Monthly Income ({target_dt.strftime('%b %Y')})", f"${proj_total:,.0f}")
    st.metric(f"Annualized at {target_dt.strftime('%b %Y')}", f"${proj_total * 12:,.0f}")
    st.markdown("---")
    ds1, ds2 = st.columns(2)
    if ds1.button("💾 Save Dividends", key="save_div_btn"):
        save_dividends()
        st.success("Dividends saved!")
    if ds2.button("📂 Load Dividends", key="load_div_btn"):
        load_dividends()
        st.success("Dividends loaded!")
        st.rerun()

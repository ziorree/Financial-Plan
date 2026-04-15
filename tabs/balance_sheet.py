"""Balance Sheet tab."""
import streamlit as st
import pandas as pd
from tabs.shared import MONEY_MARKET_TICKERS
def render(holdings_by_account, all_holdings, live_prices, cash_balance, include_shared):
    st.title("Current Balance Sheet")
    asset_totals = {}
    for acct_name, acct_holdings in holdings_by_account.items():
        if not include_shared and acct_name == "Shared":
            continue
        total = 0.0
        for h in acct_holdings:
            t = h["ticker"]
            if t in MONEY_MARKET_TICKERS:
                total += h["value"]
            else:
                total += h["shares"] * live_prices.get(t, h["price"])
        asset_totals[acct_name] = total
    if cash_balance:
        asset_totals["Cash"] = cash_balance
    total_assets = sum(asset_totals.values())
    active_liabilities = {"Car Loan": -abs(st.session_state.car_loan_balance)}
    total_liabilities = sum(active_liabilities.values())
    net_worth_val = total_assets + total_liabilities
    c1, c2, c3 = st.columns(3)
    c1.metric("Net Worth", f"${net_worth_val:,.0f}")
    c2.metric("Total Assets", f"${total_assets:,.0f}")
    c3.metric("Total Liabilities", f"${total_liabilities:,.0f}")
    if live_prices:
        st.markdown("---")
        st.subheader("Live Prices")
        price_rows = [{"Ticker": t, "Live Price": f"${p:,.2f}"} for t, p in sorted(live_prices.items())]
        st.dataframe(pd.DataFrame(price_rows), use_container_width=True, hide_index=True)
    st.markdown("---")
    a_col, l_col = st.columns(2)
    with a_col:
        st.subheader("Assets by Account")
        for acct, total in sorted(asset_totals.items(), key=lambda x: -x[1]):
            st.metric(acct, f"${total:,.0f}")
    with l_col:
        st.subheader("Liabilities")
        for k, v in sorted(active_liabilities.items(), key=lambda x: x[1]):
            if v != 0:
                st.metric(k, f"${v:,.0f}")
    st.markdown("---")
    st.subheader("All Holdings")
    detail_rows = []
    for key, h in all_holdings.items():
        if not include_shared and h["account"] == "Shared":
            continue
        p = live_prices.get(h["ticker"], h["price"])
        live_val = h["shares"] * p if h["ticker"] not in MONEY_MARKET_TICKERS else h["value"]
        detail_rows.append({
            "Account": h["account"], "Ticker": h["ticker"],
            "Shares": f"{h['shares']:,.4f}", "Price": f"${p:,.2f}",
            "Value": f"${live_val:,.0f}",
            "Cost": f"${h['cost']:,.0f}" if h["cost"] else "-",
            "P/L": f"${h['pl']:,.0f}" if h["pl"] else "-",
        })
    if detail_rows:
        st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)
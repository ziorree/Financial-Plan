"""Retirement & Paycheck tab — uses actual portfolio positions for total net worth projection."""
import streamlit as st
import pandas as pd
from datetime import datetime
from tabs.shared import (
    MONEY_MARKET_TICKERS, NUM_MONTHS,
    calc_annual_taxes, save_retirement,
)
RETIREMENT_ACCOUNTS = {"PCRA Trust", "Roth IRA"}
def _compute_account_total(holdings_list, live_prices):
    """Sum value of a single account's holdings."""
    total = 0.0
    for h in holdings_list:
        t = h["ticker"]
        if t in MONEY_MARKET_TICKERS:
            total += h["value"]
        else:
            total += h["shares"] * live_prices.get(t, h["price"])
    return total
def _compute_portfolio_totals(holdings_by_account, live_prices, include_shared):
    """Return (roth_total, k401_total, brokerage_total) from real positions."""
    roth = 0.0
    k401 = 0.0
    brokerage = 0.0
    for acct_name, holdings in holdings_by_account.items():
        if not include_shared and acct_name == "Shared":
            continue
        val = _compute_account_total(holdings, live_prices)
        if acct_name == "Roth IRA":
            roth += val
        elif acct_name == "PCRA Trust":
            k401 += val
        else:
            brokerage += val
    return roth, k401, brokerage
def render(holdings_by_account, live_prices, cash_balance, growth_rate,
           savings_yield, include_shared):
    st.title("Retirement & Paycheck Calculator")
    ret = st.session_state.retirement
    # ── Compute paycheck numbers from saved settings ────────────────────────
    _gross_annual = ret["hourly_rate"] * ret["hours_per_year"]
    if ret["pay_frequency"] == "Biweekly":
        _checks = 26
    elif ret["pay_frequency"] == "Semi-Monthly":
        _checks = 24
    else:
        _checks = 12
    _gross_per_check = _gross_annual / _checks
    _k401_per_check = _gross_per_check * (ret["k401_contribution_pct"] / 100.0)
    _k401_annual = _gross_annual * (ret["k401_contribution_pct"] / 100.0)
    _k401_monthly = _k401_annual / 12
    _fed_tax, _state_tax, _fica = calc_annual_taxes(_gross_annual, ret["state"], _k401_annual)
    _fed_pc = _fed_tax / _checks
    _state_pc = _state_tax / _checks
    _fica_pc = _fica / _checks
    _net_pc = _gross_per_check - _k401_per_check - ret["benefits_per_check"] - _fed_pc - _state_pc - _fica_pc
    _net_annual = _net_pc * _checks
    # Current portfolio values from real positions — split by account type
    roth_from_positions, k401_from_positions, brokerage_from_positions = \
        _compute_portfolio_totals(holdings_by_account, live_prices, include_shared)
    portfolio_total = roth_from_positions + k401_from_positions + brokerage_from_positions
    tab1, tab2 = st.tabs(["Paycheck Calculator", "Retirement Projection"])
    # ── TAB 1: Paycheck ─────────────────────────────────────────────────────
    with tab1:
        st.subheader("Paycheck Calculator")
        p1, p2, p3 = st.columns(3)
        ret["hourly_rate"] = p1.number_input("Hourly Rate ($)", value=float(ret["hourly_rate"]),
                                              step=0.50, key="hr_rate", format="%.2f")
        ret["hours_per_year"] = p2.number_input("Hours/Year", value=int(ret["hours_per_year"]),
                                                 step=40, key="hr_hours")
        ret["pay_frequency"] = p3.selectbox("Pay Frequency",
                                             ["Biweekly", "Semi-Monthly", "Monthly"],
                                             index=["Biweekly", "Semi-Monthly", "Monthly"].index(
                                                 ret.get("pay_frequency", "Biweekly")),
                                             key="hr_freq")
        p4, p5, p6 = st.columns(3)
        ret["benefits_per_check"] = p4.number_input("Benefits/Check ($)",
                                                     value=float(ret["benefits_per_check"]),
                                                     step=10.0, key="hr_ben")
        ret["k401_contribution_pct"] = p5.number_input("401k Contribution %",
                                                        value=float(ret["k401_contribution_pct"]),
                                                        step=0.5, key="hr_k401", format="%.1f")
        ret["state"] = p6.selectbox("State", ["Florida", "Colorado"],
                                     index=["Florida", "Colorado"].index(
                                         ret.get("state", "Florida")),
                                     key="hr_state")
        p7, _, _ = st.columns(3)
        try:
            _pd_date = datetime.strptime(ret.get("next_payday", "2026-04-24"), "%Y-%m-%d").date()
        except Exception:
            from datetime import date as _date
            _pd_date = _date(2026, 4, 24)
        _pd_val = p7.date_input("Next Payday", value=_pd_date, key="hr_next_pd")
        ret["next_payday"] = _pd_val.strftime("%Y-%m-%d")
        st.markdown("---")
        st.markdown("### Per-Check Breakdown")
        bc = st.columns(4)
        bc[0].metric("Gross Pay", f"${_gross_per_check:,.2f}")
        bc[1].metric("401k", f"-${_k401_per_check:,.2f}")
        bc[2].metric("Benefits", f"-${ret['benefits_per_check']:,.2f}")
        bc[3].metric("Net Pay", f"${_net_pc:,.2f}")
        dc = st.columns(4)
        dc[0].metric("Federal Tax", f"-${_fed_pc:,.2f}")
        dc[1].metric("State Tax" + (" (CO)" if ret["state"] == "Colorado" else " (FL: $0)"),
                      f"-${_state_pc:,.2f}")
        dc[2].metric("FICA", f"-${_fica_pc:,.2f}")
        dc[3].metric("Checks/Year", f"{_checks}")
        st.markdown("### Annual Summary")
        ac = st.columns(4)
        ac[0].metric("Gross Annual", f"${_gross_annual:,.0f}")
        ac[1].metric("Net Annual", f"${_net_annual:,.0f}")
        ac[2].metric("401k Annual", f"${_k401_annual:,.0f}")
        ac[3].metric("Total Taxes", f"${_fed_tax + _state_tax + _fica:,.0f}")
        st.caption("Monthly take-home (avg): **\\${:,.0f}** | "
                   "3-check months: ~**\\${:,.0f}** | 2-check months: ~**\\${:,.0f}**".format(
                       _net_annual / 12, _net_pc * 3, _net_pc * 2))
        st.markdown("---")
        if st.button("💾 Save Paycheck Settings", key="save_pay_btn"):
            save_retirement()
            st.success("Paycheck settings saved!")
    # ── TAB 2: Retirement Projection ────────────────────────────────────────
    with tab2:
        st.subheader("Retirement Projection")
        st.caption(f"401k from paycheck: \\${_k401_monthly:,.0f}/mo (\\${_k401_annual:,.0f}/yr at {ret['k401_contribution_pct']}%)")
        # Show real portfolio balances as starting point
        st.info(
            f"📊 **Roth IRA (from positions): \\${roth_from_positions:,.0f}**  |  "
            f"**401k / PCRA Trust (from positions): \\${k401_from_positions:,.0f}**  |  "
            f"**Brokerage (other accounts): \\${brokerage_from_positions:,.0f}**"
        )
        st.caption(
            f"Total portfolio: \\${portfolio_total:,.0f}  |  "
            f"Cash: \\${cash_balance:,.0f}  |  Car Loan: -\\${abs(st.session_state.car_loan_balance):,.0f}"
        )
        r1, r2, r3 = st.columns(3)
        ret["current_age"] = r1.number_input("Current Age", value=int(ret["current_age"]),
                                              step=1, key="ret_age")
        ret["retirement_age"] = r2.number_input("Retirement Age", value=int(ret["retirement_age"]),
                                                 step=1, key="ret_ret_age")
        ret["annual_return"] = r3.number_input("Expected Annual Return %",
                                                value=float(ret["annual_return"]),
                                                step=0.5, key="ret_return", format="%.1f")
        r6, _ = st.columns(2)
        ret["monthly_roth_contribution"] = r6.number_input(
            "Monthly Roth Contribution ($)",
            value=float(ret["monthly_roth_contribution"]),
            step=50.0, key="ret_roth_mo",
        )
        st.markdown("---")
        st.markdown("**Post-Budget Contributions (after the 12-month budget period)**")
        pb1, pb2 = st.columns(2)
        ongoing_roth = pb1.number_input("Ongoing Monthly Roth ($)",
                                         value=float(ret["monthly_roth_contribution"]),
                                         step=50.0, key="ret_ongoing_roth")
        ongoing_k401_mo = pb2.number_input("Ongoing Monthly 401k ($)",
                                            value=float(_k401_monthly),
                                            step=50.0, key="ret_ongoing_k401")
        years_to_retire = max(0, int(ret["retirement_age"]) - int(ret["current_age"]))
        monthly_return = (1 + ret["annual_return"] / 100.0) ** (1 / 12) - 1
        # Start from real position balances
        roth_bal = roth_from_positions
        k401_bal = k401_from_positions
        brokerage_bal = brokerage_from_positions
        proj_rows = []
        for yr in range(years_to_retire + 1):
            age = int(ret["current_age"]) + yr
            proj_rows.append({
                "Age": age, "Year": datetime.now().year + yr,
                "Roth IRA": roth_bal, "401k (PCRA)": k401_bal,
                "Brokerage": brokerage_bal,
                "Total": roth_bal + k401_bal + brokerage_bal,
            })
            for mo in range(12):
                month_idx = yr * 12 + mo
                if month_idx < NUM_MONTHS:
                    roth_c = float(ret["monthly_roth_contribution"])
                    k401_c = _k401_monthly
                else:
                    roth_c = ongoing_roth
                    k401_c = ongoing_k401_mo
                roth_bal = roth_bal * (1 + monthly_return) + roth_c
                k401_bal = k401_bal * (1 + monthly_return) + k401_c
                brokerage_bal = brokerage_bal * (1 + monthly_return)
        rdf = pd.DataFrame(proj_rows)
        fmt_rdf = rdf.copy()
        for col in ["Roth IRA", "401k (PCRA)", "Brokerage", "Total"]:
            fmt_rdf[col] = rdf[col].apply(lambda v: f"${v:,.0f}")
        st.dataframe(fmt_rdf, use_container_width=True, hide_index=True,
                     height=min(700, 45 + 35 * len(proj_rows)))
        st.markdown("---")
        final = proj_rows[-1] if proj_rows else {"Roth IRA": 0, "401k (PCRA)": 0, "Brokerage": 0, "Total": 0}
        fc1, fc2, fc3, fc4 = st.columns(4)
        fc1.metric("Roth at Retirement", f"${final['Roth IRA']:,.0f}")
        fc2.metric("401k (PCRA) at Retirement", f"${final['401k (PCRA)']:,.0f}")
        fc3.metric("Brokerage at Retirement", f"${final['Brokerage']:,.0f}")
        fc4.metric("Total at Retirement", f"${final['Total']:,.0f}")
        swr = final["Total"] * 0.04
        sw1, sw2 = st.columns(2)
        sw1.metric("Safe Withdrawal (4% rule)", f"${swr:,.0f}/yr")
        sw2.metric("Monthly Equivalent", f"${swr/12:,.0f}/mo")
        st.markdown("---")
        if st.button("💾 Save Retirement Settings", key="save_ret_btn"):
            save_retirement()
            st.success("Retirement saved!")
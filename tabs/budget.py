"""12-Month Budget tab with car-payment-paid toggle per month."""
import streamlit as st
from datetime import datetime
from tabs.shared import (
    INCOME_FIELDS, EXPENSE_FIELDS, INVEST_FIELDS, ROW_LABELS,
    NUM_MONTHS, save_budget, load_budget,
)
from tabs.shared import compute_paycheck_schedule

def render(include_shared, net_per_check=0.0, paydays_per_month=None):
    if paydays_per_month is None:
        paydays_per_month = {}
    # ── Always recompute paycheck schedule from live session state ──────────
    _sched_ret = st.session_state.get("retirement", {})
    _sched_npc, _sched_pdm, _ = compute_paycheck_schedule(_sched_ret)
    if _sched_npc > 0:
        net_per_check = _sched_npc
        paydays_per_month = _sched_pdm

    st.title("12-Month Budget Planner")
    st.caption("Edit cells then press Apply. Car payment toggles let you mark months already paid.")
    months = st.session_state.months
    month_labels = [m["label"] for m in months]
    # Ensure car_paid_toggles exists
    if "car_paid_toggles" not in st.session_state:
        st.session_state.car_paid_toggles = {}
    # ── PAYCHECKS RECEIVED — shown first so they're always accessible ───────
    if "checks_received" not in st.session_state:
        st.session_state.checks_received = {}
    for j in range(NUM_MONTHS):
        date_key = months[j]["date"]
        expected = len(paydays_per_month.get(date_key, []))
        if date_key not in st.session_state.checks_received:
            st.session_state.checks_received[date_key] = [False] * expected
        current_list = st.session_state.checks_received[date_key]
        while len(current_list) < expected:
            current_list.append(False)
    # ── Pre-update net_pay from received checkboxes ─────────────────────────
    if net_per_check > 0:
        for j in range(NUM_MONTHS):
            date_key = months[j]["date"]
            expected = len(paydays_per_month.get(date_key, []))
            checks_list = st.session_state.checks_received.get(date_key, [])
            received = sum(1 for x in checks_list if x)
            if expected > 0 and received > 0:
                months[j]["net_pay"] = round(received * net_per_check, 2)
            else:
                months[j]["net_pay"] = round(expected * net_per_check, 2)
    def section_header(text):
        st.markdown(f'<div class="section-hdr">{text}</div>', unsafe_allow_html=True)
    # ── Paycheck Check-Off Widget (BEFORE the form) ─────────────────────────
    section_header("✅ PAYCHECKS RECEIVED")
    if net_per_check > 0:
        st.caption(
            f"Net per check: **\\${net_per_check:,.2f}**  ·  "
            "Check off each paycheck as you receive it — Net Pay in the budget updates automatically."
        )
        pay_hdr_cols = st.columns([1.5] + [1.0] * NUM_MONTHS)
        pay_hdr_cols[0].markdown("**Payday**")
        for j, lbl in enumerate(month_labels):
            pay_hdr_cols[j + 1].markdown(f"**{lbl}**")
        pay_row_cols = st.columns([1.5] + [1.0] * NUM_MONTHS)
        pay_row_cols[0].markdown("Checks")
        for j in range(NUM_MONTHS):
            date_key = months[j]["date"]
            pay_dates = paydays_per_month.get(date_key, [])
            expected = len(pay_dates)
            checks_list = st.session_state.checks_received[date_key]
            with pay_row_cols[j + 1]:
                for ci in range(expected):
                    lbl = pay_dates[ci].strftime("%m/%d") if ci < len(pay_dates) else f"#{ci+1}"
                    checks_list[ci] = st.checkbox(
                        lbl, value=checks_list[ci], key=f"chk_{date_key}_{ci}",
                    )
                received = sum(1 for x in checks_list if x)
                color = "#2ecc71" if received == expected else ("#f39c12" if received > 0 else "#888")
                st.markdown(
                    f'<span style="color:{color};font-size:0.85em">{received}/{expected} received</span>',
                    unsafe_allow_html=True,
                )
                net_this = received * net_per_check if received > 0 else expected * net_per_check
                st.caption(f"\\${net_this:,.0f}")
    else:
        st.info("⚙️ Configure your paycheck settings in **Retirement & Paycheck** to auto-calculate Net Pay.")
    st.markdown("---")
    label_col_width = 1.5
    month_col_width = 1.0
    st.caption("Budget edits stage immediately. Use the sidebar Apply Changes button to recalculate the full app.")
    with st.container():
        # ── INCOME ──
        section_header("INCOME")
        header_cols = st.columns([label_col_width] + [month_col_width] * NUM_MONTHS)
        header_cols[0].markdown("**Category**")
        for j, lbl in enumerate(month_labels):
            header_cols[j + 1].markdown(f"**{lbl}**")
        # Net Pay — display-only, computed from paychecks received
        if net_per_check > 0:
            np_cols = st.columns([label_col_width] + [month_col_width] * NUM_MONTHS)
            np_cols[0].markdown(ROW_LABELS["net_pay"])
            for j in range(NUM_MONTHS):
                np_cols[j + 1].markdown(f"${months[j]['net_pay']:,.0f}")
        income_vals = {}
        for field in INCOME_FIELDS:
            if field == "net_pay" and net_per_check > 0:
                # Skip editable input — it's shown as display above
                income_vals[field] = [months[j]["net_pay"] for j in range(NUM_MONTHS)]
                continue
            cols = st.columns([label_col_width] + [month_col_width] * NUM_MONTHS)
            cols[0].markdown(ROW_LABELS.get(field, field))
            income_vals[field] = []
            for j in range(NUM_MONTHS):
                v = cols[j + 1].number_input(
                    f"{field}_{j}", value=float(months[j][field]),
                    step=50.0, key=f"g_{field}_{j}", label_visibility="collapsed",
                )
                income_vals[field].append(v)
        # ── EXPENSES ──
        section_header("EXPENSES")
        expense_vals = {}
        for field in EXPENSE_FIELDS + ["one_time_expense"]:
            cols = st.columns([label_col_width] + [month_col_width] * NUM_MONTHS)
            cols[0].markdown(ROW_LABELS.get(field, field))
            expense_vals[field] = []
            for j in range(NUM_MONTHS):
                v = cols[j + 1].number_input(
                    f"{field}_{j}", value=float(months[j].get(field, 0.0)),
                    step=50.0, key=f"g_{field}_{j}", label_visibility="collapsed",
                )
                expense_vals[field].append(v)
        # ── INVESTMENTS ──
        section_header("INVESTMENTS & SAVINGS")
        invest_vals = {}
        for field in INVEST_FIELDS:
            cols = st.columns([label_col_width] + [month_col_width] * NUM_MONTHS)
            cols[0].markdown(ROW_LABELS.get(field, field))
            invest_vals[field] = []
            for j in range(NUM_MONTHS):
                v = cols[j + 1].number_input(
                    f"{field}_{j}", value=float(months[j][field]),
                    step=50.0, key=f"g_{field}_{j}", label_visibility="collapsed",
                )
                invest_vals[field].append(v)
    for j in range(NUM_MONTHS):
        for field in INCOME_FIELDS:
            months[j][field] = income_vals[field][j]
        for field in EXPENSE_FIELDS + ["one_time_expense"]:
            months[j][field] = expense_vals[field][j]
        for field in INVEST_FIELDS:
            months[j][field] = invest_vals[field][j]
    # ── Car Payment Paid Toggles (outside form) ─────────────────────────────
    section_header("CAR PAYMENT — MARK PAID")
    st.caption("Toggle months where you've already made the car payment. "
               "Paid months won't reduce the loan balance again in the summary.")
    toggle_cols = st.columns([label_col_width] + [month_col_width] * NUM_MONTHS)
    toggle_cols[0].markdown("**Paid?**")
    for j in range(NUM_MONTHS):
        key = months[j]["date"]
        current = st.session_state.car_paid_toggles.get(key, False)
        st.session_state.car_paid_toggles[key] = toggle_cols[j + 1].checkbox(
            month_labels[j], value=current, key=f"carpaid_{j}", label_visibility="collapsed",
        )
    # ── Summary ─────────────────────────────────────────────────────────────
    section_header("SUMMARY")
    # Total Income
    cols = st.columns([label_col_width] + [month_col_width] * NUM_MONTHS)
    cols[0].markdown("**Total Income**")
    for j in range(NUM_MONTHS):
        ti = sum(months[j][f] for f in INCOME_FIELDS)
        cols[j + 1].markdown(f"**${ti:,.0f}**")
    # Total Expenses
    cols = st.columns([label_col_width] + [month_col_width] * NUM_MONTHS)
    cols[0].markdown("**Total Expenses**")
    for j in range(NUM_MONTHS):
        te = sum(months[j][f] for f in EXPENSE_FIELDS) + months[j].get("one_time_expense", 0.0)
        cols[j + 1].markdown(f"**${te:,.0f}**")
    # Total Invested
    cols = st.columns([label_col_width] + [month_col_width] * NUM_MONTHS)
    cols[0].markdown("**Total Invested**")
    for j in range(NUM_MONTHS):
        tv = sum(months[j][f] for f in INVEST_FIELDS)
        cols[j + 1].markdown(f"**${tv:,.0f}**")
    # Money Left
    cols = st.columns([label_col_width] + [month_col_width] * NUM_MONTHS)
    cols[0].markdown("**Money Left**")
    for j in range(NUM_MONTHS):
        ti = sum(months[j][f] for f in INCOME_FIELDS)
        te = sum(months[j][f] for f in EXPENSE_FIELDS) + months[j].get("one_time_expense", 0.0)
        tv = sum(months[j][f] for f in INVEST_FIELDS)
        left = ti - te - tv
        color = "#2ecc71" if left >= 0 else "#e74c3c"
        cols[j + 1].markdown(
            f'<span style="color:{color};font-weight:700">${left:,.0f}</span>',
            unsafe_allow_html=True,
        )
    # Running total
    cols = st.columns([label_col_width] + [month_col_width] * NUM_MONTHS)
    cols[0].markdown("**Running Total**")
    running = 0.0
    for j in range(NUM_MONTHS):
        ti = sum(months[j][f] for f in INCOME_FIELDS)
        te = sum(months[j][f] for f in EXPENSE_FIELDS) + months[j].get("one_time_expense", 0.0)
        tv = sum(months[j][f] for f in INVEST_FIELDS)
        running += ti - te - tv
        cols[j + 1].markdown(f"**${running:,.0f}**")
    # Car Loan Remaining (with paid toggles)
    cols = st.columns([label_col_width] + [month_col_width] * NUM_MONTHS)
    cols[0].markdown("**Car Loan**")
    car_bal = st.session_state.car_loan_balance
    for j in range(NUM_MONTHS):
        date_key = months[j]["date"]
        paid_already = st.session_state.car_paid_toggles.get(date_key, False)
        if not paid_already:
            car_bal = max(0, car_bal - months[j].get("car_payment", 0.0))
        cols[j + 1].markdown(f"${car_bal:,.0f}")
    # Credit Card Balance
    cols = st.columns([label_col_width] + [month_col_width] * NUM_MONTHS)
    cols[0].markdown("**Credit Card Bal**")
    cc_bal = st.session_state.get("credit_card_balance", 0.0)
    for j in range(NUM_MONTHS):
        cc_bal = max(0, cc_bal - months[j].get("credit_card", 0.0))
        cols[j + 1].markdown(f"${cc_bal:,.0f}")
    # Metrics
    st.markdown("---")
    all_left = []
    total_inv = 0.0
    for m in months:
        ti = sum(m[f] for f in INCOME_FIELDS)
        te = sum(m[f] for f in EXPENSE_FIELDS) + m.get("one_time_expense", 0.0)
        tv = sum(m[f] for f in INVEST_FIELDS)
        all_left.append(ti - te - tv)
        total_inv += tv
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Avg Monthly Left", f"${sum(all_left)/max(len(all_left),1):,.0f}")
    c2.metric("Total Invested", f"${total_inv:,.0f}")
    c3.metric("12-Mo Running", f"${sum(all_left):,.0f}")
    c4.metric("Car Loan at End", f"${car_bal:,.0f}")
    c5.metric("CC at End", f"${cc_bal:,.0f}")
    st.markdown("---")
    bs1, bs2 = st.columns(2)
    if bs1.button("💾 Save Budget", key="save_budget_btn"):
        save_budget()
        st.success("Budget saved!")
    if bs2.button("📂 Load Budget", key="load_budget_btn"):
        load_budget()
        st.success("Budget loaded!")
        st.rerun()
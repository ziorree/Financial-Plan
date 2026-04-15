"""Shared constants, helpers, persistence, and tax functions used across all tabs."""
import streamlit as st
import json
from pathlib import Path
from datetime import datetime, timedelta
# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
BUDGET_FILE    = BASE_DIR / "save_budget.json"
PROJECTION_FILE = BASE_DIR / "save_projection.json"
DIVIDEND_FILE  = BASE_DIR / "save_dividends.json"
RETIREMENT_FILE = BASE_DIR / "retirement_settings.json"
CAR_LOAN_FILE  = BASE_DIR / "car_loan_balance.json"
CREDIT_CARD_BAL_FILE = BASE_DIR / "credit_card_balance.json"
LAST_SAVED_FILE = BASE_DIR / "last_saved.json"
# ── Ticker classifications ─────────────────────────────────────────────────────
MONEY_MARKET_TICKERS = {"SWVXX", "SWTXX", "SWPPX"}
MUTUAL_FUND_TICKERS  = {"SWOBX", "SWPRX", "BPTRX", "SWPPX"}
KNOWN_YIELDS = {
    "QQQI": 0.14, "IAUI": 0.1263, "IYRI": 0.1117, "SPYI": 0.1117,
    "MLPI": 0.08, "WPAY": 0.06, "BINC": 0.055, "CGDV": 0.02,
    "OUNZ": 0.0, "VTI": 0.013, "SWVXX": 0.0425, "SWOBX": 0.02,
    "BPTRX": 0.0,
}
# Holdings that are known to pay return-of-capital (NAV erosion applies)
# Annual NAV erosion rate: e.g. 0.02 = price declines ~2%/yr on top of normal movement
KNOWN_ROC_TICKERS = {
    "QQQI": 0.03, "IAUI": 0.03, "IYRI": 0.03, "SPYI": 0.03,
    "MLPI": 0.02,
}
# ── Budget field definitions ───────────────────────────────────────────────────
EXPENSE_FIELDS = ["car_insurance_gym", "food", "gas", "car_payment", "credit_card"]
INVEST_FIELDS  = ["brokerage_main", "btc", "savings", "income_brokerage", "roth_ira"]
INCOME_FIELDS  = ["net_pay", "bonus", "other_income"]
ONETIME_FIELD  = "one_time_expense"
ALL_BUDGET_FIELDS = INCOME_FIELDS + EXPENSE_FIELDS + ["one_time_expense"] + INVEST_FIELDS
NUM_MONTHS = 12
ROW_LABELS = {
    "net_pay": "Net Pay", "bonus": "Bonus", "other_income": "Other Income",
    "car_insurance_gym": "Ins/Gym", "food": "Food",
    "gas": "Gas", "car_payment": "Car Payment", "credit_card": "Credit Card",
    "one_time_expense": "One-Time Expense",
    "brokerage_main": "Invest: Brokerage", "btc": "Invest: BTC",
    "savings": "Invest: Savings", "income_brokerage": "Invest: Income Brkrg",
    "roth_ira": "Invest: Roth IRA",
}
INVEST_TO_PORTFOLIO = {
    "brokerage_main": "Main",
    "savings": "Savings",
    "income_brokerage": "Income",
    "roth_ira": "Roth IRA",
}
# ── Tax Calculator ─────────────────────────────────────────────────────────────
FED_BRACKETS = [
    (11600, 0.10), (47150, 0.12), (100525, 0.22), (191950, 0.24),
    (243725, 0.32), (609350, 0.35), (float("inf"), 0.37),
]
FED_STANDARD_DEDUCTION = 15700
CO_STATE_TAX_RATE = 0.044
def calc_federal_tax(taxable_income):
    tax = 0.0
    prev = 0
    for bracket_top, rate in FED_BRACKETS:
        if taxable_income <= 0:
            break
        span = min(taxable_income, bracket_top - prev)
        tax += span * rate
        taxable_income -= span
        prev = bracket_top
    return tax
def calc_annual_taxes(gross_annual, state, k401_annual):
    ss = min(gross_annual, 168600) * 0.062
    medicare = gross_annual * 0.0145
    fica = ss + medicare
    taxable = max(0, gross_annual - k401_annual - FED_STANDARD_DEDUCTION)
    fed = calc_federal_tax(taxable)
    state_tax = 0.0
    if state == "Colorado":
        state_tax = max(0, gross_annual - k401_annual - FED_STANDARD_DEDUCTION) * CO_STATE_TAX_RATE
    return fed, state_tax, fica
# ── Save / Load helpers ────────────────────────────────────────────────────────
def save_budget():
    data = {
        "months": st.session_state.months,
        "car_paid_toggles": st.session_state.get("car_paid_toggles", {}),
        "checks_received": st.session_state.get("checks_received", {}),
    }
    BUDGET_FILE.write_text(json.dumps(data, indent=2, default=str))
    CAR_LOAN_FILE.write_text(json.dumps({"balance": st.session_state.car_loan_balance}))
    CREDIT_CARD_BAL_FILE.write_text(json.dumps({"balance": st.session_state.get("credit_card_balance", 0.0)}))
    _write_last_saved()
def load_budget():
    if BUDGET_FILE.exists():
        data = json.loads(BUDGET_FILE.read_text())
        st.session_state.months = data["months"]
        if "car_paid_toggles" in data:
            st.session_state.car_paid_toggles = data["car_paid_toggles"]
        if "checks_received" in data:
            st.session_state.checks_received = data["checks_received"]
    if CAR_LOAN_FILE.exists():
        st.session_state.car_loan_balance = json.loads(CAR_LOAN_FILE.read_text()).get(
            "balance", st.session_state.car_loan_balance
        )
    if CREDIT_CARD_BAL_FILE.exists():
        st.session_state.credit_card_balance = json.loads(CREDIT_CARD_BAL_FILE.read_text()).get(
            "balance", st.session_state.get("credit_card_balance", 0.0)
        )
def save_projection():
    data = {
        "portfolio_allocations": st.session_state.portfolio_allocations,
        "share_alloc_pcts": st.session_state.get("share_alloc_pcts", {}),
    }
    PROJECTION_FILE.write_text(json.dumps(data, indent=2, default=str))
    _write_last_saved()
def load_projection():
    if PROJECTION_FILE.exists():
        data = json.loads(PROJECTION_FILE.read_text())
        if "portfolio_allocations" in data:
            st.session_state.portfolio_allocations = data["portfolio_allocations"]
        if "share_alloc_pcts" in data:
            st.session_state.share_alloc_pcts = data["share_alloc_pcts"]
        elif "share_alloc_tickers" in data:
            st.session_state.share_alloc_pcts = {
                a: {t: 100.0} for a, t in data["share_alloc_tickers"].items()
            }
def save_dividends():
    data = {"div_holdings": {k: dict(v) for k, v in st.session_state.div_holdings.items()}}
    DIVIDEND_FILE.write_text(json.dumps(data, indent=2, default=str))
def load_dividends():
    if DIVIDEND_FILE.exists():
        data = json.loads(DIVIDEND_FILE.read_text())
        st.session_state.div_holdings = data.get("div_holdings", st.session_state.div_holdings)
def save_retirement():
    RETIREMENT_FILE.write_text(json.dumps(st.session_state.retirement, indent=2))
def load_retirement():
    if RETIREMENT_FILE.exists():
        st.session_state.retirement.update(json.loads(RETIREMENT_FILE.read_text()))
def _write_last_saved():
    LAST_SAVED_FILE.write_text(json.dumps({"ts": datetime.now().strftime("%Y-%m-%d %I:%M %p")}))
def save_all():
    save_budget()
    save_projection()
    save_dividends()
    save_retirement()
    _write_last_saved()
def load_all():
    load_budget()
    load_projection()
    load_dividends()
    load_retirement()

def compute_paycheck_schedule(ret):
    """Returns (net_per_check, {date_key: [payday_date, ...]}, {date_key: total_net})"""
    if not ret.get("hourly_rate"):
        return 0.0, {}, {}
    gross_annual = ret["hourly_rate"] * ret.get("hours_per_year", 2080)
    freq = ret.get("pay_frequency", "Biweekly")
    checks = {"Biweekly": 26, "Semi-Monthly": 24, "Monthly": 12}.get(freq, 26)
    gross_pc = gross_annual / checks
    k401_pct = ret.get("k401_contribution_pct", 5.0) / 100.0
    k401_pc = gross_pc * k401_pct
    k401_annual = gross_annual * k401_pct
    benefits = ret.get("benefits_per_check", 0)
    fed, state_tax, fica = calc_annual_taxes(gross_annual, ret.get("state", "Florida"), k401_annual)
    net_pc = gross_pc - k401_pc - benefits - fed / checks - state_tax / checks - fica / checks
    next_pd = ret.get("next_payday", "2026-04-24")
    try:
        start = datetime.strptime(next_pd, "%Y-%m-%d").date()
    except Exception:
        return 0.0, {}, {}
    delta = timedelta(days=14) if freq == "Biweekly" else timedelta(days=15)
    paydays_per_month = {}
    current = start
    end = start + timedelta(days=400)
    while current <= end:
        key = current.strftime("%Y-%m")
        paydays_per_month.setdefault(key, []).append(current)
        current += delta
    totals = {k: round(len(v) * net_pc, 2) for k, v in paydays_per_month.items()}
    return round(net_pc, 2), paydays_per_month, totals

def compute_month_totals(month):
    """Compute summary totals for a single month dict."""
    income_total = sum(float(month.get(f, 0.0)) for f in INCOME_FIELDS)
    expense_total = sum(float(month.get(f, 0.0)) for f in EXPENSE_FIELDS) + float(month.get("one_time_expense", 0.0))
    invested_total = sum(float(month.get(f, 0.0)) for f in INVEST_FIELDS)
    money_left = income_total - expense_total - invested_total
    return {
        "income_total": income_total,
        "expense_total": expense_total,
        "invested_total": invested_total,
        "money_left": money_left,
    }

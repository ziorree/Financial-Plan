"""Upload Positions tab."""
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import tempfile
from tabs.shared import MONEY_MARKET_TICKERS


def _format_position_table(df, cols):
    disp = df[cols].copy() if cols else df.copy()
    if "Qty" in disp.columns:
        disp["Qty"] = disp["Qty"].apply(lambda v: f"{float(v):,.4f}" if pd.notna(v) else "-")
    if "Mark" in disp.columns:
        disp["Mark"] = disp["Mark"].apply(lambda v: f"${float(v):,.2f}" if pd.notna(v) else "-")
    if "Net Liq" in disp.columns:
        disp["Net Liq"] = disp["Net Liq"].apply(lambda v: f"${float(v):,.2f}" if pd.notna(v) else "-")
    if "P/L Open" in disp.columns:
        disp["P/L Open"] = disp["P/L Open"].apply(lambda v: f"${float(v):,.2f}" if pd.notna(v) else "-")
    return disp


def render(parse_position_csv, build_holdings_from_positions, load_latest_positions,
           eq_df_loaded, ot_df_loaded, position_dir):
    st.title("Upload Position Statement")
    st.caption("Upload a Schwab Position Statement CSV. All tabs refresh instantly with new data.")
    uploaded = st.file_uploader("Choose a Position Statement CSV", type=["csv"])
    if uploaded:
        content = uploaded.read().decode("utf-8-sig")
        tmp = Path(tempfile.gettempdir()) / "pos_upload.csv"
        tmp.write_text(content, encoding="utf-8-sig")
        up_eq, up_ot, up_cash, _ = parse_position_csv(tmp)
        if not up_eq.empty:
            st.subheader("Equities")
            dcols = [c for c in ["Instrument", "Qty", "Mark", "Net Liq", "Account Name", "P/L Open"]
                     if c in up_eq.columns]
            st.dataframe(_format_position_table(up_eq, dcols), use_container_width=True)
        if not up_ot.empty:
            st.subheader("Other Holdings")
            dcols = [c for c in ["Instrument", "Qty", "Mark", "Net Liq", "Account Name"]
                     if c in up_ot.columns]
            st.dataframe(_format_position_table(up_ot, dcols), use_container_width=True)
        total_eq = up_eq["Net Liq"].sum() if "Net Liq" in up_eq.columns else 0
        total_ot = up_ot["Net Liq"].sum() if "Net Liq" in up_ot.columns else 0
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Total Equities", f"${total_eq:,.2f}")
        mc2.metric("Total Others", f"${total_ot:,.2f}")
        mc3.metric("Cash", f"${up_cash:,.2f}")
        st.markdown("---")
        save_name = st.text_input(
            "Save filename",
            value=f"{datetime.now().strftime('%Y-%m-%d')}-PositionStatement",
        )
        if st.button("💾 Save & Apply CSV", type="primary"):
            position_dir.mkdir(parents=True, exist_ok=True)
            save_path = position_dir / f"{save_name}.csv"
            save_path.write_text(content, encoding="utf-8-sig")
            # ── Update all session-state holdings so every tab refreshes ────
            new_hba, new_ah, new_cash = build_holdings_from_positions(up_eq, up_ot, up_cash)
            st.session_state.holdings_by_account = new_hba
            st.session_state.all_holdings = new_ah
            st.session_state.cash_balance = new_cash
            # Update dividend holdings
            new_div = {}
            for key, h in new_ah.items():
                if h["yield_pct"] > 0 and h["shares"] > 0:
                    new_div[key] = {
                        "ticker": h["ticker"], "shares": h["shares"], "price": h["price"],
                        "yield_pct": h["yield_pct"], "account": h["account"],
                    }
            st.session_state.div_holdings = new_div
            # Merge new accounts/tickers into share_alloc_pcts (preserve existing)
            if "share_alloc_pcts" not in st.session_state:
                st.session_state.share_alloc_pcts = {}
            for acct, holdings in new_hba.items():
                if acct not in st.session_state.share_alloc_pcts:
                    non_mm = [h["ticker"] for h in holdings if h["ticker"] not in MONEY_MARKET_TICKERS]
                    if non_mm:
                        st.session_state.share_alloc_pcts[acct] = {non_mm[0]: 100.0}
                    elif holdings:
                        st.session_state.share_alloc_pcts[acct] = {holdings[0]["ticker"]: 100.0}
                    else:
                        st.session_state.share_alloc_pcts[acct] = {}
                else:
                    for h in holdings:
                        t = h["ticker"]
                        if t not in st.session_state.share_alloc_pcts[acct]:
                            st.session_state.share_alloc_pcts[acct][t] = 0.0
            load_latest_positions.clear()
            st.success(f"Saved {save_path.name} — refreshing all tabs...")
            st.rerun()
    else:
        st.info(f"Currently loaded: latest position file from **{position_dir}**")
        if not eq_df_loaded.empty:
            st.subheader("Current Equities")
            dcols = [c for c in ["Instrument", "Qty", "Mark", "Net Liq", "Account Name"]
                     if c in eq_df_loaded.columns]
            st.dataframe(_format_position_table(eq_df_loaded, dcols), use_container_width=True)
        if not ot_df_loaded.empty:
            st.subheader("Current Other Holdings")
            dcols = [c for c in ["Instrument", "Qty", "Mark", "Net Liq", "Account Name"]
                     if c in ot_df_loaded.columns]
            st.dataframe(_format_position_table(ot_df_loaded, dcols), use_container_width=True)
        if eq_df_loaded.empty and ot_df_loaded.empty:
            st.warning("No position file found. Upload a Schwab CSV to get started.")

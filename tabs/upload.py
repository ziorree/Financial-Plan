"""Upload Positions tab."""
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import tempfile
def render(parse_position_csv, build_holdings_from_positions, load_latest_positions,
           eq_df_loaded, ot_df_loaded, position_dir):
    st.title("Upload Position Statement")
    st.caption("Upload a Schwab Position Statement CSV to update all holdings dynamically.")
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
            st.dataframe(up_eq[dcols] if dcols else up_eq, use_container_width=True)
        if not up_ot.empty:
            st.subheader("Other Holdings")
            dcols = [c for c in ["Instrument", "Qty", "Mark", "Net Liq", "Account Name"]
                     if c in up_ot.columns]
            st.dataframe(up_ot[dcols] if dcols else up_ot, use_container_width=True)
        total_eq = up_eq["Net Liq"].sum() if "Net Liq" in up_eq.columns else 0
        total_ot = up_ot["Net Liq"].sum() if "Net Liq" in up_ot.columns else 0
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Total Equities", f"${total_eq:,.2f}")
        mc2.metric("Total Others", f"${total_ot:,.2f}")
        mc3.metric("Cash", f"${up_cash:,.2f}")
        st.markdown("---")
        if st.button("Sync Dividend Holdings from Upload"):
            _, new_all, _ = build_holdings_from_positions(up_eq, up_ot, up_cash)
            new_div = {}
            for key, h in new_all.items():
                if h["yield_pct"] > 0 and h["shares"] > 0:
                    new_div[key] = {
                        "ticker": h["ticker"], "shares": h["shares"], "price": h["price"],
                        "yield_pct": h["yield_pct"], "account": h["account"],
                    }
            st.session_state.div_holdings = new_div
            st.success(f"Updated {len(new_div)} dividend holdings!")
        st.markdown("---")
        save_name = st.text_input(
            "Save filename",
            value=f"{datetime.now().strftime('%Y-%m-%d')}-PositionStatement",
        )
        if st.button("Save CSV"):
            save_path = position_dir / f"{save_name}.csv"
            save_path.write_text(content, encoding="utf-8-sig")
            st.success(f"Saved to {save_path.name}")
            load_latest_positions.clear()
    else:
        st.info(f"Currently loaded: latest position file from {position_dir}")
        if not eq_df_loaded.empty:
            st.subheader("Current Equities")
            dcols = [c for c in ["Instrument", "Qty", "Mark", "Net Liq", "Account Name"]
                     if c in eq_df_loaded.columns]
            st.dataframe(eq_df_loaded[dcols] if dcols else eq_df_loaded, use_container_width=True)
        if not ot_df_loaded.empty:
            st.subheader("Current Other Holdings")
            dcols = [c for c in ["Instrument", "Qty", "Mark", "Net Liq", "Account Name"]
                     if c in ot_df_loaded.columns]
            st.dataframe(ot_df_loaded[dcols] if dcols else ot_df_loaded, use_container_width=True)

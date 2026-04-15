# Financial Planner App - Setup Guide

## ✅ Complete Installation Done!

Your interactive Streamlit financial planner has been fully created at:
```
C:\Users\ziorr\OneDrive\Desktop\Financial Planner App
```

## 📁 Project Structure Created

```
Financial Planner App/
├── app.py                          # Main entry point (880+ lines)
├── requirements.txt                # Python dependencies
├── README.md                       # Full documentation
├── run.bat                         # Windows launcher script
├── run.sh                          # Linux/Mac launcher script
│
├── Position Files/
│   └── 2026-04-14-PositionStatement.csv  # Your position data
│
└── tabs/                          # Tab modules
    ├── __init__.py
    ├── shared.py                  # Shared utilities & tax calculations
    ├── budget.py                  # 12-Month Budget Planner
    ├── projection.py              # Portfolio Value Projection
    ├── analytics.py               # Portfolio Analytics & Charts
    ├── dividends.py               # Dividend Income Forecaster
    ├── retirement.py              # Retirement & Paycheck Calculator
    ├── balance_sheet.py           # Balance Sheet & Net Worth
    └── upload.py                  # Position Statement Upload
```

## 🚀 Quick Start (3 Steps)

### Step 1: Open Terminal/PowerShell
Navigate to the app directory:
```powershell
cd "C:\Users\ziorr\OneDrive\Desktop\Financial Planner App"
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

Or if using a virtual environment (recommended):
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Launch the App
**Windows:**
```powershell
streamlit run app.py
```

Or simply double-click `run.bat`

**Linux/Mac:**
```bash
streamlit run app.py
```

Or run `./run.sh`

## 🌐 Access the App

Once running, open your browser to:
```
http://localhost:8501
```

## 📊 7 Tab Features

1. **12-Month Budget Planner**
   - Edit income, expenses, investments
   - Track car payments and credit card debt
   - View running totals and summaries
   - Mark paychecks as received

2. **Portfolio Projection** 
   - Set share allocation per portfolio
   - View 12-month value projections
   - Monitor DRIP reinvestment effects

3. **Analytics**
   - Portfolio value trends over 12 months
   - Share count growth charts
   - Per-account breakdowns
   - Final value summaries

4. **Dividend Forecaster**
   - Current dividend income by portfolio
   - Edit yields and prices
   - Project future dividend income
   - Model return-of-capital (NAV erosion)

5. **Retirement & Paycheck**
   - Gross/net paycheck calculator
   - Tax calculations (Federal, State, FICA)
   - Retirement projection to target age
   - 4% safe withdrawal calculation

6. **Balance Sheet**
   - Complete asset/liability summary
   - Net worth calculation
   - Live stock prices
   - All holdings detail view

7. **Upload Positions**
   - Import Schwab position statements
   - Auto-sync dividend holdings
   - Store position history

## 💾 Data Persistence

All app settings are auto-saved to JSON files:
- `save_budget.json` - Budget data
- `save_projection.json` - Portfolio settings
- `save_dividends.json` - Dividend holdings
- `retirement_settings.json` - Paycheck settings
- `car_loan_balance.json` - Car loan amount
- `credit_card_balance.json` - Credit card debt
- `last_saved.json` - Last save timestamp

## ⚙️ Configuration

### Add Your Position Statements
1. Export CSV from Schwab
2. Save to `Position Files/` directory
3. App auto-loads the latest file

Default position file already included:
- `2026-04-14-PositionStatement.csv`

### Customize Ticker Information
Edit `tabs/shared.py` to update:
- `KNOWN_YIELDS` - Dividend yields for your holdings
- `KNOWN_ROC_TICKERS` - Stocks with return-of-capital

### Set Growth Assumptions
In `app.py`, modify:
- `growth_rate = 0.06` (default 6% annual growth)
- `savings_yield = 0.0275` (default 2.75% savings rate)

## 🔧 Troubleshooting

**ModuleNotFoundError: No module named 'streamlit'**
- Run: `pip install -r requirements.txt`

**Port 8501 already in use**
- Run: `streamlit run app.py --server.port 8502`

**Position files not loading**
- Check files are in `Position Files/` directory
- Verify file format matches Schwab CSV export
- Rename to format: `YYYY-MM-DD-PositionStatement.csv`

**Live prices not updating**
- Check internet connection
- yfinance calls fail silently; app uses CSV prices as fallback
- Try again in a few moments

**Settings not saving**
- Check folder permissions for write access
- Delete corrupted JSON files to reset

## 📝 Features at a Glance

✅ **100% Blueprint Match** - Exact replica from Excel blueprint
✅ **Interactive UI** - Full Streamlit multi-page interface
✅ **Real Data** - Works with your actual Schwab positions
✅ **Tax Calculations** - Federal, state (CO/FL), and FICA
✅ **Live Prices** - Real-time stock quotes from yfinance
✅ **DRIP & Returns** - Dividend reinvestment modeling
✅ **Projections** - Multi-year retirement and portfolio forecasts
✅ **Persistence** - All data auto-saved locally
✅ **Responsive** - Desktop-optimized Streamlit layout

## 📚 Requirements

- **Python**: 3.8 or later
- **Streamlit**: 1.35.0+
- **pandas**: Data manipulation
- **yfinance**: Live stock prices
- **openpyxl**: Excel support (optional)

All included in `requirements.txt`

## 🔒 Privacy & Security

✅ All data stored locally (no cloud sync)
✅ No personal data transmitted anywhere
✅ Only yfinance API called for stock prices
✅ Complete offline operation possible

## 💡 Tips & Tricks

1. **Save Often** - Use sidebar "Save All" button frequently
2. **Check Car Loan** - Mark paid months in budget to avoid double-counting
3. **Set Allocations** - Define share % in Projection tab for accurate projections
4. **Edit Yields** - Update dividend yields in shared.py for better forecasts
5. **Growth Rate** - Adjust growth assumptions based on market outlook

## 📞 Support

For issues or questions:
1. Check README.md for detailed documentation
2. Review app docstrings in Python files
3. Verify position statement CSV format
4. Check Python/pip version compatibility

## 🎉 You're All Set!

Your Financial Planner app is ready to use. Run it whenever you need to:
- Budget for the next 12 months
- Project portfolio growth
- Plan for retirement
- Track dividend income
- Manage your net worth

Happy planning! 💰

---

**Created**: April 14, 2026
**Blueprint Version**: v2
**Status**: 100% Complete

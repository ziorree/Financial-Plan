# Financial Planner App

An interactive Streamlit-based personal finance management tool with budget planning, portfolio projection, dividend forecasting, and retirement calculations.

## Features

- **12-Month Budget Planner**: Track income, expenses, and investments across 12 months
- **Portfolio Projection**: Simulate portfolio growth with monthly contributions and DRIP reinvestment
- **Portfolio Analytics**: Interactive charts showing portfolio value, share counts, and account breakdowns
- **Dividend Forecaster**: Calculate current and projected dividend income with NAV erosion modeling
- **Retirement Calculator**: Project retirement savings with paycheck calculator and tax estimation
- **Balance Sheet**: View all assets, liabilities, and net worth with real-time pricing
- **Position Upload**: Import Schwab position statements to automatically update holdings

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Add Your Position Statement

Place your position statement CSV files in the `Position Files` directory. The app will automatically load the latest file.

Example position files:
- `2026-04-14-PositionStatement.csv`

### 3. Run the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Project Structure

```
Financial Planner App/
├── app.py                 # Main entry point
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── Position Files/        # Store position statement CSVs here
└── tabs/
    ├── __init__.py
    ├── shared.py         # Shared constants, tax calculations, persistence
    ├── budget.py         # 12-Month Budget tab
    ├── projection.py     # Portfolio Projection tab
    ├── analytics.py      # Analytics & Charts tab
    ├── dividends.py      # Dividend Forecaster tab
    ├── retirement.py     # Retirement & Paycheck tab
    ├── balance_sheet.py  # Balance Sheet tab
    └── upload.py         # Upload Positions tab
```

## Usage Guide

### Budget Tab
- Edit your monthly income, expenses, and investments
- Toggle car payments and paycheck receipts
- View running totals and summaries

### Projection Tab
- Set share allocation percentages for each portfolio
- View 12-month value projections
- Monitor portfolio growth with contributions

### Analytics Tab
- See portfolio value trends
- Track share count growth from contributions and DRIP
- View per-account breakdowns

### Dividend Forecaster
- Edit dividend yields and prices
- Project future dividend income
- Model return-of-capital (ROC) tax erosion

### Retirement/Paycheck
- Calculate gross/net pay with tax breaks for your state
- Set 401k contribution percentages
- Project retirement nest egg to target age

### Balance Sheet
- View complete asset/liability summary
- See net worth calculation
- Get live prices for all holdings

### Upload Positions
- Upload new Schwab position statements
- Auto-sync dividend holdings
- Store position history

## Data Persistence

The app saves all changes to JSON files in the main directory:
- `save_budget.json` - Budget data
- `save_projection.json` - Portfolio allocation settings
- `save_dividends.json` - Dividend holdings
- `retirement_settings.json` - Retirement/paycheck settings
- `car_loan_balance.json` - Current car loan amount
- `credit_card_balance.json` - Current credit card debt

## Configuration

### Tax Settings
- Federal tax brackets and standard deduction are hardcoded for 2024
- Colorado state tax available (4.4%)
- Florida has no state income tax
- FICA calculations include Social Security and Medicare

### Yield Rates
Edit `KNOWN_YIELDS` in `tabs/shared.py` to update dividend yield estimates for your holdings.

### Return-of-Capital Tickers
Edit `KNOWN_ROC_TICKERS` for stocks with NAV erosion from return-of-capital distributions.

### Growth Assumptions
Edit the growth_rate in the app config to change portfolio growth assumptions (default: 6% annually).

## Requirements

- Python 3.8+
- Streamlit 1.35.0+
- pandas, numpy, scipy
- yfinance for live stock prices
- openpyxl for Excel support

## Excel File Support (Optional)

If you have a `Main Financial Plan.xlsx` in the app directory, it will auto-load default budget values from:
- Sheet "Main": Net pay, expense, and investment defaults
- Sheet "Savings (Shared)": Savings yield rate

## Troubleshooting

**"No position files found"**
- Ensure CSV files are in the `Position Files` directory
- Rename files to match the expected format: `YYYY-MM-DD-PositionStatement.csv`

**"yfinance timeout"**
- Live prices fail silently; app falls back to CSV prices
- Check your internet connection
- Try again in a moment

**"JSON decode error"**
- Delete corrupted JSON save files to reset
- Files affected: `save_*.json`, `*_settings.json`, etc.

## Privacy & Security

All data is saved locally. No data is sent anywhere except:
- yfinance API for stock prices
- OS system resources

## License

Personal use - modify as needed for your finances

---

Built with ❤️ using Streamlit

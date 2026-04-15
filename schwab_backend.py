"""Backend-only Schwab OAuth and accounts positions utilities.

This module is intentionally not rendered in Streamlit UI.
Use these functions from background scripts or scheduled jobs.
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import quote
import base64
import json
import requests

DEFAULT_AUTH_BASE = "https://api.schwabapi.com/v1/oauth/authorize"
DEFAULT_TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"
DEFAULT_REDIRECT_URI = "https://developer.schwab.com/oauth2-redirect.html"
DEFAULT_SCOPE = "readonly"
DEFAULT_POSITIONS_URL = "https://api.schwabapi.com/trader/v1/accounts?fields=positions"


def build_auth_url(client_id: str, scope: str = DEFAULT_SCOPE, redirect_uri: str = DEFAULT_REDIRECT_URI) -> str:
    return (
        f"{DEFAULT_AUTH_BASE}?response_type=code"
        f"&client_id={quote(client_id)}"
        f"&scope={quote(scope)}"
        f"&redirect_uri={quote(redirect_uri, safe=':/?=&')}"
    )


def exchange_code_for_tokens(client_id: str, client_secret: str, code: str, redirect_uri: str = DEFAULT_REDIRECT_URI) -> dict:
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
    resp = requests.post(
        DEFAULT_TOKEN_URL,
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        },
        timeout=25,
    )
    resp.raise_for_status()
    token_data = resp.json()
    token_data["obtained_at"] = datetime.now(timezone.utc).isoformat()
    return token_data


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> dict:
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
    resp = requests.post(
        DEFAULT_TOKEN_URL,
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=25,
    )
    resp.raise_for_status()
    token_data = resp.json()
    if "refresh_token" not in token_data:
        token_data["refresh_token"] = refresh_token
    token_data["obtained_at"] = datetime.now(timezone.utc).isoformat()
    return token_data


def fetch_accounts_positions(access_token: str, positions_url: str = DEFAULT_POSITIONS_URL) -> dict | list:
    resp = requests.get(
        positions_url,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=25,
    )
    resp.raise_for_status()
    return resp.json()


def save_json_backup(payload: dict | list, output_dir: Path, prefix: str = "schwab_positions") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_file = output_dir / f"{prefix}_{ts}.json"
    out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_file


def extract_schwab_holdings(payload: dict | list, known_yields: dict[str, float] | None = None):
    """Normalize /accounts payload to app-style structures.

    Returns (holdings_by_account, all_holdings, cash_total).
    """
    known_yields = known_yields or {}
    if isinstance(payload, dict):
        accounts = payload.get("accounts", [])
    elif isinstance(payload, list):
        accounts = payload
    else:
        accounts = []

    holdings_by_account = {}
    all_holdings = {}
    cash_total = 0.0

    for acct in accounts:
        sec = acct.get("securitiesAccount", {}) if isinstance(acct, dict) else {}
        raw_acct_num = str(sec.get("accountNumber", ""))
        acct_name = f"Acct {raw_acct_num[-4:]}" if raw_acct_num else "Schwab"

        current_bal = sec.get("currentBalances", {}) if isinstance(sec.get("currentBalances", {}), dict) else {}
        initial_bal = sec.get("initialBalances", {}) if isinstance(sec.get("initialBalances", {}), dict) else {}
        cash_total += float(current_bal.get("cashBalance", 0.0) or initial_bal.get("cashBalance", 0.0) or 0.0)

        for idx, pos in enumerate(sec.get("positions", []) or []):
            inst = pos.get("instrument", {}) if isinstance(pos, dict) else {}
            ticker = str(inst.get("symbol", "")).strip().upper()
            if not ticker:
                continue
            long_qty = float(pos.get("longQuantity", 0.0) or 0.0)
            short_qty = float(pos.get("shortQuantity", 0.0) or 0.0)
            shares = long_qty - short_qty
            avg_price = float(pos.get("averagePrice", 0.0) or pos.get("averageLongPrice", 0.0) or 0.0)
            market_value = float(pos.get("marketValue", 0.0) or (shares * avg_price))
            cost = float(pos.get("currentDayCost", 0.0) or (shares * avg_price))
            pl = float(pos.get("longOpenProfitLoss", 0.0) or 0.0) - float(pos.get("shortOpenProfitLoss", 0.0) or 0.0)

            entry = {
                "ticker": ticker,
                "shares": shares,
                "price": avg_price,
                "value": market_value,
                "cost": cost,
                "pl": pl,
                "account": acct_name,
                "yield_pct": float(known_yields.get(ticker, 0.0)),
                "section": "equity",
            }
            holdings_by_account.setdefault(acct_name, []).append(entry)
            all_holdings[f"{ticker}_{acct_name}_{idx}"] = entry

    return holdings_by_account, all_holdings, cash_total


def save_tokens(token_data: dict, token_file: Path):
    token_file.write_text(json.dumps(token_data, indent=2), encoding="utf-8")


def load_tokens(token_file: Path) -> dict:
    if not token_file.exists():
        return {}
    try:
        return json.loads(token_file.read_text(encoding="utf-8"))
    except Exception:
        return {}

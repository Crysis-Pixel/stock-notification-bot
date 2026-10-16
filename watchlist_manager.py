"""
Watchlist and State Management.
Persists tracked stocks and user alert thresholds.
"""
import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
WATCHLIST_FILE = os.path.join(DATA_DIR, "watchlist.json")


def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)


def load_watchlist() -> Dict[str, Dict[str, Any]]:
    """
    Loads watchlist dictionary:
    {
        "AAPL": {
            "dip_percentage": 3.0,
            "target_price": None,
            "last_alert_time": 0,
            "last_alert_price": None,
            "baseline_price": None
        }
    }
    """
    _ensure_data_dir()
    if not os.path.exists(WATCHLIST_FILE):
        # Default starter watchlist
        default_data = {
            "AAPL": {
                "dip_percentage": 2.5,
                "target_price": None,
                "last_alert_time": 0,
                "last_alert_price": None,
                "baseline_price": None
            },
            "TSLA": {
                "dip_percentage": 3.5,
                "target_price": None,
                "last_alert_time": 0,
                "last_alert_price": None,
                "baseline_price": None
            }
        }
        save_watchlist(default_data)
        return default_data

    try:
        with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading watchlist: {e}")
        return {}


def save_watchlist(data: Dict[str, Dict[str, Any]]) -> bool:
    """Saves the watchlist dictionary to disk."""
    _ensure_data_dir()
    try:
        with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving watchlist: {e}")
        return False


def add_ticker(
    ticker: str,
    dip_percentage: float = 3.0,
    target_price: Optional[float] = None
) -> Dict[str, Any]:
    """Adds or updates a ticker in the watchlist."""
    ticker = ticker.upper().strip()
    watchlist = load_watchlist()

    existing = watchlist.get(ticker, {})
    watchlist[ticker] = {
        "dip_percentage": float(dip_percentage),
        "target_price": float(target_price) if target_price is not None else None,
        "last_alert_time": existing.get("last_alert_time", 0),
        "last_alert_price": existing.get("last_alert_price", None),
        "baseline_price": existing.get("baseline_price", None)
    }
    save_watchlist(watchlist)
    return watchlist[ticker]


def remove_ticker(ticker: str) -> bool:
    """Removes a ticker from the watchlist."""
    ticker = ticker.upper().strip()
    watchlist = load_watchlist()
    if ticker in watchlist:
        del watchlist[ticker]
        save_watchlist(watchlist)
        return True
    return False

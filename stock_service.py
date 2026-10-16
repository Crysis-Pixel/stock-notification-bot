"""
Stock Price Service using Finnhub real-time market API.
Finnhub provides real-time Cboe/BATS quotes for US stocks (matching Revolut / retail brokers).
"""
import os
import logging
import aiohttp
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

FINNHUB_QUOTE_URL = "https://finnhub.io/api/v1/quote"


class StockService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY", "")
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def fetch_quote(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetches real-time quote for ticker.
        Finnhub response structure:
        {
          "c": 175.5,   # Current price
          "d": -2.3,    # Change
          "dp": -1.29,  # Percent change
          "h": 178.2,   # High price of the day
          "l": 174.8,   # Low price of the day
          "o": 177.0,   # Open price of the day
          "pc": 177.8,  # Previous close price
          "t": 1697478000
        }
        """
        ticker = ticker.upper().strip()
        if not self.api_key or self.api_key.startswith("your_"):
            logger.warning("Finnhub API key is missing or set to placeholder.")
            return None

        params = {
            "symbol": ticker,
            "token": self.api_key
        }

        try:
            session = await self.get_session()
            async with session.get(FINNHUB_QUOTE_URL, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    current_price = data.get("c", 0)
                    # When a symbol is invalid, Finnhub returns 0 for all fields
                    if current_price and current_price > 0:
                        return {
                            "ticker": ticker,
                            "current_price": float(data.get("c", 0.0)),
                            "change": float(data.get("d", 0.0)),
                            "percent_change": float(data.get("dp", 0.0)),
                            "high": float(data.get("h", 0.0)),
                            "low": float(data.get("l", 0.0)),
                            "open": float(data.get("o", 0.0)),
                            "previous_close": float(data.get("pc", 0.0)),
                            "timestamp": data.get("t", 0)
                        }
                    else:
                        logger.warning(f"Ticker {ticker} returned empty quote from Finnhub.")
                        return None
                elif response.status == 429:
                    logger.warning("Finnhub rate limit reached (60 calls/minute on free tier).")
                    return None
                else:
                    logger.error(f"Finnhub API returned status {response.status} for {ticker}")
                    return None
        except Exception as e:
            logger.error(f"Failed to fetch quote for {ticker}: {e}")
            return None

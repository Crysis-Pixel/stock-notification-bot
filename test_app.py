"""
Self-contained unit tests to verify watchlist management,
embed generation, and keep-alive HTTP server routes.
"""
import unittest
import os
import shutil
import tempfile
import asyncio

import watchlist_manager
from keep_alive import KeepAliveServer
from main import create_dip_embed, create_quote_embed


class TestStockBot(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        watchlist_manager.DATA_DIR = self.test_dir
        watchlist_manager.WATCHLIST_FILE = os.path.join(self.test_dir, "watchlist.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_watchlist_add_and_remove(self):
        # Add ticker
        rule = watchlist_manager.add_ticker("AAPL", dip_percentage=4.5, target_price=160.0)
        self.assertEqual(rule["dip_percentage"], 4.5)
        self.assertEqual(rule["target_price"], 160.0)

        # Check loaded
        data = watchlist_manager.load_watchlist()
        self.assertIn("AAPL", data)

        # Remove ticker
        removed = watchlist_manager.remove_ticker("AAPL")
        self.assertTrue(removed)
        data = watchlist_manager.load_watchlist()
        self.assertNotIn("AAPL", data)

    def test_embed_creation(self):
        quote = {
            "ticker": "TSLA",
            "current_price": 200.0,
            "change": -10.0,
            "percent_change": -4.76,
            "high": 215.0,
            "low": 198.5,
            "open": 212.0,
            "previous_close": 210.0,
            "timestamp": 123456789
        }
        rule = {"dip_percentage": 3.0, "target_price": 205.0}

        dip_embed = create_dip_embed("TSLA", quote, rule, -4.76)
        self.assertIn("DIP ALERT", dip_embed.title)
        self.assertEqual(len(dip_embed.fields), 7)

        quote_embed = create_quote_embed(quote)
        self.assertIn("TSLA", quote_embed.title)

    def test_keep_alive_routes(self):
        async def run_server_check():
            server = KeepAliveServer(port=18899)
            await server.start()
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://127.0.0.1:18899/") as resp:
                    self.assertEqual(resp.status, 200)
                    data = await resp.json()
                    self.assertEqual(data["status"], "online")

                async with session.get("http://127.0.0.1:18899/health") as resp:
                    self.assertEqual(resp.status, 200)
                    data = await resp.json()
                    self.assertEqual(data["status"], "healthy")
            await server.stop()

        asyncio.run(run_server_check())


if __name__ == "__main__":
    unittest.main()

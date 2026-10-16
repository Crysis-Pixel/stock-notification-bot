"""
Main Discord Bot & Price Monitoring Loop.
Combines:
- Discord Slash Commands (/watch, /unwatch, /watchlist, /quote, /status)
- Continuous Stock Dip Polling Loop with intelligent alert cooldowns
- Built-in HTTP Keep-Alive server for Render 24/7 uptime
"""
import os
import sys
import time
import asyncio
import logging
from typing import Optional

from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import tasks

from keep_alive import KeepAliveServer
from stock_service import StockService
import watchlist_manager

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("StockBot")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "60"))
ALERT_COOLDOWN_MINUTES = int(os.getenv("ALERT_COOLDOWN_MINUTES", "60"))
PORT = int(os.getenv("PORT", "10000"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

stock_service = StockService()
keep_alive_server = KeepAliveServer(port=PORT)


def format_currency(val: float) -> str:
    return f"${val:,.2f}"


def create_dip_embed(ticker: str, quote: dict, rule: dict, dip_amount: float) -> discord.Embed:
    current_price = quote["current_price"]
    prev_close = quote["previous_close"]
    pct_change = quote["percent_change"]

    embed = discord.Embed(
        title=f"🚨 DIP ALERT: {ticker} has dropped!",
        description=(
            f"**{ticker}** has dropped **{abs(dip_amount):.2f}%** "
            f"below baseline/target threshold.\n"
            f"Opportunity to buy on dip!"
        ),
        color=0xE74C3C  # Bright Red/Crimson
    )
    embed.add_field(name="Current Price", value=f"**{format_currency(current_price)}**", inline=True)
    embed.add_field(name="Previous Close", value=format_currency(prev_close), inline=True)
    embed.add_field(name="Day Change", value=f"{pct_change:+.2f}%", inline=True)
    embed.add_field(name="Day High", value=format_currency(quote["high"]), inline=True)
    embed.add_field(name="Day Low", value=format_currency(quote["low"]), inline=True)
    embed.add_field(name="Watch Threshold", value=f"Dip ≥ {rule.get('dip_percentage', 3.0)}%", inline=True)

    if rule.get("target_price"):
        embed.add_field(name="Target Price", value=format_currency(rule["target_price"]), inline=True)

    embed.set_footer(text="Data source: Finnhub (Real-time Cboe/BATS) • Revolut-aligned")
    embed.timestamp = discord.utils.utcnow()
    return embed


def create_quote_embed(quote: dict) -> discord.Embed:
    ticker = quote["ticker"]
    current_price = quote["current_price"]
    change = quote["change"]
    pct = quote["percent_change"]

    color = 0x2ECC71 if change >= 0 else 0xE74C3C  # Green if up, Red if down

    embed = discord.Embed(
        title=f"📈 Market Quote: {ticker}",
        color=color
    )
    embed.add_field(name="Current Price", value=f"**{format_currency(current_price)}**", inline=True)
    embed.add_field(name="Change", value=f"{change:+.2f} ({pct:+.2f}%)", inline=True)
    embed.add_field(name="Day Range", value=f"{format_currency(quote['low'])} - {format_currency(quote['high'])}", inline=False)
    embed.add_field(name="Previous Close", value=format_currency(quote["previous_close"]), inline=True)
    embed.add_field(name="Open Price", value=format_currency(quote["open"]), inline=True)
    embed.set_footer(text="Real-time Cboe/BATS Quotes")
    embed.timestamp = discord.utils.utcnow()
    return embed


@tasks.loop(seconds=CHECK_INTERVAL_SECONDS)
async def stock_checker_task():
    """Periodic task that checks all stocks in the watchlist for dips."""
    try:
        watchlist = watchlist_manager.load_watchlist()
        if not watchlist:
            return

        target_channel_id = os.getenv("DISCORD_CHANNEL_ID")
        if not target_channel_id:
            logger.warning("DISCORD_CHANNEL_ID is not configured. Cannot send alerts.")
            return

        channel = client.get_channel(int(target_channel_id))
        if not channel:
            try:
                channel = await client.fetch_channel(int(target_channel_id))
            except Exception as e:
                logger.error(f"Could not find Discord channel with ID {target_channel_id}: {e}")
                return

        current_time = time.time()
        cooldown_seconds = ALERT_COOLDOWN_MINUTES * 60

        for ticker, rule in list(watchlist.items()):
            quote = await stock_service.fetch_quote(ticker)
            if not quote:
                continue

            current_price = quote["current_price"]
            prev_close = quote["previous_close"]
            target_dip_pct = float(rule.get("dip_percentage", 3.0))
            target_price = rule.get("target_price")

            # Calculate dip relative to previous close
            dip_from_close = ((current_price - prev_close) / prev_close) * 100

            # Condition 1: Day drop meets or exceeds dip_percentage (e.g. -3.0%)
            is_percentage_dip = dip_from_close <= -abs(target_dip_pct)

            # Condition 2: Target price reached (if set)
            is_target_hit = (target_price is not None and current_price <= target_price)

            if is_percentage_dip or is_target_hit:
                last_alert_time = rule.get("last_alert_time", 0)
                # Check cooldown
                if (current_time - last_alert_time) >= cooldown_seconds:
                    logger.info(f"Triggering dip alert for {ticker} at {current_price}")
                    embed = create_dip_embed(ticker, quote, rule, dip_from_close)
                    await channel.send(
                        content=f"🔔 **Dip detected on {ticker}!** <@everyone>",
                        embed=embed
                    )

                    # Update alert record
                    rule["last_alert_time"] = current_time
                    rule["last_alert_price"] = current_price
                    watchlist[ticker] = rule
                    watchlist_manager.save_watchlist(watchlist)

            # Avoid spamming stock API in a tight burst
            await asyncio.sleep(1.0)

    except Exception as e:
        logger.error(f"Error in stock_checker_task: {e}", exc_info=True)


@stock_checker_task.before_loop
async def before_checker():
    await client.wait_until_ready()


# --- Discord Slash Commands ---

@tree.command(name="watch", description="Add or update a stock ticker to watch for dips")
@app_commands.describe(
    ticker="Stock symbol (e.g. AAPL, TSLA, NVDA)",
    dip_percentage="Percentage dip from previous close to trigger alert (e.g. 3.0)",
    target_price="Specific price at or below which to alert (optional)"
)
async def watch_cmd(
    interaction: discord.Interaction,
    ticker: str,
    dip_percentage: float = 3.0,
    target_price: Optional[float] = None
):
    ticker = ticker.upper().strip()
    await interaction.response.defer()

    quote = await stock_service.fetch_quote(ticker)
    if not quote:
        await interaction.followup.send(
            f"❌ Could not verify quote for **{ticker}**. Please check the ticker symbol.",
            ephemeral=True
        )
        return

    rule = watchlist_manager.add_ticker(ticker, dip_percentage, target_price)

    msg = (
        f"✅ Now watching **{ticker}**!\n"
        f"• Current Price: **{format_currency(quote['current_price'])}**\n"
        f"• Alert Trigger: Dip of **≥ {rule['dip_percentage']}%**"
    )
    if rule["target_price"]:
        msg += f" or Price ≤ **{format_currency(rule['target_price'])}**"

    await interaction.followup.send(msg)


@tree.command(name="unwatch", description="Stop tracking a stock ticker")
@app_commands.describe(ticker="Stock symbol to remove")
async def unwatch_cmd(interaction: discord.Interaction, ticker: str):
    ticker = ticker.upper().strip()
    success = watchlist_manager.remove_ticker(ticker)
    if success:
        await interaction.response.send_message(f"🗑️ Removed **{ticker}** from watchlist.")
    else:
        await interaction.response.send_message(f"⚠️ **{ticker}** was not in the watchlist.", ephemeral=True)


@tree.command(name="watchlist", description="List all currently tracked stocks and their alert conditions")
async def watchlist_cmd(interaction: discord.Interaction):
    watchlist = watchlist_manager.load_watchlist()
    if not watchlist:
        await interaction.response.send_message("📭 Your watchlist is currently empty. Use `/watch` to add stocks.")
        return

    embed = discord.Embed(
        title="📋 Active Stock Watchlist",
        color=0x3498DB
    )

    for ticker, rule in watchlist.items():
        details = f"• Dip Alert: **≥ {rule['dip_percentage']}%**\n"
        if rule.get("target_price"):
            details += f"• Target Price: **{format_currency(rule['target_price'])}**\n"
        embed.add_field(name=ticker, value=details, inline=True)

    embed.set_footer(text="Use /watch to modify or /unwatch to remove tickers.")
    await interaction.response.send_message(embed=embed)


@tree.command(name="quote", description="Get the real-time quote for any stock symbol")
@app_commands.describe(ticker="Stock symbol (e.g. AAPL, MSFT, AMZN)")
async def quote_cmd(interaction: discord.Interaction, ticker: str):
    ticker = ticker.upper().strip()
    await interaction.response.defer()

    quote = await stock_service.fetch_quote(ticker)
    if not quote:
        await interaction.followup.send(f"❌ Could not retrieve data for **{ticker}**.", ephemeral=True)
        return

    embed = create_quote_embed(quote)
    await interaction.followup.send(embed=embed)


@tree.command(name="status", description="Show bot health, uptime, and Render keep-alive status")
async def status_cmd(interaction: discord.Interaction):
    uptime_seconds = int(time.time() - keep_alive_server.start_time)
    hours, rem = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(rem, 60)

    watchlist = watchlist_manager.load_watchlist()

    embed = discord.Embed(
        title="🤖 Stock Bot Status",
        color=0x2ECC71
    )
    embed.add_field(name="Status", value="🟢 Online & Monitoring", inline=True)
    embed.add_field(name="Uptime", value=f"{hours}h {minutes}m {seconds}s", inline=True)
    embed.add_field(name="Tracked Tickers", value=str(len(watchlist)), inline=True)
    embed.add_field(name="Check Interval", value=f"{CHECK_INTERVAL_SECONDS} seconds", inline=True)
    embed.add_field(name="Keep-Alive Port", value=str(PORT), inline=True)
    embed.add_field(name="Render Ping Endpoint", value=f"Port {PORT} (`/` or `/health`)", inline=False)
    await interaction.response.send_message(embed=embed)


@client.event
async def on_ready():
    logger.info(f"Logged in as {client.user} (ID: {client.user.id})")
    try:
        synced = await tree.sync()
        logger.info(f"Synced {len(synced)} application slash commands.")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")

    if not stock_checker_task.is_running():
        stock_checker_task.start()
        logger.info("Stock checker background loop started.")


async def main():
    # Start Keep-Alive HTTP server on Render's PORT
    await keep_alive_server.start()

    if not DISCORD_BOT_TOKEN or DISCORD_BOT_TOKEN.startswith("your_"):
        logger.warning(
            "DISCORD_BOT_TOKEN is not configured! "
            "Please create your .env file using .env.example before running the bot."
        )
        # Keep web server running even if Discord token is not yet configured,
        # so health-checks don't fail during deployment setup.
        while True:
            await asyncio.sleep(3600)
    else:
        try:
            await client.start(DISCORD_BOT_TOKEN)
        finally:
            await stock_service.close()
            await keep_alive_server.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot process interrupted by user.")

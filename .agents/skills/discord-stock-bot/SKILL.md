---
name: discord-stock-bot
description: >-
  Expert guidelines and operational runbook for developing, configuring, testing,
  and deploying the Discord Stock Dip Notification Bot with Render health-check server.
---

# Discord Stock Bot Skill

This skill provides domain knowledge and execution procedures for the Discord Stock Notification Bot.

## Core Architecture
1. **Discord Interface (`discord.py`)**:
   - Manages Discord gateway connection, slash commands (`/watch`, `/unwatch`, `/watchlist`, `/quote`, `/status`).
   - Rich embed notifications with color coding (Green for recovery/gain, Crimson Red for dip alerts).
2. **Stock Polling Engine (`stock_service.py`)**:
   - Queries real-time stock prices (Finnhub API / Yahoo Finance fallback).
   - Tracks 52-week high, recent highs, or percentage dip from previous close / reference baseline.
   - Throttles alerts to prevent spam (cooldown timer per ticker, e.g. 1 alert per hour unless dip exceeds previous alert by another X%).
3. **HTTP Keep-Alive Server (`aiohttp`)**:
   - Binds to `0.0.0.0:${PORT:-10000}`.
   - Responds to `GET /` and `GET /health` with HTTP 200 `{"status": "alive", "timestamp": "..."}`.
   - Ensures Render Web Service never stays idle for 15 minutes when pinged by UptimeRobot.
4. **Data Persistence (`watchlist.json` / SQLite)**:
   - Stores user watchlist with target dip percentages and reference baseline prices.

## Development Checklist
- Always use asynchronous libraries (`aiohttp`, `discord.py`) to prevent blocking the event loop.
- Secure all tokens/keys using `.env` (`DISCORD_BOT_TOKEN`, `FINNHUB_API_KEY`, `PORT`).
- Graceful error handling for stock API rate limits.

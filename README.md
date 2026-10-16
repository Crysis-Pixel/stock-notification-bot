# Real-Time Stock Dip Notification Discord Bot 📉🔔

An always-on Discord bot that continuously monitors real-time US stock quotes (Finnhub API / Cboe BATS feed matching Revolut) and instantly sends push notifications with rich embeds when a stock dips below your defined threshold.

Designed to run **100% free 24/7 on Render** using an integrated HTTP keep-alive server pinged by free external uptime monitors.

---

## ⚡ Features
- **Real-Time Market Quotes**: Connected to Finnhub (Cboe BATS real-time quote feed, identical to Revolut retail quotes).
- **Custom Dip Thresholds**: Track percentage drops (e.g., `-3.0%` from previous close) or target price floors (e.g., `≤ $150.00`).
- **Rich Embed Notifications**: Formatted Discord embeds displaying current price, daily range, previous close, percentage change, and direct buy cues with `@everyone` tags.
- **Anti-Spam Cooldown**: Built-in alert cooldown prevents repeat pings on every minor price fluctuation.
- **Interactive Slash Commands**:
  - `/watch <ticker> [dip_percentage] [target_price]`: Add or update tracked stock.
  - `/unwatch <ticker>`: Remove a stock from tracking.
  - `/watchlist`: View all actively monitored tickers and triggers.
  - `/quote <ticker>`: Query the real-time quote of any stock anytime.
  - `/status`: Check bot uptime, Render keep-alive server status, and health.
- **Render 24/7 Keep-Alive**: Includes an embedded `aiohttp` web server bound to Render's port (`PORT=10000`) ready for UptimeRobot pings.

---

## 🛠️ Step-by-Step Setup Guide

### 1. Get Free Finnhub API Key
1. Go to [finnhub.io](https://finnhub.io/) and create a free account.
2. Copy your **API Key** from the dashboard.

### 2. Create Your Discord Bot
1. Open the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application** and give it a name (e.g., `StockDipBot`).
3. Under **Bot**:
   - Click **Reset Token** and copy the **Bot Token**.
4. Under **OAuth2 → URL Generator**:
   - Check `bot` and `applications.commands`.
   - Under Bot Permissions, check:
     - `Send Messages`
     - `Embed Links`
     - `Mention Everyone`
   - Copy the generated URL and open it in your browser to invite the bot to your Discord server.
5. In your Discord server:
   - Right-click the channel where you want notifications (enable Developer Mode in Discord Settings if needed).
   - Click **Copy Channel ID**.

### 3. Local Configuration & Testing
1. Clone or open this folder.
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Fill in your keys in `.env`:
   ```env
   DISCORD_BOT_TOKEN=your_token_here
   DISCORD_CHANNEL_ID=your_channel_id_here
   FINNHUB_API_KEY=your_finnhub_key_here
   PORT=10000
   CHECK_INTERVAL_SECONDS=60
   ALERT_COOLDOWN_MINUTES=60
   ```
4. Run tests:
   ```bash
   source .venv/bin/activate
   python -m unittest test_app.py
   ```
5. Run the bot locally:
   ```bash
   python main.py
   ```

---

## 🚀 Free 24/7 Cloud Deployment on Render

### Step A: Push to GitHub
1. Create a new private repository on [GitHub](https://github.com).
2. Initialize git and push this folder:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of stock notification discord bot"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

### Step B: Deploy on Render
1. Go to [Render.com](https://render.com/) and sign up / log in.
2. Click **New +** → **Web Service**.
3. Select your GitHub repository.
4. Render will automatically detect `render.yaml` or you can configure:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Instance Type**: **Free**
5. Under **Environment Variables**, add:
   - `DISCORD_BOT_TOKEN`: (Your bot token)
   - `DISCORD_CHANNEL_ID`: (Your channel ID)
   - `FINNHUB_API_KEY`: (Your Finnhub key)
   - `PORT`: `10000`
6. Click **Deploy Web Service**.
7. Once deployed, Render will provide a public URL (e.g. `https://stock-discord-bot.onrender.com`).

### Step C: Keep Awake with UptimeRobot (Free)
1. Go to [uptimerobot.com](https://uptimerobot.com/) and register for a free account.
2. Click **Add New Monitor**:
   - **Monitor Type**: `HTTP(s)`
   - **Friendly Name**: `Stock Bot Keep-Alive`
   - **URL (or IP)**: `https://YOUR-APP-NAME.onrender.com/` (your Render URL)
   - **Monitoring Interval**: `5 minutes`
3. Click **Create Monitor**.
4. **Done!** UptimeRobot will ping your bot every 5 minutes, preventing Render's free tier from sleeping. Your bot will remain online 24/7!

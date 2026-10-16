# Project Rules for Discord Stock Notification App

- **Asynchronous Execution**: All network calls (Discord API, stock queries, HTTP keep-alive) MUST be non-blocking and use `async`/`await` (e.g., `aiohttp`, `asyncio`).
- **Security & Secrets**: Never hardcode API keys, Discord tokens, or webhooks. Always retrieve them via `os.getenv` with helpful error messages if missing. Use `.env.example` as a template and ignore `.env` in `.gitignore`.
- **Render Compatibility**: Ensure the application exposes an HTTP server on the port given by `PORT` (defaulting to 10000) so Render recognizes it as an active web service.
- **Alert Quality & Rate Limiting**: Dip notifications must include ticker symbol, current price, baseline price, percentage drop, timestamp, and a cooldown check to avoid spamming the channel.

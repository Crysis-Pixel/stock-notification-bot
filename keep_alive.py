"""
Lightweight HTTP Server for Render Keep-Alive.
Render's free tier keeps the service awake as long as it handles incoming HTTP traffic.
Ping this endpoint using free services like UptimeRobot or Cron-Job.org every 5-10 minutes.
"""
import os
import time
import logging
from aiohttp import web

logger = logging.getLogger(__name__)


class KeepAliveServer:
    def __init__(self, port: int = 10000):
        self.port = port
        self.app = web.Application()
        self.app.router.add_get("/", self.handle_root)
        self.app.router.add_get("/health", self.handle_health)
        self.runner = None
        self.site = None
        self.start_time = time.time()

    async def handle_root(self, request):
        uptime_seconds = int(time.time() - self.start_time)
        return web.json_response({
            "status": "online",
            "message": "Stock Notification Discord Bot is active!",
            "uptime_seconds": uptime_seconds
        })

    async def handle_health(self, request):
        return web.json_response({
            "status": "healthy",
            "timestamp": time.time()
        })

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "0.0.0.0", self.port)
        await self.site.start()
        logger.info(f"Keep-Alive HTTP server listening on http://0.0.0.0:{self.port}")

    async def stop(self):
        if self.runner:
            await self.runner.cleanup()
            logger.info("Keep-Alive HTTP server stopped.")

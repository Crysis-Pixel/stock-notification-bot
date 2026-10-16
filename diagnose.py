import asyncio
import os
import discord
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")
channel_id = int(os.getenv("DISCORD_CHANNEL_ID"))

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    print(f"\n=== Logged in as: {client.user} ===")
    print(f"Total Guilds/Servers Bot is in: {len(client.guilds)}")
    
    for g in client.guilds:
        print(f"\nGuild Name: '{g.name}' (ID: {g.id})")
        found = False
        for c in g.channels:
            if c.id == channel_id:
                found = True
                print(f"  --> FOUND TARGET CHANNEL: '{c.name}' (Type: {c.type})")
                me = g.me
                perms = c.permissions_for(me)
                print(f"      Bot Permissions in channel:")
                print(f"        view_channel: {perms.view_channel}")
                print(f"        send_messages: {perms.send_messages}")
                print(f"        embed_links: {perms.embed_links}")
        if not found:
            print("  --> Target channel NOT in this guild. Here are all channels the bot can see:")
            for c in g.channels:
                if str(c.type) in ["text", "news"]:
                    print(f"      Channel: #{c.name} (ID: {c.id})")

    await client.close()

asyncio.run(client.start(token))

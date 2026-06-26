import os
import discord

TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable not set")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    print("Ready.")


@client.event
async def on_message(message):
    print(message)
    print(f"[{message.guild} / #{message.channel}] {message.author}: {message.content}")


client.run(TOKEN)

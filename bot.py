import os
import discord
import asyncio
import signal
import aiohttp
import hashlib
import time
from collections import defaultdict

# Config
BOT_TOKEN = os.environ.get("DISCORD_TOKEN")
if not BOT_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable not set")

SPAM_WINDOW_SECONDS = 60  # How far back to look
SPAM_CHANNEL_THRESHOLD = 3  # How many distinct channels before it's spam
ALERT_CHANNEL_NAME = "general"  # Channel to send spam alerts to

# State
# { guild_id: { message_key: [(channel_id, timestamp), ...] } }
tracker: dict[int, dict[tuple, list]] = defaultdict(lambda: defaultdict(list))


# Attachment hashing
async def hash_attachment(session: aiohttp.ClientSession, attachment: discord.Attachment) -> str:
    """Download an attachment and return the MD5 hash of its bytes."""
    try:
        async with session.get(attachment.url) as resp:
            data = await resp.read()
            return hashlib.md5(data).hexdigest()
    except Exception:
        # Fall back to filename so we don't silently drop the attachment
        return f"fallback:{attachment.filename}"


async def get_attachment_hashes(attachments: list[discord.Attachment]) -> tuple[str, ...]:
    """Return a sorted tuple of MD5 hashes for all attachments in a message."""
    if not attachments:
        return ()
    async with aiohttp.ClientSession() as session:
        hashes = [await hash_attachment(session, a) for a in attachments]
    return tuple(sorted(hashes))


# Spam detection
def make_message_key(user_id: int, content: str, attachment_hashes: tuple) -> tuple:
    """
    Unique key for a (user, message content, attachments) combo.
    Two messages with the same key are considered identical.
    """
    return (user_id, content, attachment_hashes)


def record_and_check(guild_id: int, key: tuple, channel_id: int) -> set[int] | None:
    """
    Record this message occurrence and return the set of distinct channels
    it appeared in if the spam threshold is reached, otherwise None.
    Prunes entries older than SPAM_WINDOW_SECONDS automatically.
    """
    now = time.time()
    entries = tracker[guild_id][key]

    entries.append((channel_id, now))

    # Drop stale entries outside the window
    tracker[guild_id][key] = [(ch, ts) for ch, ts in entries if now - ts <= SPAM_WINDOW_SECONDS]

    distinct_channels = {ch for ch, _ in tracker[guild_id][key]}

    if len(distinct_channels) >= SPAM_CHANNEL_THRESHOLD:
        del tracker[guild_id][key]  # Reset so we don't re-alert for the same burst
        return distinct_channels

    return None


# Alerting
def build_spam_embed(message: discord.Message, channels: set[int]) -> discord.Embed:
    """Build the embed that gets posted to #general when spam is detected."""
    attachment_links = "\n".join(a.url for a in message.attachments) or "None"
    channel_mentions = ", ".join(f"<#{ch}>" for ch in channels)

    embed = discord.Embed(title="🚨 [Testing] I smell spam", color=discord.Color.red())
    embed.add_field(name="Sender", value=str(message.author), inline=False)
    embed.add_field(name="Message", value=message.content or "*(no text)*", inline=False)
    embed.add_field(name="Attachments", value=attachment_links, inline=False)
    embed.add_field(name="Channels", value=channel_mentions, inline=False)

    return embed


async def send_spam_alert(guild: discord.Guild, message: discord.Message, channels: set[int]):
    """Find #general and post a spam alert embed."""
    general = discord.utils.get(guild.text_channels, name=ALERT_CHANNEL_NAME)
    if not general:
        print(f"[warn] Could not find #{ALERT_CHANNEL_NAME} in {guild.name}")
        return
    await general.send(embed=build_spam_embed(message, channels))


# Main
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):
    # Ignore bots and DMs
    if message.author.bot or not message.guild:
        return

    print(f"[{message.guild} / #{message.channel}] {message.author}: {message.content}")

    hashes = await get_attachment_hashes(message.attachments)
    key = make_message_key(message.author.id, message.content, hashes)
    spam_channels = record_and_check(message.guild.id, key, message.channel.id)

    if spam_channels:
        print(f"[spam] {message.author} triggered spam detection across {len(spam_channels)} channels")
        await send_spam_alert(message.guild, message, spam_channels)


def handle_sigint(sig, frame):
    print("\nShutting down...")
    asyncio.create_task(client.close())


signal.signal(signal.SIGINT, handle_sigint)

client.run(BOT_TOKEN)

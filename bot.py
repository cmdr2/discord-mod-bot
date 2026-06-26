import discord
import asyncio
import signal
import aiohttp
import hashlib
import logging as log
import time
import os
from collections import defaultdict

# Config
BOT_TOKEN = os.environ.get("DISCORD_TOKEN")
if not BOT_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable not set")

SPAM_WINDOW_SECONDS = 60
SPAM_CHANNEL_THRESHOLD = 3
ALERT_CHANNEL_NAME = "mod-room"  # Channel to send spam alerts to

log.basicConfig(
    filename="log.txt",
    filemode="a",
    level=log.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)

# State

# { guild_id: { message_key: [(channel_id, timestamp, message_id), ...] } }
tracker: dict[int, dict[tuple, list]] = defaultdict(lambda: defaultdict(list))
# { guild_id: { message_key: expiry_timestamp } }
confirmed_spam: dict[int, dict[tuple, float]] = defaultdict(dict)


# Privilege checking
def is_privileged(member: discord.Member) -> bool:
    """Return True if the member is the server owner or has a role with moderator permissions."""
    if member.guild.owner_id == member.id:
        return True
    return any(role.permissions.administrator or role.permissions.moderate_members for role in member.roles)


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


def record_and_check(
    guild_id: int, key: tuple, channel_id: int, message_id: int
) -> tuple[list[tuple[int, int]], list[str]]:
    """
    Record this message occurrence and return a list of (channel_id, message_id) pairs, and actions to perform.
    If the spam threshold is reached across enough distinct channels, return "alert" and "delete" actions.
    If the spam has already been confirmed (and alerted), return "delete" action.
    Otherwise, return an empty list of pairs and no actions.

    Records confirmed spam entries with a TTL of 10 * SPAM_WINDOW_SECONDS.
    """
    now = time.time()

    # If already confirmed spam, delete the msg immediately (unless the window expired)
    if key in confirmed_spam[guild_id]:
        if now < confirmed_spam[guild_id][key]:
            return [(channel_id, message_id)], ["delete"]
        else:  # TTL expired, clear the entry
            del confirmed_spam[guild_id][key]

    entries = tracker[guild_id][key]
    entries.append((channel_id, now, message_id))

    tracker[guild_id][key] = [(ch, ts, mid) for ch, ts, mid in entries if now - ts <= SPAM_WINDOW_SECONDS]

    distinct_channels = {ch for ch, _, _ in tracker[guild_id][key]}

    if len(distinct_channels) >= SPAM_CHANNEL_THRESHOLD:
        matches = [(ch, mid) for ch, _, mid in tracker[guild_id][key]]
        confirmed_spam[guild_id][key] = now + (10 * SPAM_WINDOW_SECONDS)
        del tracker[guild_id][key]
        return matches, ["alert", "delete"]

    return [], []


# Alerting
def build_spam_embed(message: discord.Message, matches: list[tuple[int, int]]) -> discord.Embed:
    """Build the embed posted to #ALERT_CHANNEL_NAME when spam is detected."""
    attachment_links = "\n".join(a.url for a in message.attachments) or "None"
    channel_mentions = ", ".join(f"<#{ch}>" for ch, _ in matches)

    embed = discord.Embed(title="🚨 I smell spam", color=discord.Color.red())
    embed.add_field(name="Sender", value=str(message.author), inline=False)
    embed.add_field(name="Message", value=message.content or "*(no text)*", inline=False)
    embed.add_field(name="Attachments", value=attachment_links, inline=False)
    embed.add_field(name="Channels", value=channel_mentions, inline=False)

    return embed


async def send_spam_alert(guild: discord.Guild, message: discord.Message, matches: list[tuple[int, int]]):
    """Post a spam alert embed to #ALERT_CHANNEL_NAME."""
    alert_channel = discord.utils.get(guild.text_channels, name=ALERT_CHANNEL_NAME)
    if not alert_channel:
        log.warning(f"[warn] Could not find #{ALERT_CHANNEL_NAME} in {guild.name}")
        return
    log.warning(f"[alert] Sending spam alert for {message.author} in #{message.channel.name}")
    await alert_channel.send(embed=build_spam_embed(message, matches))


async def delete_spam_messages(guild: discord.Guild, matches: list[tuple[int, int]]):
    """Delete all tracked spam messages by their stored IDs."""
    for channel_id, message_id in matches:
        channel = guild.get_channel(channel_id)
        if not channel:
            continue
        try:
            msg = await channel.fetch_message(message_id)
            log.warning(f"[delete] Deleting message {message_id} in #{channel.name}")
            await msg.delete()
        except discord.NotFound:
            pass  # Already deleted
        except discord.Forbidden:
            log.warning(f"[warn] Missing permission to delete message in #{channel.name}")
        except Exception as e:
            log.error(f"[error] Failed to delete message {message_id} in #{channel.name}: {e}")


# Main
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    log.info(f"Logged in as {client.user}")
    log.info("Ready.")


@client.event
async def on_message(message: discord.Message):
    # Ignore bots and DMs
    if message.author.bot or not message.guild:
        return

    log.debug(f"[{message.guild} / #{message.channel}] {message.author}: {message.content}")

    if is_privileged(message.author):
        return

    hashes = await get_attachment_hashes(message.attachments)
    key = make_message_key(message.author.id, message.content, hashes)
    matches, actions = record_and_check(message.guild.id, key, message.channel.id, message.id)

    if matches:
        log.warning(
            f"[spam] {message.author} triggered spam detection across {len(set(ch for ch, _ in matches))} channels"
        )
        if "alert" in actions:
            await send_spam_alert(message.guild, message, matches)
        if "delete" in actions:
            await delete_spam_messages(message.guild, matches)


def handle_sigint(sig, frame):
    print("\nShutting down...")
    asyncio.create_task(client.close())


signal.signal(signal.SIGINT, handle_sigint)

client.run(BOT_TOKEN)

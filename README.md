# discord-mod-bot

## Setup:
### Create a Bot
1. Go to [https://discord.com/developers/applications](https://discord.com/developers/applications), create an app, add a Bot, and copy the token. Make the app and bot private, if necessary.
2. Under `Bot → Privileged Gateway Intents`, enable `Message Content Intent` (required or `message.content` will be empty).
3. Invite the bot to your server by generating an invite link from the `OAuth2` section. Select the bot scope and the following permissions: `Read Message History`, `Send Messages`, `Manage Messages`, `Embed Links`, `View Channels`.
4. Copy the generated URL at the bottom and open it in your browser.
5. Pick which server to add it to.

### Allowing the bot to post in #mod-room
Create a channel called `#mod-room` with restricted permissions (owners and moderators only). If you use a different name for the channel, update the `ALERT_CHANNEL_NAME` variable in `bot.py`.

Since `#mod-room` has restricted visibility, Discord's permission overwrites will block the bot by default even if it has `Send Messages` globally. You need to explicitly grant it access:

1. Go to `#mod-room → Edit Channel → Permissions`.
2. Click `+` and add your bot (search by its username).
3. Grant it: `View Channel`, `Send Messages`, `Embed Links`.

The bot doesn't need `Read Messages History` in `#mod-room` since it only posts there, not reads from it.

### Start the Bot
On the server that'll run the bot:

1. `pip install discord.py`
2. Create a `.env` file in the project root with `DISCORD_TOKEN=<your_bot_token>`, then run `source .env`
3. Run `python bot.py`

### Example post in #mod-room
<img width="805" height="357" alt="image" src="https://github.com/user-attachments/assets/225c1ebb-8999-43de-a309-459c1093f720" />

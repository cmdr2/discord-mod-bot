# discord-mod-bot

## Setup:
### Create a Bot
1. Go to [https://discord.com/developers/applications](https://discord.com/developers/applications), create an app, add a Bot, and copy the token. Make the app and bot private, if necessary.
2. Under `Bot → Privileged Gateway Intents`, enable `Message Content Intent` (required or `message.content` will be empty).
3. Invite the bot to your server by generating an invite link from the `OAuth2` section. Select the bot scope and the following permissions: `Read Messages`, `Send Messages`, `Embed Links`, `Read Message History`.
4. Copy the generated URL at the bottom and open it in your browser.
5. Pick which server to add it to.

### Start the Bot
On the server that'll run the bot:

1. `pip install discord.py`
2. Create a `.env` file in the project root with `DISCORD_TOKEN=<your_bot_token>`
3. Run `python bot.py`

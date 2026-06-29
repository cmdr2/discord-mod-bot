Spam protection for my two servers (Freebird and Easy Diffusion). My server frequently gets attacked by compromised users, who always post in a very specific pattern.

Pattern: Duplicate message across multiple channels within 60 seconds (with one or more identical images).

I tried alternatives, but they either didn't catch this simple pattern, or were too bloated and complex for my simple server needs. The spam load has increased significantly over the past few weeks.

My bot simply checks whether the same message was sent across multiple channels, with one or more identical image attachments, within 60 seconds. If so, it deletes the messages, and posts a report in the private #mod-room channel. The report mentions the post author, and a copy of the post content, and links to the post image URLs. This helps audit the bot's behavior.

The bot does not store user messages, other than a brief "in-memory" storage for upto 10 minutes, to allow catching delayed spamming patterns. After 10 minutes, the in-memory message buffer is cleared of old messages.

Message Content: Here's the spam alert posted by my bot in our #mod-room channel - https://me.cmdr2.org/tmp/modbot.jpg

Here's an example of the kind of spam we get regularly - https://me.cmdr2.org/tmp/spam-example.jpg

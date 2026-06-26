#!/usr/bin/env bash

# Create directory structure
mkdir -p $PREFIX/var/service/discord-mod-bot/log

# Link the logger service
ln -sf $PREFIX/share/termux-services/svlogger $PREFIX/var/service/discord-mod-bot/log/run

# Overwrite and write the run file cleanly with the correct shebang
RUN_FILE=$PREFIX/var/service/discord-mod-bot/run
cat << 'EOF' > "$RUN_FILE"
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
cd /data/data/com.termux/files/home/discord-mod-bot
exec ./run.sh 2>&1
EOF

# Make it executable
chmod +x "$RUN_FILE"

# Enable and check status
sv-enable discord-mod-bot
sv up discord-mod-bot
sv status discord-mod-bot

#!/usr/bin/env bash

nohup python bot.py > /dev/null 2> crash_log.txt &
disown

echo "Bot launched. System errors will be saved to crash_log.txt"

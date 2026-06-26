#!/usr/bin/env bash

sv status discord-mod-bot

tail -f $PREFIX/var/log/sv/discord-mod-bot/current

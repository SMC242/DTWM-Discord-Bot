#!/bin/bash
git pull
pip3 install -r requirements.txt
sudo systemctl daemon-reload
sudo systemctl restart DiscordBot.service
sudo systemctl enable Discordbot.service

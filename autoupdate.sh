#!/bin/bash
git pull
yes | pip3 install -r ./Text\ Files/requirements.txt
sudo systemctl daemon-reload
sudo systemctl restart DiscordBot.service
sudo systemctl enable Discordbot.service

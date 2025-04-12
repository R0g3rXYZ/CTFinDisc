# CTFinDisc
Bot to integrate CTFd with Discord.

# Installation Instructions:
Instructions to run this bot.
## 1. Prequisites
Before you run the bot you must first have a few tokens/ids.
For the Discord API you will need to create a Discord bot through the Discord Developer Portal. You will need to assign the relevant permissions for this bot, read messages, send messages, and see message history. Once you have done this you can add the bot to your server. In the server you add it to, you will need to create/choose a channel for the bot to use. You will need the Discord bot API token/key and the channel ID for running the bot.
You also need to go into CTFd (in an administrator account) and generate a personal API token.
## 2. Running the Bot
To run the bot you must first download the `bot.py` and `requirements.txt` files. You then must use pip to install all of the requirements from the requirements file. Once you have done this you can input the Discord bot API token/key into the bot.py file (line 23). You can now run the file using:
```
python bot.py -t <ctfd_token> -u <ctfd_url> -c <channel_id>
```

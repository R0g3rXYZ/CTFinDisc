# CTFinDisc
Bot to integrate CTFd with Discord.

# Installation Instructions:
Instructions to run this bot.
## 1. Prequisites
Before you run the bot you must first have a few tokens/ids.
### Discord API:
First you will need to create a Discord bot through the Discord Developer Portal. Once you have done this you can add the bot to your server. 
In the server you add it to, you will need to create/choose a channel for the bot to use. 
Save the Discord API Token and the Channel ID as you will need them to run the bot.
### CTFd API:
You also need to go into CTFd (in an administrator account) and generate a personal API token.
## 2. Running the Bot
### Setup:
To run the bot you must first download the `bot.py` and `requirements.txt` files, or you can use `git clone https://github.com/R0g3rXYZ/CTFinDisc.git`. 
You then must use pip to install all of the requirements from the requirements file: `pip install requirements.txt`. 
You must then input the Discord API token into line 23 of the bot.py file.
### Command to run:
You can now run the file using:
```
python bot.py -t <ctfd_token> -u <ctfd_url> -c <channel_id>
```

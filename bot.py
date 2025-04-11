#!/usr/bin/env python3
import os
import discord
from discord.ext import commands, tasks
import time
import datetime
import requests
import json
import sys
import asyncio
import argparse

# Global variables to be set from CLI arguments
start_time = time.time()
url = ""
channel_id = 0
prevsolve = ""
page = 1
api_token = ""
common_headers = {}

# Set your bot token here (or consider loading it from an environment variable)
TOKEN = "<YOUR_TOKEN_HERE>"

# -------- Helper functions --------
def get_team_info(teamname):
    response = requests.get(f"{url}/api/v1/scoreboard", headers=common_headers, verify=True)
    data = response.json()['data']
    msg = "Team Info\n"
    for i in data:
        if i['name'].lower() == teamname.lower():
            msg += "**" + i['name'] + "** => Current Score: " + str(i['score']) + "\n\n"
            msg += "Team Members\n"
            for j in i['members']:
                msg += j['name'] + "\n"
            return msg
    return {"Error": "Teamname Not found"}

def get_scoreboard():
    response = requests.get(f"{url}/api/v1/scoreboard", headers=common_headers, verify=True)
    data = response.json()['data']
    message = "```\n"
    for i in data[:20]:
        message += f"#{i['pos']} : {i['name']} ==> {i['score']} points\n"
    message += "```"
    return message

def descchall(challname):
    response = requests.get(f"{url}/api/v1/challenges", headers=common_headers, verify=True)
    data = response.json()['data']
    category = []
    for i in data:
        category.append(i['category'])
        if i['name'].lower() == challname.lower():
            return {"name": i['name'], 'points': i['value'], 'type': i['type'], 'category': i['category']}
    if challname in category:
        challs = [i['name'] for i in data if i['category'].lower() == challname.lower()]
        return challs
    return {"Error": "Challenge or Category Name Not found"}

def get_challenges():
    response = requests.get(f"{url}/api/v1/challenges", headers=common_headers, verify=True)
    data = response.json()['data']
    return {i['id']: i['name'] for i in data}

def submission():
    try:
        global page
        response = requests.get(f"{url}/api/v1/submissions?page={page}&per_page=1&type=correct", headers=common_headers, verify=True)
        meta = response.json().get("meta",{}).get("pagination", {})
        current_page = meta.get("page", 1)
        max_page = meta.get("pages", 1)
        res_json = response.json()
        if current_page < max_page:
            response = requests.get(f"{url}/api/v1/submissions?page={max_page}&per_page=1&type=correct", headers=common_headers, verify=True)
            page = max_page
            res_json = response.json()
        data = response.json().get('data', [])
        if not data:
            print("no data")
            return []
        last = data[-1]
    except Exception as e:
        print(f"Data json parsing in submission incorrect: {e}")
        return []
    if last['type'] != "incorrect":
        response = requests.get(f"{url}/api/v1/users", headers=common_headers, verify=True)
        users = {i["id"]: i["name"] for i in response.json()['data']}
        return [users.get(last["user_id"], "Unknown"), last['challenge_id'], last['date']]
    return []

def author_info():
    response = requests.get(f"{url}/api/v1/challenges", headers=common_headers, verify=True)
    data = response.json().get('data', [])
    authors = {}
    for challenge in data:
        try:
            for tag in challenge.get('tags', []):
                value = tag.get('value', '')
                if value.startswith("@"):
                    author = value[1:]
                    authors.setdefault(author, []).append(challenge['name'])
        except Exception:
            continue
    return authors

def position(user):
    response = requests.get(f"{url}/api/v1/scoreboard", headers=common_headers, verify=True)
    data = response.json()['data']
    for i in data:
    #    for j in i['members']: uncomment for team mode in ctfd and remove below if statement
     #       if j['name'] == user:
        if i["name"] == user:
            return [i['pos'], i['score']]
    return {"Error": "User not Found"}

# -------- Bot Setup --------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
bot.remove_command("help")

last_scoreboard_update = None
scoreboard_msg = None

@bot.event
async def on_ready():
    print(f"{bot.user} has connected.")
    channel = bot.get_channel(channel_id)
    if channel:
        try:
            await channel.purge(limit=None)
        except discord.errors.Forbidden:
            print("Bot lacks permissions to purge messages.")
        await channel.send(
            "```bash\nThis is magicbytebot joining your channel. The bot will keep you updated on live scoreboard and valid submissions. Type /help for more info.```"
        )
        score = get_scoreboard()
        embed = discord.Embed(title="ScoreBoard", description=score, colour=0x080f5d)
        global scoreboard_msg
        scoreboard_msg = await channel.send(embed=embed)
        await scoreboard_msg.pin()
        monitor_submissions.start()

@tasks.loop(seconds=3)
async def monitor_submissions():
    global prevsolve, last_scoreboard_update
    channel = bot.get_channel(channel_id)
    if channel is None:
        return
    try:
        score = get_scoreboard()
        chall = get_challenges()
        check = submission()
        #print(prevsolve)
        if check:
            temp = " ".join(str(v) for v in check)
            #print(temp)
            if temp != prevsolve:
                prevsolve = temp
                pos_score = position(check[0])
                if isinstance(pos_score, list):
                    pos, score_val = pos_score
                    chall_name = chall.get(int(check[1]), "Unknown")
                    solve_time = datetime.datetime.strptime(
                        check[2], "%Y-%m-%dT%H:%M:%S.%f%z"
                    ).strftime("%b %d %Y %H:%M:%S")
                    msg = (f"**{check[0]}** has solved challenge **{chall_name}** "
                           f"(Current Rank: {pos}, Total score: {score_val}) at {solve_time}")
                    embed = discord.Embed(title="Kudos", description=msg, colour=0x46befa)
                    await channel.send(embed=embed)
                    global scoreboard_msg
                    if scoreboard_msg:
                        embed = discord.Embed(title="ScoreBoard", description=score, colour=0x080f5d)
                        await scoreboard_msg.edit(embed=embed)
    except Exception as e:
        print(f"Error in background task: {e}")

# -------- Commands --------
@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="Help",
        description=(
            "Magicbytebot monitors live solves and submissions, updates the scoreboard, "
            "and provides commands to get detailed info from the CTFd platform."
        ),
        colour=0x46befa,
    )
    embed.set_author(name="magicbytebot", url="https://google.com")
    #embed.set_thumbnail(url="https://i.imgur.com/352sSJI.png")
    embed.add_field(name="/team <teamname>", value="Display team details and members", inline=False)
    embed.add_field(name="/user <username>", value="Show your current rank and score", inline=False)
    embed.add_field(name="/scoreboard [full]", value="Display top 20 teams or full scoreboard link", inline=False)
    embed.add_field(name="/challenge <list/challenge_name/category>", value="List challenges or display details", inline=False)
    embed.add_field(name="/author <list/author_name/challenge_name>", value="List authors or get challenge author info", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def team(ctx, *, teamname: str):
    info = get_team_info(teamname)
    if isinstance(info, str):
        await ctx.send(info)
    else:
        await ctx.send(info.get("Error", "Team not found"))

@bot.command()
async def user(ctx, username: str = None):
    data = position(username)
    if isinstance(data, list):
        pos, score_val = data
        msg = f"```ini\n- {username}'s Current Rank: {pos}\n- Total Score: {score_val}\n```"
        await ctx.send(msg)
    else:
        await ctx.send(data.get("Error", "User not found"))

@bot.command()
async def scoreboard(ctx, arg: str = None):
    if arg and arg.lower() == "full":
        await ctx.send("Checkout the link for Full Scoreboard: " + url + "/scoreboard")
    else:
        score_msg = get_scoreboard()
        embed = discord.Embed(title="ScoreBoard", description=score_msg, colour=0x080f5d)
        sent = await ctx.send(embed=embed)

@bot.command()
async def challenge(ctx, *, arg: str):
    challs = get_challenges()
    if arg.lower() == "list":
        msg = "List of Active Challenges:\n"
        for i, name in enumerate(challs.values(), start=1):
            msg += f"> {i}. {name}\n"
        await ctx.send(msg)
    else:
        info = descchall(arg)
        if isinstance(info, list):
            msg = f"List of {arg} Challenges:\n"
            for i, name in enumerate(info, start=1):
                msg += f"> {i}. {name}\n"
            await ctx.send(msg)
        elif "Error" not in info:
            embed = discord.Embed(title="Challenge Description")
            embed.add_field(name="Name", value=info['name'], inline=True)
            embed.add_field(name="Category", value=info['category'], inline=True)
            embed.add_field(name="Points", value=info['points'], inline=True)
            embed.add_field(name="Type", value=info['type'], inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send(info.get("Error", "Challenge not found"))

@bot.command()
async def author(ctx, *, arg: str):
    authors = author_info()
    all_challs = [ch for challs in authors.values() for ch in challs]
    if arg.lower() == "list":
        msg = "Here is the list of Authors:\n"
        for auth in authors.keys():
            msg += f"- {auth}\n"
        await ctx.send(msg)
    else:
        if arg in authors:
            msg = f"List of Challenges created by **{arg}**:\n"
            for ch in authors[arg]:
                msg += f"> {ch}\n"
            await ctx.send(msg)
        elif arg.strip() in all_challs:
            auth_id = None
            for auth, challs in authors.items():
                if arg.strip() in challs:
                    auth_id = auth
                    break
            if auth_id:
                await ctx.send(f"<@{ctx.author.id}> Please ping @{auth_id} for challenge queries.")
            else:
                await ctx.send("Author not found.")
        else:
            await ctx.send("Challenge name or Author name not found.")

# -------- Main Execution --------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--token", required=True, help="API access token for CTFd")
    parser.add_argument("-u", "--url", required=True, help="CTFd platform URL")
    parser.add_argument("-c", "--channel", required=True, help="Discord channel ID")
    args = parser.parse_args()

    channel_id = int(args.channel)
    url = args.url.rstrip("/")
    api_token = args.token
    common_headers = {
        "Authorization": f"Token {api_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "magicbytebot/1.0"
    }

    # Validate token
    resp = requests.get(f"{url}/api/v1/submissions", headers=common_headers, verify=True)
    if resp.status_code != 200:
        print("ERROR: Invalid API token or insufficient permissions.")
        sys.exit(1)

    bot.run(TOKEN)


# Import dependencies.

import discord
import json
import random
import time
import mysql.connector
import validators
import asyncio

# Load the configuration file.
with open('./storage/config.json') as f:
    config = json.load(f)

prefix = config.get("prefix")
token = config.get("token")

client = discord.Client()

mydb = mysql.connector.connect(
  host=config.get("db_host"),
  user=config.get("db_user"),
  password=config.get("db_password"),
  database=config.get("db_database")
)

mycursor = mydb.cursor()

@client.event
async def on_ready():
    print('Currently online!')
    await client.change_presence(activity=discord.Streaming(name= prefix + "help", url="https://twitch.tv/NateTheCarrot"))
    global log_channel
    log_channel = client.get_channel(config.get("logs_id"))

client.run(token)
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

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
owner_id = config.get("owner_id")

client = discord.Client()

queue = []

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
    await client.change_presence(activity=discord.Streaming(name= prefix + "add to register a channel!", url="https://twitch.tv/NateTheCarrot"))
    global log_channel
    log_channel = client.get_channel(config.get("logs_id"))

@client.event
async def on_message(message):
    if(message.author.bot): # Checks if the person who sent the message is a bot, and if they are:
        return # It will ignore the message.

    msg = message.content.lower().replace("'", "").replace("\"", "").replace("`", "")
    if(msg == prefix + "add"):
        if message.author.guild_permissions.manage_channels: # If the author has the "manage channels" permission
             # Look through all the channels and see if it's already added
            mycursor.execute("SELECT * FROM allowed_channels WHERE channel_id = " + str(message.channel.id)) 
            myresult = mycursor.fetchone()
            if(myresult == None): # Essentially saying "if the channel isn't in the database"
                sql = "INSERT INTO allowed_channels (channel_id, allowed) VALUES (%s, %s)"
                val = (str(message.channel.id), 1)
                mycursor.execute(sql, val)
                mydb.commit() # Push the changes to the database
                # Also, f strings help a lot with not having to use + prefix + all the time.
                await message.channel.send(f"This channel will now be registered by the bot to talk in. To undo this, run `{prefix}remove` in the same channel.")
            elif(myresult[2] == 1):
                await message.channel.send(f"Sorry, this channel is already registered.")
                return
            else: # If the channel was added before but needs to be re-registered
                await message.channel.send(f"This channel has been re-registered for the bot to talk in. To undo this again, run `{prefix}remove` in the same channel.")
                mycursor.execute("UPDATE allowed_channels SET allowed = 1 WHERE channel_id = " + str(message.channel.id))
                mydb.commit()
                return
            return
        else: # If this user does not have the permissions needed.
            await message.channel.send(f"Sorry, you need the `MANAGE_CHANNELS` permission to do that. If you believe this is a mistake, please contact <@{owner_id}>.")


    if(msg == prefix + "remove"):
        if message.author.guild_permissions.manage_channels:
            mycursor.execute("UPDATE allowed_channels SET allowed = 0 WHERE channel_id = " + str(message.channel.id)) # Does not return an error if the channel doesn't exist in the database.
            mydb.commit()
            await message.channel.send("This channel is no longer registered by the bot to talk in. To undo this, run `{prefix}add` in the same channel.")
            return
        else:
            await message.channel.send(f"Sorry, you need the `MANAGE_CHANNELS` permission to do that. If you believe this is a mistake, please contact <@{owner_id}>.")
    
    mycursor.execute("SELECT * FROM allowed_channels WHERE channel_id = " + str(message.channel.id))
    myresult = mycursor.fetchone() # Get the information about the current channel.
    try:
        global queue
        if(message.author.id in queue):
            return
        if(myresult[2] != 0): # If it can go in the channel
            mycursor.execute("SELECT * FROM messages WHERE original = '" + msg + "'")
            myresult = mycursor.fetchone()
            if(myresult != None):
                replies_to_use = myresult[2].split(", ")
                true_reply = random.choice(replies_to_use) # I'm deciding to use random.choice as a temporary option until I can work out a rating/reward system for the bot.
                if(validators.url(true_reply)):
                    await message.channel.send(true_reply)
                    return
                else:
                    async with message.channel.typing(): # Occasionally will duplicate the typing if server connection issues occur - EDIT: Still may happen if connection errors occur, but too a much less degree.
                        await asyncio.sleep(len(true_reply) / 10) # / 10 to make it more realistic (and faster). That means a 10 letter word would take 10 seconds to type.
                        await message.channel.send(true_reply)
                        return
            else:
                edited_msg = msg.replace(".", "").replace("?", "").replace("!", "")
                mycursor.execute("SELECT * FROM messages WHERE original = '" + edited_msg + "'")
                myresult = mycursor.fetchone()
                if(myresult != None):
                    replies_to_use = myresult[2].split(", ")
                    true_reply = random.choice(replies_to_use) # I'm deciding to use random.choice as a temporary option until I can work out a rating/reward system for the bot.
                    if(validators.url(true_reply)):
                        await message.channel.send(true_reply)
                        return
                    else:
                        async with message.channel.typing(): # Occasionally will duplicate the typing if server connection issues occur - EDIT: Still may happen if connection errors occur, but too a much less degree.
                            await asyncio.sleep(len(true_reply) / 10) # / 10 to make it more realistic (and faster). That means a 10 letter word would take 10 seconds to type.
                            await message.channel.send(true_reply)
                            return
                await message.channel.send("**REPEAT** *(what should be the response for this message?)*: " + msg)
                queue.append(message.author.id)
                def check(message):
                    return not message.author.bot
                reply = await client.wait_for('message', check=check)
                sql = "INSERT INTO messages (original, replies) VALUES (%s, %s)"
                val = (msg, reply.content.lower())
                mycursor.execute(sql, val)
                mydb.commit()
                await message.channel.send("Successfully added reply, thanks for contributing!")
                await log_channel.send("<@" + str(message.author.id) + "> added phrase \"`" + reply.content.lower() + "`\" to `" + msg + "`")
                queue.remove(message.author.id)
                return
                """
                mycursor.execute("UPDATE messages SET replies = '" + myresult[2] + ", " + reply + "' WHERE sentences = '" + filter_message(word[0]) + "'")
                mydb.commit()
                await message.channel.send("Successfully added reply, thanks for contributing!")
                await log_channel.send("<@" + str(message.author.id) + "> added phrase \"`" + filter_message(word[1]) + "`\" to `" + filter_message(word[0]) + "`")
                return
                """
        else:
            return
    except TypeError:
        return

client.run(token)
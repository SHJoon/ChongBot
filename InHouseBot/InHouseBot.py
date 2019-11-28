import discord
import os
import random

from discord.ext import commands, tasks

from cogs.WillumpCog import WillumpCog
from cogs.QueueCog import QueueCog
from cogs.MemeCog import MemeCog

# Change this to whatever prefix you'd like
prefix = "!"  # Instantiate our bot #
bot = commands.Bot(command_prefix=prefix,
                    case_insensitive=True,
                    description="Ask The_Fire_Chief/perks for any questions!")

@tasks.loop(seconds=30)
async def change_status():
    await bot.wait_until_ready()
    activities = ["Playing", "Watching", "Listening"]
    set_type = random.choice(activities)
    if set_type == "Playing":
        phrases = [
            "with Chong's feelings",
            "with Nunu",
            "Truc Simulator 2019",
            "with the boys",
            "tank-abuser meta",
            "League In-House",
            "wadetendo Garen"
        ]
        phrase = random.choice(phrases)
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.playing, name=phrase)
        )
    elif set_type == "Watching":
        phrases = [
            "WWE Smackdown",
            "Chong's toilet",
            "not much",
            "League In-House",
            "from a cave",
            "furry convention",
            "cute anime girls",
            "the boys",
            "Danny pooping",
            "chair porn",
            "RuPaul's Drag Race",
            "missed Morgana Q's"
        ]
        phrase = random.choice(phrases)
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name=phrase)
        )
    else:
        phrases = [
            "Truc yelling",
            "Worst Mecaniks reading",
            "Jackzilla casting",
            "the inner voice",
            "Fuck Truc by the Boys",
            "Boyz II Men"
        ]
        phrase = random.choice(phrases)
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name=phrase)
        )


@bot.event
async def on_ready():
    print(bot.user.name)
    print(bot.user.id)
    #I want to get notified when the bot resets
    user = bot.get_user(219726815663620096)
    await user.send('Bot has been reset.')
    change_status.start()

def levenshtein(msg1, msg2):
    rows = len(msg1) + 1
    cols = len(msg2) + 1
    distance = [[0 for x in range(cols)] for x in range(rows)]
    # Populate matrix of zeros with the indices of each character of both strings
    for i in range(1, rows):
        for k in range(1,cols):
            distance[i][0] = i
            distance[0][k] = k

    # Compute the cost of deletions,insertions and/or substitutions    
    for col in range(1, cols):
        for row in range(1, rows):
            if msg1[row-1] == msg2[col-1]:
                cost = 0 # If the characters are the same in the two strings in a given position [i,j] then the cost is 0
            else:
                cost = 1
            distance[row][col] = min(distance[row-1][col] + 1,      # Cost of deletions
                                 distance[row][col-1] + 1,          # Cost of insertions
                                 distance[row-1][col-1] + cost)     # Cost of substitutions
    return distance[row][col]

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    # Delete white spaces from the beginning and the end
    message_strip = message.content.strip()
    # Delete ALL white spaces
    new_message = message_strip.replace(" ", "")
    # Capitalize the message for easier comparison
    new_message_upper = new_message.upper()
    if new_message_upper.startswith("HTOWN"):
        if(levenshtein(new_message_upper, "HTOWNLET'SGETIT!") <= 2):
            await message.add_reaction("\U0001F680")
            await message.add_reaction("\U0001F1FC")
    elif message.content.upper() == "W":
        await message.add_reaction("\U0001F1FC")
    elif "smH" in message.content:
        await message.add_reaction("\U0001F1F8")
        await message.add_reaction("\U0001F1F2")
        await message.add_reaction("\U0001F1ED")
    elif message.content.upper() == "L":
        await message.add_reaction("\U0001F1F1")
    elif message.content.upper() == "F":
        await message.add_reaction("\U0001F1EB")
    elif new_message_upper.startswith(("HI","HELLO","HERRO","HEY","HOWDY","GREETINGS","WHATSUP","SUP")):
        if message.author.id == 132709848864391170:
            await message.delete()
            await message.channel.send("SHUT UP TRUC")
    else:
        await bot.process_commands(message)

# roles = {emoji_id:role_id, role_sub_id}
roles = {649426239706234886:[569662747915321344, 569978007591190539],# Top
649426253056573450:[569662812344025089, 569978157663387658],# Jungle
649426225961500713:[569662844556148741, 569977972929462283],# Mid
649463087476375573:[569662919055245312, 569977902993506305],# Bot
649426197918515211:[569662971484176395, 569978337502691333],# Support
649426272933642240:[569663143786184727, 569980965582012416]# Fill
}

main_role_msg_id = 649464520179187765
sub_role_msg_id = 649464528102490123

@bot.event
async def on_raw_reaction_add(reaction):
    if reaction.user_id == bot.user.id:
        return
    if not reaction.emoji.id in roles:
        return
    
    guild = await bot.fetch_guild(reaction.guild_id)
    user = await guild.fetch_member(reaction.user_id)

    if reaction.message_id == main_role_msg_id:
        emojiID = roles.get(reaction.emoji.id)
        id = emojiID[0]
        await user.add_roles(guild.get_role(id))
    elif reaction.message_id == sub_role_msg_id:
        emojiID = roles.get(reaction.emoji.id)
        id = emojiID[1]
        await user.add_roles(guild.get_role(id))
    else:
        return

@bot.event
async def on_raw_reaction_remove(reaction):
    if reaction.user_id == bot.user.id:
        return
    if not reaction.emoji.id in roles:
        return
    
    guild = await bot.fetch_guild(reaction.guild_id)
    user = await guild.fetch_member(reaction.user_id)

    if reaction.message_id == main_role_msg_id:
        emojiID = roles.get(reaction.emoji.id)
        id = emojiID[0]
        await user.remove_roles(guild.get_role(id))
    elif reaction.message_id == sub_role_msg_id:
        emojiID = roles.get(reaction.emoji.id)
        id = emojiID[1]
        await user.remove_roles(guild.get_role(id))
    else:
        return

token = None
creds = None

if "BOT_KEY" in os.environ:
    token = os.environ["BOT_KEY"]
    print("Using environment var for key")
elif os.path.isfile("key"):
    print("Using file for key")
    with open("key", "r") as f:
        token = f.read().strip().strip("\n")

# Add in our cogs
bot.add_cog(WillumpCog(bot))
bot.add_cog(QueueCog(bot))
bot.add_cog(MemeCog(bot))

if "GOOGLE_OAUTH_JSON" in os.environ:
    from cogs.LeagueCog import LeagueCog
    bot.add_cog(LeagueCog(bot))
else:
    print("No relevant file found. LeagueCog is disabled.")

if token is not None:
    bot.run(token)
else:
    print("Failed to find token in `key` file or `BOT_KEY` environment variable")

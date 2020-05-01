import discord
import os
import random

from discord.ext import commands, tasks

from cogs.WillumpCog import WillumpCog
from cogs.QueueCog import QueueCog
from cogs.MemeCog import MemeCog
from cogs.LeagueCog import LeagueCog
from cogs.MusicCog import MusicCog

# Change this to whatever prefix you'd like
prefixes = ["!", "."]
# Instantiate our bot
bot = commands.Bot(command_prefix=prefixes,
                    case_insensitive=True,
                    )

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

@tasks.loop(hours=10, minutes=30)
async def say_phrases():
    await bot.wait_until_ready()
    phrases = ["troi duc oi", "What a champ", "Bet", "die duck guy",
    "<:grabhandL:668730434984869888> <:thereallickle:670051941296111616> <:grabhandR:668730456333877248>"]
    channel = bot.get_channel(611413760266993675)
    phrase = random.choice(phrases)
    await channel.send(phrase)

@bot.event
async def on_ready():
    print(bot.user.name)
    print(bot.user.id)
    change_status.start()

    # Disabled, as it got a little spammy
    # say_phrases.start()

    # I want to get notified when the bot resets
    user = bot.get_user(219726815663620096)
    await user.send('Bot has been reset.')
    channel = bot.get_channel(569974088932655134)
    await channel.send('Bot has been reset.')

async def levenshtein(msg1, msg2):
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

truc_words = ["DN", "NUTS"]

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
    user = bot.get_user(219726815663620096)
    if new_message_upper.startswith("HTOWN"):
        if(await levenshtein(new_message_upper, "HTOWNLET'SGETIT!") <= 2):
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
            await user.send(f"Truc said: {message.content}")
            await message.delete()
            await message.channel.send("SHUT UP TRUC")
    elif "DEEZ" in message.content.upper():
        if message.author.id == 132709848864391170:
            await user.send(f"Truc said: {message.content}")
            await message.delete()
            await message.channel.send("SHUT UP TRUC")
    # Capitalize the message for Truc filter
    message_split_upper = message.content.upper().split()
    for word in truc_words:
        if word in message_split_upper:
            if message.author.id == 132709848864391170:
                await user.send(f"Truc said: {message.content}")
                await message.delete()
                await message.channel.send("SHUT UP TRUC")
                break
    await bot.process_commands(message)

# roles = {emoji_id:role_id, role_sub_id}
roles = {649426239706234886:[569662747915321344, 569978007591190539],# Top
649426253056573450:[569662812344025089, 569978157663387658],# Jungle
649426225961500713:[569662844556148741, 569977972929462283],# Mid
649463087476375573:[569662919055245312, 569977902993506305],# Bot
649426197918515211:[569662971484176395, 569978337502691333],# Support
649426272933642240:[569663143786184727, 569980965582012416] # Fill
}

extra_roles = {699173571783819354:699171129306382386,# Valorant
699173548065030184:699171219806617651,# TFT
699173955939991572:699171346071945216,# Tabletop Sim
699173595070595142:699171917168377867,# CS:GO
699174587996307969:699174228443922462,# Melee
699175867833909268:699171856334192640,# Animal Crossing
700461362006196257:700461216383893504 # Minecraft
}

main_role_msg_id = 649464520179187765
sub_role_msg_id = 649464528102490123
extra_role_msg_id = 699179766271443044

# queue_emojis = [join_id, drop_id]
queue_emojis = [668410201099206680,668410288667885568]

@bot.event
async def on_raw_reaction_add(reaction):
    if reaction.user_id == bot.user.id:
        return
    if not ((reaction.emoji.id in roles) or (reaction.emoji.id in queue_emojis) or (reaction.emoji.id in extra_roles)):
        return
    
    guild = bot.get_guild(reaction.guild_id)
    user = guild.get_member(reaction.user_id)
    channel = bot.get_channel(reaction.channel_id)
    message = await channel.fetch_message(reaction.message_id)
    ctx = await bot.get_context(message)

    if reaction.emoji.id == 668410201099206680:
        await ctx.invoke(bot.get_command("forceadd"),user)
        return
    elif reaction.emoji.id == 668410288667885568:
        await ctx.invoke(bot.get_command("forceremove"),user)
        return

    if reaction.message_id == main_role_msg_id:
        emojiID = roles.get(reaction.emoji.id)
        id = emojiID[0]
        await user.add_roles(guild.get_role(id))
    elif reaction.message_id == sub_role_msg_id:
        emojiID = roles.get(reaction.emoji.id)
        id = emojiID[1]
        await user.add_roles(guild.get_role(id))
    elif reaction.message_id == extra_role_msg_id:
        emojiID = extra_roles.get(reaction.emoji.id)
        await user.add_roles(guild.get_role(emojiID))
    else:
        return

@bot.event
async def on_raw_reaction_remove(reaction):
    if reaction.user_id == bot.user.id:
        return
    if not ((reaction.emoji.id in roles) or (reaction.emoji.id in extra_roles)):
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
    elif reaction.message_id == extra_role_msg_id:
        emojiID = extra_roles.get(reaction.emoji.id)
        await user.remove_roles(guild.get_role(emojiID))
    else:
        return

token = None

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
bot.add_cog(LeagueCog(bot))
bot.add_cog(MusicCog(bot))

if ("GOOGLE_OAUTH_JSON" in os.environ) or (os.path.isfile("InHouseTest.json")):
    from cogs.StreamCog import StreamCog
    bot.add_cog(StreamCog(bot))
    from cogs.MoneyCog import MoneyCog
    bot.add_cog(MoneyCog(bot))
else:
    print("No relevant file found. StreamCog/MoneyCog is disabled.")

if token is not None:
    bot.run(token)
else:
    print("Failed to find token in `key` file or `BOT_KEY` environment variable")

import discord
import os
import random
from discord.ext import commands, tasks


from cogs.WillumpCog import WillumpCog
from cogs.QueueCog import QueueCog
from cogs.LeagueCog import LeagueCog

# Change this to whatever prefix you'd like
prefix = "!"  # Instantiate our bot #
bot = commands.Bot(command_prefix=prefix)


@tasks.loop(seconds=30)
async def change_status():
    await bot.wait_until_ready()
    set_type = random.randint(0, 2)
    if set_type == 0:
        phrases = [
            "with Chong's feelings",
            "with Nunu",
            "Truc Simulator 2019",
            "with the boys",
            "tank-abuser meta",
            "League In-House",
            "wadetendo Garen",
        ]
        phrase = random.choice(phrases)
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.playing, name=phrase)
        )
    elif set_type == 1:
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
            "missed Morgana Q's",
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
            "Boyz II Men",
        ]
        phrase = random.choice(phrases)
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name=phrase)
        )


@bot.event
async def on_ready():
    print(bot.user.name)
    print(bot.user.id)
    change_status.start()


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content.upper() == "W":
        await message.add_reaction("\U0001F1FC")
    elif message.content == "smH":
        await message.add_reaction("\U0001F1F8")
        await message.add_reaction("\U0001F1F2")
        await message.add_reaction("\U0001F1ED")
    elif message.content.upper() == "H TOWN LET'S GET IT!":
        await message.add_reaction("\U0001F680")
        await message.add_reaction("\U0001F1FC")
    elif message.content.upper() == "L":
        await message.add_reaction("\U0001F1F1")
    elif message.content.upper() == "F":
        await message.add_reaction("\U0001F1EB")
    else:
        await bot.process_commands(message)


token = None
api_key = None

if "BOT_KEY" in os.environ:
    token = os.environ["BOT_KEY"]
    print("Using environment var for key")
elif os.path.isfile("key"):
    print("Using file for key")
    with open("key", "r") as f:
        token = f.read().strip().strip("\n")

if api_key is None:
    print(
        "Could not find api_key credentials for backend, launching with those features disabled"
    )

# Add in our cogs
#
bot.add_cog(WillumpCog(bot))
bot.add_cog(QueueCog(bot))
bot.add_cog(LeagueCog(bot))

if token is not None:
    bot.run(token)
else:
    print("Failed to find token in `key` file or `BOT_KEY` environment variable")

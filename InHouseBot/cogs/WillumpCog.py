import random
import itertools
import discord
import asyncio
from discord.ext import commands
import heapq

# Figuring out how the !help command gets automatically registered and invoked
# is actually a good excercise in reading source code Howard

class AliasHelpCommand(commands.DefaultHelpCommand):
    def __init__(self):
        super().__init__(
            command_attrs={"name": "help", "aliases": ["commands", "command"]}
        )

class WillumpCog(commands.Cog):
    def __init__(self, bot):
        bot.help_command = AliasHelpCommand()
        bot.help_command.cog = self

        self.flip_count = 0
        # Set up our typo structs for lulcaptains()
        self.keyboard_array = [
            # A string is just an array of characters
            "1234567890-=",
            "qwertyuiop[",
            "asdfghjkl;'",
            "zxcvbnm,./",
        ]
        # Pog syntax
        self.lookup_table = {
            letter: [row_idx, col_idx]
            for row_idx, row in enumerate(self.keyboard_array)
            for col_idx, letter in enumerate(row)
        }
        self.typo_replace_chance = 10
        self.typo_add_chance = 10
        self.bot = bot

    @commands.command(pass_context=True)
    async def flip(self, ctx):
        """ Heads or Tails """
        flip = ["Heads", "Tails"]
        ranflip = random.choice(flip)
        if random.randrange(50) == 49:
            ranflip = "Sides"
            self.flip_count = 0
        elif self.flip_count == 50:
            ranflip = "Sides"
            self.flip_count = 0

        embed = discord.Embed(title=ranflip)

        if ranflip == "Heads":
            pics_url = [
                "https://cdn.discordapp.com/attachments/688598474861707304/689666020834803712/unknown.png",
                "https://cdn.discordapp.com/attachments/602376454491078659/659905323217322021/image0.jpg"
            ]
            ranpic = random.choice(pics_url)
            embed.set_image(url=ranpic)
            embed.colour = discord.Colour.orange()
        elif ranflip == "Tails":
            pics_url = [
                "https://cdn.discordapp.com/attachments/623390018991292426/681340369912201264/tails_gif.gif",
                "https://cdn.discordapp.com/attachments/623390018991292426/680682916220895276/unknown.png",
                "https://cdn.discordapp.com/attachments/663534641164320801/663956797048225804/unknown.png"
            ]
            # "https://i.imgur.com/grTqgib.png"
            # "https://media0.giphy.com/media/uWcNWtfqzySDYqkORw/source.gif"
            ranpic = random.choice(pics_url)
            embed.set_image(url=ranpic)
            embed.colour = discord.Colour.blue()
        else:
            embed.set_image(
                url="https://cdn.discordapp.com/attachments/224084353779630080/674848939085922364/EQEaufMUUAIM0aW.png"
                # "https://i.imgur.com/P3EbqRH.gif"
                # "https://lolskinshop.com/wp-content/uploads/2015/04/Poppy_2.jpg"
            )
            embed.colour = discord.Colour.green()
        
        self.flip_count += 1
        await ctx.send(embed=embed)
    
    @commands.command(hidden = True)
    async def massflip(self, ctx, num:int):
        """ Mini command to flip many times """
        member = ctx.message.author
        if num > 50000:
            await ctx.send(f"{member.mention} YOU MONKEY TRYING TO BREAK THE BOT, 50000 FLIPS OR LESS ONLY")
            return
        flip = ["Heads", "Tails"]
        head_count = 0
        tail_count = 0
        for _ in range(num):
            ranflip = random.choice(flip)
            if ranflip == "Heads":
                head_count += 1
            else:
                tail_count += 1
        await ctx.send(f"Heads:{head_count}\nTails:{tail_count}")

    @commands.command(pass_context=True)
    async def choose(self, ctx, *choices: str):
        """ Randomly choose from your own provided list of choices """
        await ctx.send(random.choice(choices))

    @commands.command()
    async def roll(self, ctx, dice: str):
        """ AdX format only(A=number of die, X=number of faces) """
        try:
            rolls, limit = map(int, dice.split("d"))
        except Exception:
            await ctx.send("AdX format only(A=number of die, X=number of faces)")
            return

        result = ", ".join(str(random.randint(1, limit)) for r in range(rolls))
        await ctx.send(result)
    
    @commands.command()
    async def timer(self, ctx, sec: int):
        """ Set a timer (Only in seconds) """
        author = ctx.message.author
        await asyncio.sleep(sec)
        await ctx.send(f"Time's up!!! {author.mention}")

    async def generate_typo(self, letter):
        """ Typo helper function """
        # Remember our case
        holdShift = letter.isupper()
        # Standardize
        letter = letter.lower()
        row, col = self.lookup_table[letter]

        # Handle our edge cases for when we can't go up (above our row idx)
        # or past the end of our row charecters  (col idx)
        # Worth looking into this and figuring out whats going on! I wrote it as
        # if I would normally write code so a lot of new concepts
        new_row = random.choice(
            [
                idx
                for idx in (lambda row=row: [row + i for i in range(-1, 2)])()
                if idx >= 0 and idx < len(self.keyboard_array)
            ]
        )

        new_col = random.choice(
            [
                idx
                for idx in (lambda col=col: [col + i for i in range(-1, 2)])()
                if idx >= 0 and idx < len(self.keyboard_array[row])
            ]
        )

        typo = self.keyboard_array[new_row][new_col]
        return typo.upper() if holdShift else typo

    @commands.command(hidden=True)
    async def typo(self, ctx, chance_replace: int, chance_add: int):
        """ Modify settings for lulcaptains typo """
        if not (0 <= chance_replace <= 100 and 0 <= chance_add <= 100):
            return ctx.send("The chances have to be between 0~100%!")
        
        await ctx.send(
            f"lulcaptains settings:\
        \nReplace chance set to {chance_replace}%.\
        \nAdd chance set to {chance_add}%."
        )
        self.typo_replace_chance = chance_replace - 1
        self.typo_add_chance = chance_add - 1

    @commands.command(pass_context=True)
    async def captains(self, ctx):
        """ Randomizes captains list from General Voice channel"""
        members = ctx.message.author.voice.channel.members
        random.shuffle(members)
        message = ""
        for place, member in enumerate(members):
            name = member.nick if member.nick else member.name
            message += f"**#{place+1}** : {name}\n"
        if not message:
            message = "No voice lobby for captains draft"
        await ctx.send(message)

    @commands.command(pass_context=True)
    async def lulcaptains(self, ctx):
        """ Like !captains, but like when Danny drinks"""
        members = ctx.message.author.voice.channel.members
        random.shuffle(members)
        message = ""

        for place, member in enumerate(members):
            name = member.nick if member.nick else member.name
            danny_name = ""
            # Lets typo our name
            for letter_substring in ["".join(g) for _, g in itertools.groupby(name)]:
                # No support for shift+char typos or other non present keys atm, so just pass them to stop
                # us key error indexing on our table
                if letter_substring[0].lower() not in self.lookup_table:
                    danny_name += letter_substring
                elif (
                    random.randrange(100) <= self.typo_replace_chance
                ):  # 10% to REPLACE w/ typo by default
                    typo = await self.generate_typo(letter_substring[0])  # Get the typo
                    danny_name += typo * len(letter_substring)
                elif (
                    random.randrange(100) <= self.typo_add_chance
                ):  # 10% to ADD w/ typo by default
                    # I only want to add like 1 extra character, so don't need
                    # to handle sequences!
                    typo = await self.generate_typo(letter_substring[0])
                    danny_name += letter_substring + typo
                else:
                    danny_name += letter_substring  # this already is stretched out

            message += f"**#{place+1}** : {danny_name}\n"

        if not message:
            message = "No voice lobby for captains draft"

        await ctx.send(message)
    
    @commands.command(aliases=["val"])
    async def valorant(self, ctx):
        """ Choose a random valorant agent. """
        agents = [
            "Breach",
            "Brimstone",
            "Cypher",
            "Jett",
            "Killjoy",
            "Omen", 
            "Phoenix",
            "Raze",
            "Reyna",
            "Sage",
            "Sova",
            "Skye",
            "Viper",
            "Yoru"
            ]
        
        agent_msg = await ctx.send(random.choice(agents))
        await asyncio.sleep(180)
        await agent_msg.delete()
        await ctx.message.delete()
    
    @commands.command()
    async def sd(self, ctx, *, msg):
        """ Only Danny and I know what this does """
        channel = self.bot.get_channel(569646728224178184)
        await channel.send(msg)
    
    @commands.command(aliases = ["reward", "rewards"])
    async def cashout(self, ctx):
        """ Shows what you can spend NunuBucks on """
        await ctx.send(
            "You can cashout NunuBucks for the following:\
            \n30,000 NB - Custom emote for the server\
            \n50,000 NB - Meme command(image/text format)\
            \n70,000 ~ 150,000 NB - Utility command (price depends on the difficulty of implementation)\
            \n\nMessage one of the mods for the request!"
        )

    @commands.command(hidden=True)
    async def ilovdandan(self, ctx):
        # Command to change "React for role" feature message
        guild = ctx.guild
        try:
            chn = guild.get_channel(649323021433307147)
            msg = await chn.fetch_message(699179766271443044)
            await msg.edit(
                content="React to any of your additional interests!\
                    \n<:AnimalCrossing:699175867833909268> Animal Crossing\
                    \n<:csgo:699173595070595142> CS:GO\
                    \n<:minecraft:700461362006196257> Minecraft\
                    \n<:meleefox:699174587996307969> Super Smash Bros. Melee\
                    \n<:d20:699173955939991572> Tabletop Simulator\
                    \n<:tft:699173548065030184> TFT\
                    \n<:valorant:699173571783819354> Valorant\
                    \n <:Gamer:736072194056257537> Gamer (Choose this role if you would like to be pinged for norm/casual League games)\n\
                    \n**NOTE** Choose as many roles as you want!")
            await msg.add_reaction("<:AnimalCrossing:699175867833909268>")
            await msg.add_reaction("<:csgo:699173595070595142>")
            await msg.add_reaction("<:minecraft:700461362006196257>")
            await msg.add_reaction("<:meleefox:699174587996307969>")
            await msg.add_reaction("<:d20:699173955939991572>")
            await msg.add_reaction("<:tft:699173548065030184>")
            await msg.add_reaction("<:valorant:699173571783819354>")
            await msg.add_reaction("<:Gamer:736072194056257537>")
        except:
            await ctx.send("Doesn't work in this server.")

    @commands.command(hidden=True)
    async def mik(self, ctx):
        self.mik_embed = discord.Embed(
            title="Satoru Gojou",
            description="Jujutsu Kaisen\n\
                **746**<:kakera:815692761449103371>"
        )
        self.mik_embed.set_image(url="https://media.discordapp.net/attachments/472313197836107780/584195806563663882/SzcapaF.png")
        self.mik_embed.color = discord.Color.green()

        # test_channel_id = 622142949307973642
        waifu_channel_id = 814386182343491584
        channel = ctx.guild.get_channel(waifu_channel_id)
        # channel = ctx.guild.get_channel(test_channel_id)

        self.msg = await channel.send(embed=self.mik_embed)
        await self.msg.add_reaction("<:revolvingHearts:815701810207391797>")
    
    @commands.command(hidden=True)
    async def edit_mik(self, ctx):
        self.mik_embed.set_image(url="https://i.imgur.com/B0IVc3x.gif")
        self.mik_embed.color = discord.Color.dark_red()

        # test_channel_id = 622142949307973642
        waifu_channel_id = 814386182343491584
        channel = ctx.guild.get_channel(waifu_channel_id)
        # channel = ctx.guild.get_channel(test_channel_id)

        await self.msg.edit(embed=self.mik_embed)
        
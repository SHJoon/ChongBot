import random
import itertools
import discord
from discord.ext import commands

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

    @commands.command(pass_context=True)
    async def fuckchong(self, ctx):
        """ Self explanatory """
        msg = await ctx.send(f"FUCK CHONG")
        await msg.add_reaction("\U0001F1EB")
        await msg.add_reaction("\U0001F1FA")
        await msg.add_reaction("\U0001F1E8")
        await msg.add_reaction("\U0001F1F0")
        await msg.add_reaction("\U000021AA")
        await msg.add_reaction("\U0001F1ED")
        await msg.add_reaction("\U0001F1F4")
        await msg.add_reaction("\U0001F1F3")
        await msg.add_reaction("\U0001F1EC")
        emoji = "<:FuckChong:598605265641930757>"
        await msg.add_reaction(emoji)

    @commands.command(pass_context=True)
    async def ass(self, ctx):
        """ It is the truth """
        await ctx.send(f"CHONG IS AN ASS EATER")

    @commands.command(pass_context=True)
    async def grime(self, ctx):
        """ Important slice of in-house history... """
        await ctx.send(
            f"On May 6th, 2019, Chong invited an ex-LCS player to the server..."
        )

    @commands.command(pass_context=True)
    async def morg(self, ctx):
        """ Everyone misses a skill shot occasionally, even you """
        await ctx.send(
            f"https://media.discordapp.net/attachments/569646728224178184/598615204288397501/unknown.png?width=1250&height=676"
        )

    @commands.command(pass_context=True)
    async def boys(self, ctx):
        """ The boys are back in town """
        await ctx.send(f"https://i.imgflip.com/360ktl.jpg")

    @commands.command(pass_contect=True)
    async def boys2(self, ctx):
        """ The boys are back in town again """
        await ctx.send("https://i.imgflip.com/36j064.jpg")

    @commands.command(pass_context=True)
    async def cool(self, ctx):
        """ See if you are cool or not! """
        author = ctx.message.author
        # Chong's server ID
        if author.id == 172899191998251009:
            await ctx.send(f"You're grimey")
        else:
            await ctx.send(f"You're cool! {author.mention}")

    @commands.command(pass_context=True)
    async def ape(self, ctx):
        """ Current state of inhouse drafts """
        await ctx.send(
            "https://media.discordapp.net/attachments/569646728224178184/611036013715783710/In-House_meme.png?width=902&height=866"
        )

    @commands.command(pass_context=True)
    async def ksaper(self, ctx):
        """ Stats telling me no, but my body telling me YES """
        await ctx.send(f"beep boop :robot: 4fun4 :robot: beep boop")

    @commands.command()
    async def flames(self, ctx):
        """ 'ConsTRUCtive flaming """
        await ctx.send("https://i.imgflip.com/38i4t9.jpg")

    @commands.command()
    async def wade(self, ctx):
        """ Self-loathing tank abuse """
        await ctx.send(
            f"im wade top lane blows dick and i dont think anyone can be good at league of legends except me"
        )

    @commands.command()
    async def danny(self, ctx):
        """ KING """
        await ctx.send(f"https://i.imgflip.com/384zeu.jpg")

    @commands.command(pass_context=True)
    async def flip(self, ctx):
        """ Heads or Tails """
        flip = ["Heads", "Tails"]
        ranflip = random.choice(flip)

        embed = discord.Embed(title=ranflip)

        if ranflip == "Heads":
            # embed.set_image(
            #     url="https://nexus.leagueoflegends.com/wp-content/uploads/2018/08/Nunu_Bot_fqvx53j9ion1fxkr34ag.gif"
            # )
            embed.set_image(url="https://i.imgur.com/lDlR54a.gif")
            embed.colour = discord.Colour.orange()
        else:
            embed.set_image(
                url="https://media0.giphy.com/media/3oz8xCXbQDReF34WWs/giphy-downsized.gif"
            )
            embed.colour = discord.Colour.blue()

        # https://nexus.leagueoflegends.com/wp-content/uploads/2018/08/Nunu_Bot_fqvx53j9ion1fxkr34ag.gif
        # https://media0.giphy.com/media/3oz8xCXbQDReF34WWs/giphy-downsized.gif
        # https://www.ssbwiki.com/images/b/bf/Fox_SSBM.jpg
        # https://www.ssbwiki.com/images/1/17/Falco_SSBM.jpg
        # https://lolskinshop.com/wp-content/uploads/2015/04/Poppy_2.jpg
        # https://2.bp.blogspot.com/-_1l8obImQmA/V3F9Z8MV3_I/AAAAAAAA8FI/Kcj-ALPCPoY5cTeaAgFtgYIg6qihz4XBgCLcB/s1600/Taric_Splash_4.jpg

        await ctx.send(embed=embed)

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

    @commands.command(pass_context=True)
    async def typo(self, ctx, chance_replace: int, chance_add: int):
        """ Modify settings for lulcaptains typo"""
        if (
            (chance_replace > 100)
            or (chance_replace < 0)
            or (chance_add > 100)
            or (chance_add < 0)
        ):
            await ctx.send("The chances have to be between 0~100%!")
        else:
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
        members = discord.utils.get(
            ctx.guild.channels, name="General", type=discord.ChannelType.voice
        ).members
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
        members = discord.utils.get(
            ctx.guild.channels, name="General", type=discord.ChannelType.voice
        ).members
        random.shuffle(members)
        message = ""

        for place, member in enumerate(members):
            name = member.nick if member.nick else member.name
            danny_name = ""
            # Lets typo our name
            for letter_substring in ["".join(g) for _, g in itertools.groupby(name)]:
                # No support for shift+char typos or other non present keys atm, so just pass them to stop
                # us key error indexing on our table
                if letter_substring[0] not in self.lookup_table:
                    danny_name += letter_substring
                elif (
                    random.randrange(100) <= self.typo_replace_chance
                ):  # 10% to REPLACE w/ typo by default
                    typo = await self.generate_typo(letter_substring[0])  # Get the typo
                    danny_name += typo * len(letter_substring)  #
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

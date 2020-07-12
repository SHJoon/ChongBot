import discord
import random
from discord.ext import commands

class MemeCog(commands.Cog):
    def __init__(self, bot):
        self.chongID = 172899191998251009
        self.trucID = 132709848864391170
        self.ksaperID = 131626920738684928
        self.ethanID = 303289460970487811
        self.dareID = 141733872315400193
        self.showernum = 10
    
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
    
    @commands.command()
    async def fuckdare(self, ctx):
        """ Please """
        msg = await ctx.send(f"FUCK DARE")
        await msg.add_reaction("\U0001F1EB")
        await msg.add_reaction("\U0001F1FA")
        await msg.add_reaction("\U0001F1E8")
        await msg.add_reaction("\U0001F1F0")

        await msg.add_reaction("\U0001F1E9")
        await msg.add_reaction("\U0001F1E6")
        await msg.add_reaction("\U0001F1F7")
        await msg.add_reaction("\U0001F1EA")

        emoji = "<:DareW:679993204589854769>"
        await msg.add_reaction(emoji)
    
    @commands.command()
    async def fucktruc(self,ctx):
        """ He deserves it """
        msg = await ctx.send("FUCK TRUC")
        await msg.add_reaction("\U0001F1EB")
        await msg.add_reaction("\U0001F1FA")
        await msg.add_reaction("\U0001F1E8")
        await msg.add_reaction("\U0001F1F0")

        await msg.add_reaction("\U0001F1F9")
        await msg.add_reaction("\U0001F1F7")
        await msg.add_reaction("\U000026CE")
        await msg.add_reaction("\U000021AA")

        await msg.add_reaction("\U0001F69A")
    
    @commands.command(aliases=["gdiethan","goddamnit","goddamnitethan"])
    async def gdi(self,ctx):
        """ Goddamn it """
        msg = await ctx.send("GOD DAMN IT ETHAN")
        await msg.add_reaction("\U0001F1EC")
        await msg.add_reaction("\U0001F1E9")
        await msg.add_reaction("\U0001F1EE")
        await msg.add_reaction("\U0001F1EA")
        await msg.add_reaction("\U0001F1F9")
        await msg.add_reaction("\U0001F1ED")
        await msg.add_reaction("\U0001F1E6")
        await msg.add_reaction("\U0001F1F3")
        await msg.add_reaction("\U0001F926")

    @commands.command(hidden=True)
    async def fuckme(self, ctx):
        """ Chong, Truc, and Ethan(Valley) use only """
        author = ctx.message.author
        if author.id == self.chongID:
            await ctx.invoke(self.fuckchong)
        elif author.id == self.trucID:
            await ctx.invoke(self.fucktruc)
        elif author.id == self.ethanID:
            await ctx.invoke(self.gdi)
        elif author.id == self.dareID:
            await ctx.invoke(self.fuckdare)
        else:
            return
    
    @commands.command(hidden=True)
    async def ass(self, ctx):
        """ It is the truth """
        await ctx.send(f"CHONG IS AN ASS EATER")

    @commands.command(hidden=True)
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

    @commands.command(hidden=True)
    async def boys(self, ctx):
        """ The boys are back in town """
        await ctx.send(f"https://i.imgflip.com/360ktl.jpg")

    @commands.command(hidden=True)
    async def boys2(self, ctx):
        """ The boys are back in town again """
        await ctx.send("https://i.imgflip.com/36j064.jpg")

    @commands.command(hidden=True)
    async def cool(self, ctx):
        """ See if you are cool or not! """
        author = ctx.message.author

        if author.id == self.chongID:
            await ctx.send(f"You're grimey")
        elif author.id == self.trucID:
            await ctx.send(f"You're a dad")
        elif author.id == self.ksaperID:
            await ctx.send(f"You're 4chill4")
        else:
            await ctx.send(f"You're cool! {author.mention}")

    @commands.command(hidden=True)
    async def ape(self, ctx):
        """ Current state of inhouse drafts """
        await ctx.send(
            "https://media.discordapp.net/attachments/569646728224178184/611036013715783710/In-House_meme.png?width=902&height=866"
        )
    
    @commands.command()
    async def amar(self, ctx):
        """ 4amar """
        embed = discord.Embed(colour=discord.Colour.purple())
        embed.set_image(url="https://cdn.discordapp.com/attachments/219726377648128001/731764897804714024/wait_its_all.jpg")
        await ctx.send(embed=embed)
    
    @commands.command(hidden=True)
    async def anees(self, ctx):
        """ FREE PALASTINE """
        await ctx.send(
            f"https://cdn.discordapp.com/attachments/629458377193422849/651856430365802532/image0.jpg"
        )
        
    @commands.command(hidden=True)
    async def danny(self, ctx):
        """ KING """
        await ctx.send(
            f"https://i.imgflip.com/384zeu.jpg"
        )
    
    @commands.command(aliases=["shower"])
    async def dare(self, ctx):
        """ How long has it been since Dare showered? """
        self.showernum += random.randint(10, 100)
        if random.randrange(50) == 49:
            self.showernum = 0
        await ctx.send(f"It has been {self.showernum} days since Dare showered...")

    @commands.command(aliases=["boobsareass", "evelyn"])
    async def evelynn(self, ctx):
        """ hmm... """
        embed = discord.Embed(colour=discord.Colour.purple())
        embed.set_image(url="https://cdn.discordapp.com/attachments/629458377193422849/660287429680562176/unknown.png")
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def ksaper(self, ctx):
        """ Who the hell """
        embed = discord.Embed(colour=discord.Colour.purple())
        embed.set_image(url="https://cdn.discordapp.com/attachments/569646728224178184/651570847546343424/4c856b92b38200175aa1c923ed729021.png")
        await ctx.send(f"Did some bimbo 1st, 2nd, or 3rd pick Ksaper?!?!",embed=embed)

    @commands.command(aliases=["flame"],hidden=True)
    async def flames(self, ctx):
        """ ConsTRUCtive flaming """
        await ctx.send(
            "https://i.imgflip.com/38i4t9.jpg"
            )
    
    @commands.command(aliases=["memes"])
    async def meme(self, ctx):
        """ Imgur link for Ethan's shops """
        await ctx.send(
            "<https://imgur.com/a/Sy65OZd>"
            )
    
    @commands.command()
    async def pinecone(self, ctx):
        """ Vincent draw a pinecone """
        embed = discord.Embed(colour=discord.Colour.dark_magenta())
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/611413760266993675/691195233349927002/unknown.png"
        )
        await ctx.send(embed=embed)
    
    @commands.command(aliases=["getfuckedtruc"])
    async def truc(self, ctx):
        """ Get fucked Truc """
        embed = discord.Embed(colour=discord.Colour.teal())
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/569646728224178184/678851818075193344/unknown.png"
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def trucard(self, ctx):
        """ Truc excuses """
        phrases = [
            '"This guy\'s deck is CRAZY!" \U00002611',
            '"My deck can\'t win against a deck like that" \U00002611',
            '"He NEEDED precisely those two cards to win" \U00002611',
            '"He topdecked the only card that could beat me" \U00002611',
            '"He had the perfect cards" \U00002611',
            '"There was nothing I could do" \U00002611',
            '"I played that perfectly" \U00002611'
        ]
        phrase = random.choice(phrases)
        await ctx.send(phrase)
    
    @commands.command()
    async def truco(self, ctx):
        """ He has become what he hates the most """
        embed = discord.Embed()
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/569646728224178184/661008639112249404/unknown.png"
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def truggered(self, ctx):
        """ Mad Truc Disease """
        embed = discord.Embed()
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/629458377193422849/657014560791724032/madtruc.gif"
        )
        await ctx.send(embed=embed)
    
    @commands.command(aliases=["uwu"])
    async def truwu(self, ctx):
        """ UwU with a touch of Truc """
        embed = discord.Embed(title="trUwU")
        embed.set_image(
            url="https://i.imgur.com/9HC22JW.png"
        )
        embed.colour = discord.Colour.orange()
        await ctx.send(embed=embed)
    
    @commands.command(aliases = ["ethan"])
    async def valley(self, ctx):
        """ Meme KING """
        await ctx.send(
            f"https://www.youtube.com/channel/UCLlFPxjfcwQAT9XWOLpi0KQ"
            )
    
    @commands.command(hidden=True)
    async def wade(self, ctx):
        """ Self-loathing tank abuse """
        await ctx.send(
            f"im wade, top lane blows dick and i dont think anyone can be good at league of legends except me"
        )

    @commands.command(aliases=["king"])
    async def wadetendo(self, ctx):
        """ WADETENDO KING """
        embed = discord.Embed(colour=discord.Colour.red())
        embed.set_image(url="https://cdn.discordapp.com/attachments/569646728224178184/672295666923601920/unknown.png")
        await ctx.send(embed=embed)
    
    @commands.command(aliases = ["wolffy", "w01ffy"])
    async def wolfy(self, ctx):
        """ Peen Queen """
        embed = discord.Embed(colour=discord.Colour.dark_teal())
        embed.set_image(url="https://cdn.discordapp.com/attachments/569646728224178184/730320894576033862/unknown.png")
        await ctx.send(embed=embed)
        
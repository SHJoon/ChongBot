import discord
from discord.ext import commands

class MemeCog(commands.Cog):
    def __init__(self, bot):
        self.chongID = 172899191998251009
        self.trucID = 132709848864391170
        self.ksaperID = 131626920738684928
    
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

    @commands.command()
    async def fuckme(self, ctx):
        """ Chong and Truc use only """
        author = ctx.message.author
        if author.id == self.chongID:
            await ctx.invoke(self.fuckchong)
        elif author.id == self.trucID:
            await ctx.invoke(self.fucktruc)
        else:
            return
    
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
        if author.id == self.chongID:
            await ctx.send(f"You're grimey")
        # Truc's server ID
        elif author.id == self.trucID:
            await ctx.send(f"You're a dad")
        elif author.id == self.ksaperID:
            await ctx.send(f"You're chillin")
        else:
            await ctx.send(f"You're cool! {author.mention}")

    @commands.command(pass_context=True)
    async def ape(self, ctx):
        """ Current state of inhouse drafts """
        await ctx.send(
            "https://media.discordapp.net/attachments/569646728224178184/611036013715783710/In-House_meme.png?width=902&height=866"
        )
    
    @commands.command()
    async def anees(self, ctx):
        """ FREE PALASTINE """
        await ctx.send(
            f"https://cdn.discordapp.com/attachments/629458377193422849/651856430365802532/image0.jpg"
        )
        
    @commands.command()
    async def danny(self, ctx):
        """ KING """
        await ctx.send(f"https://i.imgflip.com/384zeu.jpg")

    @commands.command(pass_context=True)
    async def ksaper(self, ctx):
        """ Stats telling me no, but my body telling me YES """
        await ctx.send(f"beep boop :robot: 4fun4 :robot: beep boop")

    @commands.command()
    async def flames(self, ctx):
        """ ConsTRUCtive flaming """
        await ctx.send("https://i.imgflip.com/38i4t9.jpg")
    
    @commands.command()
    async def valley(self, ctx):
        """ Meme KING """
        await ctx.send(f"https://www.youtube.com/channel/UCLlFPxjfcwQAT9XWOLpi0KQ")
    
    @commands.command()
    async def wade(self, ctx):
        """ Self-loathing tank abuse """
        await ctx.send(f"im wade, top lane blows dick and i dont think anyone can be good at league of legends except me")

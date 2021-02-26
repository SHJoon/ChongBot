import discord
from discord.ext import commands
import youtube_dl
import os
import shutil
import asyncio

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        
        if "BOT_KEY" in os.environ:
            if not discord.opus.is_loaded():
                discord.opus.load_opus('libopus.so')
        
        self.songq = []
        self.voice = None
        self.volume = 0.30
        self.volume_control = None
        self.voice_source = None
    
    async def check_q(self, ctx):
        if not self.songq:
            return
        else:
            song = self.songq.pop(0)
            song_there = os.path.isfile("song.mp3")

            if song_there:
                os.remove("song.mp3")
            
            self.voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)

            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192"
                }]
            }

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([song])
            
            for file in os.listdir("./"):
                if file.endswith(".mp3"):
                    name = file
                    os.rename(file, "song.mp3")
            
            self.voice.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: self.check_q(ctx))
            self.voice.source = discord.PCMVolumeTransformer(self.voice.source)
            self.voice.source.volume = 0.07
    
    @commands.command(hidden=True)
    async def j(self, ctx):
        """ Make bot join voice channel """
        channel = ctx.message.author.voice.channel
        self.voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)

        if self.voice and self.voice.is_connected():
            await self.voice.move_to(channel)
        else:
            self.voice = await channel.connect()
    
    @commands.command(hidden=True)
    async def l(self, ctx):
        """ Make bot leave voice channel """
        channel = ctx.message.author.voice.channel
        self.voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)

        if self.voice and self.voice.is_connected():
            await self.voice.disconnect()

    @commands.command(aliases=["p"])
    async def play(self, ctx, url: str, volume=0):
        """ Play music (Youtube link only for now) """
        async with self.lock:
            await ctx.invoke(self.j)
            song_there = os.path.isfile("song.mp3")

            try:
                if song_there:
                    os.remove("song.mp3")
            except PermissionError:
                # await ctx.invoke(self.qu, url)
                return

            self.voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)

            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192"
                }]
            }

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            for file in os.listdir("./"):
                if file.endswith(".mp3"):
                    name = file
                    os.rename(file, "song.mp3")
            
            self.voice.play(discord.FFmpegPCMAudio("song.mp3"))
            self.voice.source = discord.PCMVolumeTransformer(self.voice.source)

            set_volume = None
            if volume == 0:
                set_volume = self.volume
            else:
                set_volume = volume

            self.voice.source.volume = set_volume

    @commands.command()
    async def pause(self, ctx):
        """ Pause the music """
        self.voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)

        if self.voice and self.voice.is_playing():
            self.voice.pause()
            await ctx.send("Music paused")
        else:
            await ctx.send("Music not playing")

    @commands.command(aliases=["r"])
    async def resume(self, ctx):
        """ Resume the music """
        self.voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)
        if self.voice and self.voice.is_paused():
            self.voice.resume()
            await ctx.send("Resumed music")
        else:
            await ctx.send("No music to resume")
    
    @commands.command(aliases=["s"])
    async def stop(self, ctx):
        """ Stop the music (Also works as skip for now) """
        self.voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)
        if self.voice and self.voice.is_playing():
            self.voice.stop()
            await ctx.send("Music stopped")
        else:
            await ctx.send("No music playing")

    @commands.command()
    async def qu(self, ctx, url: str):
        """ Queue up music (Youtube link only for now) (WIP) """
        self.songq.append(url)

    @commands.command()
    async def skip(self, ctx):
        """ Don't use yet """
        await ctx.invoke(self.stop)
        if self.songq is None:
            await ctx.send("There is no queued song!")
            return
        
        song = self.songq.pop(0)
        await ctx.invoke(self.play, song)
    
    @commands.command(hidden = True)
    async def songqu(self, ctx):
        print(self.songq)
    
    @commands.command(name="volume",aliases=["setvolume","vol","v"])
    async def changevolume(self, ctx, vol:int):
        if not 0 <= vol <= 100:
            await ctx.send("Volume has to be between 0~100")
            return

        new_vol = float(vol)/100

        if self.voice and self.voice.is_playing():
            self.voice.source.volume = new_vol
        self.volume = new_vol
    
    async def playcustom(self, ctx, name, volume=0):
        async with self.lock:
            await ctx.invoke(self.j)

            self.voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)

            self.voice.play(discord.FFmpegPCMAudio(os.path.join(".", "InHouseBot", "custom_songs", f"{name}.mp3")))
            # self.voice.play(discord.FFmpegPCMAudio(os.path.join(".", "custom_songs", f"{name}.mp3")))
            self.voice.source = discord.PCMVolumeTransformer(self.voice.source)

            set_volume = None
            if volume == 0:
                set_volume = self.volume
            else:
                set_volume = volume

            self.voice.source.volume = set_volume
            await ctx.message.delete()

    @commands.command(aliases=["odin","odinrush", "pillarmen"])
    async def pillar(self, ctx):
        await self.playcustom(ctx, "Pillar", 0.08)
    
    @commands.command()
    async def bonesaw(self, ctx):
        await self.playcustom(ctx, "Bonesaw", 0.4)

    @commands.command(name="3minutes")
    async def threeminutes(self, ctx):
        await self.playcustom(ctx, "3Minutes", 0.7)
    
    @commands.command()
    async def yessir(self, ctx):
        await self.playcustom(ctx, "Yessir", 0.2)

    @commands.command()
    async def skinman(self, ctx):
        await self.playcustom(ctx, "Skinman")
    
    @commands.command()
    async def skeletonman(self, ctx):
        await self.playcustom(ctx, "Skeleton")
    
    @commands.command()
    async def nyanpasu(self, ctx):
        await self.playcustom(ctx, "NyanPasu")
        
    @commands.command(aliases=["haiti", "midnight"])
    async def midnighthaiti(self, ctx):
        await self.playcustom(ctx, "MidnightHaiti")
        
    @commands.command()
    async def bababooey(self, ctx):
        await self.playcustom(ctx, "Bababooey")
    
    @commands.command(aliases=['ohhi', 'oh'])
    async def garbage(self, ctx):
        await self.playcustom(ctx, "garbage")

    @commands.command()
    async def sus(self, ctx):
        await self.playcustom(ctx, "police")

    @commands.command(aliases=['openup'])
    async def fbi(self, ctx):
        await self.playcustom(ctx, "fbi")

    @commands.command()
    async def sail(self, ctx):
        await self.playcustom(ctx, "Sail")

    @commands.command(aliases=["yoniceknifedude", "knife", "dude"])
    async def yo(self, ctx):
        await self.playcustom(ctx, "knife")
    
    @commands.command(aliases=["world", "domination", "dom"])
    async def worlddomination(self, ctx):
        await self.playcustom(ctx, "WorldDomination")
        
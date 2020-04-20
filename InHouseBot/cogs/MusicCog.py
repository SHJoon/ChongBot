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

        if not discord.opus.is_loaded():
            discord.opus.load_opus('libopus.so')

        self.songq = []
        self.voice = None
    
    def check_q(self, ctx):
        if self.songq is None:
            return
        else:
            song = self.songq.pop(0)
            song_there = os.path.isfile("song.mp3")

            if song_there:
                os.remove("song.mp3")
            
            voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)

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
            
            voice.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: self.check_q(ctx))
            voice.source = discord.PCMVolumeTransformer(voice.source)
            voice.source.volume = 0.07

            print(name)

            nname = name.rsplit("-", 1)
    
    @commands.command()
    async def j(self, ctx):
        """ Make bot join voice channel """
        channel = ctx.message.author.voice.channel
        voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)

        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
            # await ctx.send(f"The bot has been connected to {channel}")
    
    @commands.command()
    async def l(self, ctx):
        """ Make bot leave voice channel """
        channel = ctx.message.author.voice.channel
        voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)

        if voice and voice.is_connected():
            await voice.disconnect()
            # await ctx.send(f"Bot has left {channel}")

    @commands.command(aliases=["p"])
    async def play(self, ctx, url: str):
        """ Play music (Youtube link only for now) """
        async with self.lock:
            await ctx.invoke(self.j)
            song_there = os.path.isfile("song.mp3")

            try:
                if song_there:
                    os.remove("song.mp3")
            except PermissionError:
                await ctx.invoke(self.qu, url)
                return

            voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)

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
            
            voice.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: self.check_q(ctx))
            voice.source = discord.PCMVolumeTransformer(voice.source)
            voice.source.volume = 0.07

            nname = name.rsplit("-", 1)
            await ctx.send(f"**Now playing:** {nname[0]}")

    @commands.command()
    async def pause(self, ctx):
        """ Pause the music """
        voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)

        if voice and voice.is_playing():
            voice.pause()
            await ctx.send("Music paused")
        else:
            await ctx.send("Music not playing")

    @commands.command()
    async def resume(self, ctx):
        """ Resume the music """
        voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)
        if voice and voice.is_paused():
            voice.resume()
            await ctx.send("Resumed music")
        else:
            await ctx.send("No music to resume")
    
    @commands.command()
    async def stop(self, ctx):
        """ Stop the music (Also works as skip for now) """
        voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)
        if voice and voice.is_playing():
            voice.stop()
            await ctx.send("Music stopped")
        else:
            await ctx.send("No music playing")

    @commands.command()
    async def qu(self, ctx, url: str):
        """ Queue up music (Youtube link only for now) """
        self.songq.append(url)

    @commands.command()
    async def skip(self, ctx):
        await ctx.invoke(self.stop)
        if self.songq is None:
            await ctx.send("There is no queued song!")
            return
        
        song = self.songq.pop(0)
        await ctx.invoke(self.play, song)
    
    @commands.command(hidden = True)
    async def songqu(self, ctx):
        print(self.songq)

    @commands.command(aliases=["odin","pillarmen"])
    async def pillar(self, ctx):
        await ctx.invoke(self.play, "https://www.youtube.com/watch?v=XUhVCoTsBaM")
    
    @commands.command()
    async def bonesaw(self, ctx):
        await ctx.invoke(self.play, "https://www.youtube.com/watch?v=powBr8Hobbk")

    @commands.command(name="3minutes")
    async def threeminutes(self, ctx):
        await ctx.invoke(self.play, "https://www.youtube.com/watch?v=AI-LvOYc5Gc")

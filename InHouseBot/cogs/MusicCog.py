import discord
from discord.ext import commands
import youtube_dl
import os
import shutil

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.songq = []
        self.voice = None
    
    def check_q(self, ctx):
        if self.songq is None:
            return
        else:
            song = self.songq.pop(0)
            await ctx.invoke(self.play, song)
            return
    
    @commands.command()
    async def j(self, ctx):
        channel = ctx.message.author.voice.channel
        voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)

        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
            await ctx.send(f"The bot has been connected to {channel}")
    
    @commands.command()
    async def l(self, ctx):
        channel = ctx.message.author.voice.channel
        voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)

        if voice and voice.is_connected():
            await voice.disconnect()
            await ctx.send(f"Bot has left {channel}")
        else:
            await ctx.send(f"Bot was not in a channel")

    @commands.command(aliases=["p"])
    async def play(self, ctx, url: str):
        song_there = os.path.isfile("song.mp3")

        try:
            if song_there:
                os.remove("song.mp3")
                print("Removed old song file")
        except PermissionError:
            await ctx.invoke(self.qu, url)
            return
        
        print("Getting everything ready")

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
            print("Downloading audio")
            ydl.download([url])
        
        for file in os.listdir("./"):
            if file.endswith(".mp3"):
                name = file
                print(f"Renamed File: {file}")
                os.rename(file, "song.mp3")
        
        voice.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: self.check_q(ctx))
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = 0.04

        print(name)

        nname = name.rsplit("-", 1)
        await ctx.send(f"**Now playing:** {nname[0]}")
        print("Playing")

    @commands.command()
    async def pause(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)

        if voice and voice.is_playing():
            print("Music paused")
            voice.pause()
            await ctx.send("Music paused")
        else:
            print("Music not playing")
            await ctx.send("Music not playing")

    @commands.command()
    async def resume(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)
        if voice and voice.is_paused():
            print("Music resuming")
            voice.resume()
            await ctx.send("Resumed music")
        else:
            await ctx.send("No music to resume")
    
    @commands.command()
    async def stop(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)
        if voice and voice.is_playing():
            print("Music stopped")
            voice.stop()
            await ctx.send("Music stopped")
        else:
            print("No music playing")
            await ctx.send("No music playing")

    @commands.command()
    async def qu(self, ctx, url: str):
        self.songq.append(url)

    @commands.command()
    async def skip(self, ctx):
        if self.songq is None:
            await ctx.send("There is no queued song!")
            return
        
        song = self.songq.pop(0)
        await ctx.invoke(self.play, song)

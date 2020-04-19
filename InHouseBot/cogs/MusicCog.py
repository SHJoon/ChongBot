import discord
from discord.ext import commands
import youtube_dl
import os
import shutil

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.songq = {}
    
    @commands.command()
    async def j(self, ctx):
        global voice
        channel = ctx.message.author.voice.channel
        voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)

        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
            print(f"The bot has been connected to {channel}.")
        """
        await voice.disconnect()

        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
            print(f"The bot has been connected to {channel}.")
        """
        # await ctx.send(f"Joined {channel}")
    
    @commands.command()
    async def l(self, ctx):
        channel = ctx.message.author.voice.channel
        voice = discord.utils.get(self.bot.voice_clients, guild = ctx.guild)

        if voice and voice.is_connected():
            await voice.disconnect()
            print(f"The bot has left {channel}")
            # await ctx.send(f"Left {channel}")
        else:
            print(f"Bot was not in a channel")
            # await ctx.send(f"Bot was not in a channel")

    @commands.command()
    async def p(self, ctx, url: str):

        def check_queue():

        song_there = os.path.isfile("song.mp3")

        try:
            if song_there:
                os.remove("song.mp3")
                print("Removed old song file")
        except PermissionError:
            print("Trying to delete, but it's being played")
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
        
        voice.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: print(f"{name} has finished playing"))
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
    async def qu(self, ctx, url):
        Queue_infile = os.path.isdir("./Queue")
        if not Queue_infile:
            os.mkdir("Queue")
        DIR = os.path.abspath(os.path.realpath("Queue"))
        q_num = len(os.listdir(DIR))
        q_num += 1
        add_queue = True
        while add_queue:
            if q_num in self.songq:
                q_num += 1
            else:
                add_queue = False
                self.songq[q_num] = q_num
        
        queue_path = os.path.abspath(os.path.realpath("Queue") + f"/song{q_num}.%(ext)%")

        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "outtmpl": queue_path,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }]
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print("Downloading audio")
            ydl.download([url])

        await ctx.send(f"Adding song {q_num} to the queue")

        print("Song added to q")
        
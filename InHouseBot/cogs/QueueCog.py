import asyncio
import discord
from discord.ext import commands

approved_roles = ["Admin"]

def is_approved():
    def predicate(ctx):
        author = ctx.message.author
        if any(role.name in approved_roles for role in author.roles):
            return True

    return commands.check(predicate)

class QueueCog(commands.Cog):
    def __init__(self, bot):
        self.queue = {}
        self.queuemsg = {}
        self.readynum = 10
    
    @commands.command(name="queue", aliases=["lobby", "q"])
    async def _queue(self, ctx):
        """ View the queue! """
        server = ctx.guild
        if server.id not in self.queuemsg:
            self.queuemsg[server.id] = None

        if self.queuemsg[server.id] is not None:
            try:
                await self.queuemsg[server.id].delete()
            except Exception:
                pass
        
        if server.id not in self.queue:
            self.queue[server.id] = [[], "None set yet"]
        
        message = f"**Gaming time**: {self.queue[server.id][1]}\n"
        for place, member_id in enumerate(self.queue[server.id][0]):
            member = discord.utils.get(server.members, id=member_id)
            name = member.nick if member.nick else member.name
            message += f"**#{place+1}** : {name}\n"
        if len(self.queue[server.id][0]) == 0:
            message += f"Queue is empty."
        
        embed = discord.Embed(description=message, colour=discord.Colour.green())
        embed.set_footer(text="Join the queue with !add / Leave the queue with !leave")
        self.queuemsg[server.id] = await ctx.send(embed=embed)
        await self.queuemsg[server.id].add_reaction("<:Join:668410201099206680>")
        await self.queuemsg[server.id].add_reaction("<:Drop:668410288667885568>")
        await self.queuemsg[server.id].add_reaction("<:RepostQueue:727428376331157585>")
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(aliases=["join"])
    async def add(self, ctx):
        """ Add yourself to the queue! """
        server = ctx.guild
        author = ctx.message.author

        # If the command is invoked for the first time in the server
        # Create a new key value pair
        if server.id not in self.queue:
            self.queue[server.id] = [[author.id], "None set yet"]
        # Else, append to the existing queue with the server id
        else:
            if author.id not in self.queue[server.id][0]:
                self.queue[server.id][0].append(author.id)
            else:
                await ctx.send("You are already in the queue!")
        await ctx.invoke(self._queue)
    
    @commands.command(aliases=["forcejoin","fjoin", "fadd"])
    async def forceadd(self, ctx, member: discord.Member):
        """ Force another user to join the queue with an @ """
        server = ctx.guild
        name = member.nick if member.nick else member.name

        if server.id not in self.queue:
            self.queue[server.id] = [[member.id], "None set yet"]
        else:
            if member.id not in self.queue[server.id][0]:
                self.queue[server.id][0].append(member.id)
            else:
                await ctx.send(f"{name} is already in the queue!")
        await ctx.invoke(self._queue)
    
    @commands.command(aliases=["leave", "drop"])
    async def remove(self, ctx):
        """ Remove yourself from the queue """
        server = ctx.guild
        author = ctx.message.author
        name = author.nick if author.nick else author.name

        if server.id not in self.queue or author.id not in self.queue[server.id][0]:
            await ctx.send("You were not in the queue")
        else:
            self.queue[server.id][0].remove(author.id)
            await ctx.send(f"{name} has been removed from the queue.")
        await ctx.invoke(self._queue)

    @commands.command(aliases=["forcedrop","forceleave","fremove","fdrop","fleave"])
    async def forceremove(self, ctx, member: discord.Member):
        """ Force another user to drop from the queue with an @ """
        server = ctx.guild
        name = member.nick if member.nick else member.name

        if server.id not in self.queue or member.id not in self.queue[server.id][0]:
            await ctx.send(f"{name} was not in the queue!")
        else:
            self.queue[server.id][0].remove(member.id)
            await ctx.send(f"{name} has been removed from the queue")
        await ctx.invoke(self._queue)
    
    @commands.command(name="ready", aliases=["go"])
    async def _ready(self, ctx):
        """ If everyone is ready to game, this command will ping them! """
        server = ctx.guild
        if server.id not in self.queue:
            self.queue[server.id] = [[], "None set yet"]
        
        if len(self.queue[server.id][0]) < self.readynum:
            await ctx.send("Not enough people in the lobby...")
            await ctx.invoke(self._queue)
            return
        
        message = ""
        for member_id in self.queue[server.id][0][0:self.readynum]:
            member = discord.utils.get(server.members, id=member_id)
            message += member.mention
        await ctx.send(message)
        for _ in range(self.readynum):
            self.queue[server.id][0].pop(0)
        await ctx.send("10 MEN TIME LESGOO")
        await ctx.invoke(self._queue)
    
    @commands.command(aliases=["qtime", "settime"])
    async def queuetime(self, ctx, *, _time):
        """ Set gaming time """
        server = ctx.guild
        if server.id not in self.queue:
            self.queue[server.id] = [[], _time]
        else:
            self.queue[server.id][1] = _time
        await ctx.invoke(self._queue)

    @commands.command(name="next")
    async def _next(self, ctx, num=1):
        """ Call the next member(s) in the queue """
        server = ctx.guild
        
        for _ in range(num):
            if len(self.queue[server.id][0]) == 0:
                await ctx.send("No one left in the queue :(")
                return
            
            member = discord.utils.get(ctx.guild.members, id=self.queue[server.id][0][0])
            await ctx.send(f"You are up **{member.mention}**! Have fun!")
            self.queue[server.id][0].remove(self.queue[server.id][0][0])
    
    @commands.command()
    @commands.has_permissions(manage_roles=True, ban_members=True)
    async def clear(self, ctx):
        """ Clears the queue (ADMIN ONLY) """
        server = ctx.guild
        self.queue[server.id] = [[], "None set yet"]
        await ctx.send("Queue has been cleared")
        await ctx.invoke(self._queue)
    
    @clear.error
    async def clear_error(self, error, ctx):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Only admins can perform that action.")
    
    @commands.command()
    async def leggo(self, ctx, *, _time = "None set yet"):
        """ Let's organize a game! """
        server = ctx.guild
        self.queue[server.id] = [[], _time]
        await ctx.send("Time for some games! Join the lobby @here")
        await ctx.invoke(self._queue)
    
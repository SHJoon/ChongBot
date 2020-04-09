import random
import discord
import asyncio
import httpx
from discord.ext import commands
from utils.codes import cid_lookup, item_lookup

class LeagueCog(commands.Cog):
    def __init__(self, bot):
        self._init_champ()
        self.client = httpx.AsyncClient()

    def _init_champ(self):
        champ_req = httpx.get("https://api.op.lol/tierlist/5/?lane=default&patch=10.7&tier=platinum_plus&queue=420&region=all")
        top_req = httpx.get("https://api.op.lol/tierlist/5/?lane=top&patch=10.7&tier=platinum_plus&queue=420&region=all")
        jungle_req = httpx.get("https://api.op.lol/tierlist/5/?lane=jungle&patch=10.7&tier=platinum_plus&queue=420&region=all")
        middle_req = httpx.get("https://api.op.lol/tierlist/5/?lane=middle&patch=10.7&tier=platinum_plus&queue=420&region=all")
        bottom_req = httpx.get("https://api.op.lol/tierlist/5/?lane=bottom&patch=10.7&tier=platinum_plus&queue=420&region=all")
        support_req = httpx.get("https://api.op.lol/tierlist/5/?lane=support&patch=10.7&tier=platinum_plus&queue=420&region=all")

        self.champ_resp = champ_req.json()
        self.top_resp = top_req.json()
        self.jungle_resp = jungle_req.json()
        self.middle_resp = middle_req.json()
        self.bottom_resp = bottom_req.json()
        self.support_resp = support_req.json()
        
        self.champs_list, self.top_list, self.jungle_list, self.middle_list, self.bottom_list, self.support_list = [], [], [], [], [], []

        self.update_role_list(self.champ_resp, self.champs_list)
        self.update_role_list(self.top_resp, self.top_list)
        self.update_role_list(self.jungle_resp, self.jungle_list)
        self.update_role_list(self.middle_resp, self.middle_list)
        self.update_role_list(self.bottom_resp, self.bottom_list)
        self.update_role_list(self.support_resp, self.support_list)
    
    def update_role_list(self, role_resp, role_list):
        for cid in role_resp['cid']:
            if role_resp['cid'][cid][0] == 0:
                continue
            else:
                role_list.append(cid_lookup[int(cid)])
    
    @commands.group(aliases = ["champ", "champs", "champions"])
    async def champion(self, ctx, role = None):
        """ Randomly choose a champ for you """
        if role is None:
            await ctx.send(random.choice(self.champs_list))
        elif role in ("top"):
            await ctx.send(random.choice(self.top_list))
        elif role in ("jungle", "jg", "jung"):
            await ctx.send(random.choice(self.jungle_list))
        elif role in ("middle", "mid"):
            await ctx.send(random.choice(self.middle_list))
        elif role in ("bottom", "bot", "adc"):
            await ctx.send(random.choice(self.bottom_list))
        elif role in ("support", "sup", "supp", "spt"):
            await ctx.send(random.choice(self.support_list))
        elif role in ("fun", "4fun", "4fun4"):
            chmp = random.choice(self.champs_list)
            rl = random.choice(["Top", "Jungle", "Mid", "Bot", "Support"])
            await ctx.send(f"{chmp} {rl}")
        else:
            await ctx.send(random.choice(self.champs_list))
"""
    @commands.group()
    async def topchamp(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("L")
    
    @topchamp.command()
    async def top(self, ctx, num = 10):
        await ctx.send("test")
    
    @topchamp.command(aliases = ["jg", "jung"])
    async def jungle(self, ctx, num = 10):
        await ctx.send("test1")

    @topchamp.command(aliases = ["mid"])
    async def middle(self, ctx, num = 10):
        await ctx.send("test2")

    @topchamp.command(aliases = ["bot", "adc"])
    async def bottom(self, ctx, num = 10):
        await ctx.send("test3")

    @topchamp.command(aliases = ["sup", "supp", "spt"])
    async def support(self, ctx, num = 10):
        await ctx.send("test4")

    @commands.command()
    async def test(self, ctx):
        sett_req = await self.client.get("https://api.op.lol/champion/2/?patch=10.7&cid=875&lane=top&tier=platinum_plus&queue=420&region=all")
        sett_resp = sett_req.json()
        print(sett_resp)
"""
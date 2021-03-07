import random
import discord
import asyncio
import httpx
from discord.ext import commands
from utils.codes import cid_lookup, item_lookup, urls
import io

class LeagueCog(commands.Cog):
    def __init__(self, bot):
        self._init_champ()
        self.client = httpx.AsyncClient()

    def _init_champ(self):
        self.version_num = httpx.get("https://ddragon.leagueoflegends.com/api/versions.json").json()
        self.patch_num = self.version_num[0].split(".")
        self.patch = f"{self.patch_num[0]}.{self.patch_num[1]}"
        # self.patch = "10.16"
        champ_req = httpx.get(f"https://api.op.lol/tierlist/5/?lane=default&patch={self.patch}&tier=platinum_plus&queue=420&region=all")
        top_req = httpx.get(f"https://api.op.lol/tierlist/5/?lane=top&patch={self.patch}&tier=platinum_plus&queue=420&region=all")
        jungle_req = httpx.get(f"https://api.op.lol/tierlist/5/?lane=jungle&patch={self.patch}&tier=platinum_plus&queue=420&region=all")
        middle_req = httpx.get(f"https://api.op.lol/tierlist/5/?lane=middle&patch={self.patch}&tier=platinum_plus&queue=420&region=all")
        bottom_req = httpx.get(f"https://api.op.lol/tierlist/5/?lane=bottom&patch={self.patch}&tier=platinum_plus&queue=420&region=all")
        support_req = httpx.get(f"https://api.op.lol/tierlist/5/?lane=support&patch={self.patch}&tier=platinum_plus&queue=420&region=all")

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
    async def champion(self, ctx, role = "None"):
        """ Randomly choose a champ for you """
        if role in ("top"):
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
    
    async def topkmsg(self, inp_dict, k):
        new_dict = {}
        for cid in inp_dict['cid']:
            if not inp_dict['cid'][cid][0] == 0:
                new_dict[cid] = inp_dict['cid'][cid]
        
        # Use linear sort, but will try to use more efficient top-k sort in the future
        sorted_dict = dict(sorted(new_dict.items(), key = lambda inner: inner[1]))
        if k > len(sorted_dict):
            k = len(sorted_dict)
        msg = ""
        for champdata in list(sorted_dict.items())[:k]:
            msg += f"#{champdata[1][0]}: {cid_lookup[int(champdata[0])]}\n"
        
        return msg
    
    async def sendEmbed(self, ctx, etitle, econtent, eurl):
        embed = discord.Embed(title=etitle, description=econtent, url=eurl)
        embed.set_thumbnail(url="https://cdn.op.lol/img/lolalytics/logo/lolalytics.png")
        await ctx.send(embed=embed)

    @commands.group(aliases=["topchamps", "topchampion", "topchampions"])
    async def topchamp(self, ctx):
        """ View the list of top champions in each lane! """
        if ctx.invoked_subcommand is None:
            cmd = ctx.message.content.split(" ", 1)
            print(cmd)
            key = cmd[1]
            if not key.isdigit():
                await ctx.send("The command format is `!topchamp [amount]` or `!topchamp [role] [amount]`")
                return
            num = int(key)
            if not num >= 0:
                await ctx.send("Really...")
                return
            if num > len(self.champ_resp['cid']):
                num = len(self.champ_resp['cid'])
            title = f"Lolalytics top {key} champion(s) \nin every lanes (Patch {self.patch})"
            await self.sendEmbed(ctx, title, await self.topkmsg(self.champ_resp, num), urls["all"])

    @topchamp.command()
    async def top(self, ctx, num:int = 10):
        if not num >= 0:
            await ctx.send("Really...")
            return
        title = f"Lolalytics top {num} champion(s) \nin the Top lane (Patch {self.patch})"
        await self.sendEmbed(ctx, title, await self.topkmsg(self.top_resp, num), urls["top"])
    
    @topchamp.command(aliases = ["jg", "jung"])
    async def jungle(self, ctx, num:int = 10):
        if not num >= 0:
            await ctx.send("Really...")
            return
        title = f"Lolalytics top {num} champion(s) \nin the Jungle (Patch {self.patch})"
        await self.sendEmbed(ctx, title, await self.topkmsg(self.jungle_resp, num), urls["jungle"])

    @topchamp.command(aliases = ["mid"])
    async def middle(self, ctx, num:int = 10):
        if not num >= 0:
            await ctx.send("Really...")
            return
        title = f"Lolalytics top {num} champion(s) \nin the Mid lane (Patch {self.patch})"
        await self.sendEmbed(ctx, title, await self.topkmsg(self.middle_resp, num), urls["mid"])

    @topchamp.command(aliases = ["bot", "adc"])
    async def bottom(self, ctx, num:int = 10):
        if not num >= 0:
            await ctx.send("Really...")
            return
        title = f"Lolalytics top {num} champion(s) \nin the Bot lane (Patch {self.patch}):"
        await self.sendEmbed(ctx, title, await self.topkmsg(self.bottom_resp, num), urls["bot"])

    @topchamp.command(aliases = ["sup", "supp", "spt"])
    async def support(self, ctx, num:int = 10):
        if not num >= 0:
            await ctx.send("Really...")
            return
        title = f"Lolalytics top {num} champion(s) \nin the Support (Patch {self.patch}):"
        await self.sendEmbed(ctx, title, await self.topkmsg(self.support_resp, num), urls["sup"])

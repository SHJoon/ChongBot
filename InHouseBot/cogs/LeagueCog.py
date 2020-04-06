import random
import discord
import asyncio
import httpx
from discord.ext import commands

class LeagueCog(commands.Cog):
    def __init__(self, bot):
        self.cid_lookup = {
            266: "Aatrox",
            103: "Ahri",
            84: "Akali",
            12: "Alistar",
            32: "Amumu",
            34: "Anivia",
            1: "Annie",
            523: "Aphelios",
            22: "Ashe",
            136: "Aurelion Sol",
            268: "Azir",
            432: "Bard",
            53: "Blitzcrank",
            63: "Brand",
            201: "Braum",
            51: "Caitlyn",
            164: "Camille",
            69: "Cassiopeia",
            31: "Cho'gath",
            42: "Corki",
            122: "Darius",
            131: "Diana",
            119: "Draven",
            36: "Dr. Mundo",
            245: "Ekko",
            60: "Elise",
            28: "Evelynn",
            81: "Ezreal",
            9: "Fiddlesticks",
            114: "Fiora",
            105: "Fizz",
            3: "Galio",
            41: "Gangplank",
            86: "Garen",
            150: "Gnar",
            79: "Gragas",
            104: "Graves",
            120: "Hecarim",
            74: "Heimerdinger",
            420: "Illaoi",
            39: "Irelia",
            427: "Ivern",
            40: "Janna",
            59: "Jarvan IV",
            24: "Jax",
            126: "Jayce",
            202: "Jhin",
            222: "Jinx",
            145: "Kai'sa",
            429: "Kalista",
            43: "Karma",
            30: "Karthus",
            38: "Kassadin",
            55: "Katarina",
            10: "Kayle",
            141: "Kayn",
            85: "Kennen",
            121: "Kha'zix",
            203: "Kindred",
            240: "Kled",
            96: "Kog'Maw",
            7: "Leblanc",
            64: "Lee Sin",
            89: "Leona",
            127: "Lissandra",
            236: "Lucian",
            117: "Lulu",
            99: "Lux",
            54: "Malphite",
            90: "Malzahar",
            57: "Maokai",
            11: "Master Yi",
            21: "Miss Fortune",
            62: "Wukong",
            82: "Mordekaiser",
            25: "Morgana",
            267: "Nami",
            75: "Nasus",
            111: "Nautilus",
            518: "Neeko",
            76: "Nidalee",
            56: "Nocturne",
            20: "Nunu",
            2: "Olaf",
            61: "Orianna",
            516: "Ornn",
            80: "Pantheon",
            78: "Poppy",
            555: "Pyke",
            246: "Qiyana",
            133: "Quinn",
            497: "Rakan",
            33: "Rammus",
            421: "Rek'Sai",
            58: "Renekton",
            107: "Rengar",
            92: "Riven",
            68: "Rumble",
            13: "Ryze",
            113: "Sejuani",
            235: "Senna",
            875: "Sett",
            35: "Shaco",
            98: "Shen",
            102: "Shyvana",
            27: "Singed",
            14: "Sion",
            15: "Sivir",
            72: "Skarner",
            37: "Sona",
            16: "Soraka",
            50: "Swain",
            517: "Sylas",
            134: "Syndra",
            223: "Tahm Kench",
            163: "Taliyah",
            91: "Talon",
            44: "Taric",
            17: "Teemo",
            412: "Thresh",
            18: "Tristana",
            48: "Trundle",
            23: "Tryndamere",
            4: "Twisted Fate",
            29: "Twitch",
            77: "Udyr",
            6: "Urgot",
            110: "Varus",
            67: "Vayne",
            45: "Veigar",
            161: "Vel'koz",
            254: "Vi",
            112: "Viktor",
            8: "Vladimir",
            106: "Volibear",
            19: "Warwick",
            498: "Xayah",
            101: "Xerath",
            5: "Xin Zhao",
            157: "Yasuo",
            83: "Yorick",
            350: "Yuumi",
            154: "Zac",
            238: "Zed",
            115: "Ziggs",
            26: "Zilean",
            142: "Zoe",
            143: "Zyra",
        }
        # self.client = httpx.AsyncClient()

        self._init_champ()

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
                role_list.append(self.cid_lookup[int(cid)])
    
    @commands.group(aliases = ["champ", "champs", "champions"])
    async def champion(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(random.choice(self.champs_list))

    @champion.command()
    async def top(self, ctx):
        await ctx.send(random.choice(self.top_list))

    @champion.command(aliases = ["jg"])
    async def jungle(self, ctx):
        await ctx.send(random.choice(self.jungle_list))
        
    @champion.command(aliases = ["mid"])
    async def middle(self, ctx):
        await ctx.send(random.choice(self.middle_list))
        
    @champion.command(aliases = ["bot", "adc"])
    async def bottom(self, ctx):
        await ctx.send(random.choice(self.bottom_list))
        
    @champion.command(aliases = ["sup", "supp", "spt"])
    async def support(self, ctx):
        await ctx.send(random.choice(self.support_list))
    
    @champion.command(aliases=["4fun","4fun4"])
    async def fun(self, ctx):
        chmp = random.choice(self.champs_list)
        rl = random.choice(["Top", "Jungle", "Mid", "Bot", "Support"])
        await ctx.send(f"{chmp} {rl}")

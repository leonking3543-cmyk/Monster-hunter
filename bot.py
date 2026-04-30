"""
Monster Hunter RPG - Discord Bot - V118 HTML-Synced
Sincronizado com monster_hunter_V117.html — mecânicas, HUD e sistema de batalha completos
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
import math
import asyncio
import time
import urllib.parse
import aiohttp
import base64
import io
from typing import Optional

# ══════════════════════════════════════════════
# POLLINATIONS AI — Geração de imagem (100% gratuito, sem API key)
# ══════════════════════════════════════════════
_image_lock = asyncio.Lock()
_next_api_call = 0.0

async def generate_image_with_queue(prompt: str, max_attempts: int = 5) -> bytes:
    global _next_api_call
    last_err = None
    async with _image_lock:
        for attempt in range(max_attempts):
            now = time.time()
            if now < _next_api_call:
                await asyncio.sleep(_next_api_call - now)
            try:
                encoded_prompt = urllib.parse.quote(prompt)
                url = (
                    f"https://image.pollinations.ai/prompt/{encoded_prompt}"
                    f"?width=512&height=512&model=flux&nologo=true&enhance=false"
                )
                timeout = aiohttp.ClientTimeout(total=180, connect=20)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url) as resp:
                        if resp.status == 429:
                            wait_time = min(30 * (attempt + 1), 120)
                            print(f"⚠️ [IMG] 429 — pausa de {wait_time}s (tentativa {attempt+1}/{max_attempts})")
                            _next_api_call = time.time() + wait_time
                            continue
                        if resp.status != 200:
                            raise Exception(f"Erro HTTP {resp.status}")
                        data = await resp.read()
                        if len(data) > 1000:
                            _next_api_call = time.time() + 5.0
                            return data
                        raise Exception("Resposta vazia da API")
            except Exception as e:
                last_err = str(e)
                print(f"[IMG] Tentativa {attempt+1} falhou: {last_err}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(5)
    raise Exception(f"Falha após {max_attempts} tentativas. Último erro: {last_err}")

# ══════════════════════════════════════════════
# CONFIGURAÇÕES DE SAVE (NOVO)
# ══════════════════════════════════════════════

SAVE_VERSION = 2   # ← Aumente este número quando mudar a estrutura do save

def migrate_save(data: dict) -> dict:
    """Migra saves antigos automaticamente"""
    version = data.get("save_version", 0)

    if version < 1:
        data.setdefault("team", [])
        data.setdefault("box", [])
        data.setdefault("caught", [])
        data.setdefault("bossDefeated", [])
        data.setdefault("items", {})
        data.setdefault("materials", {})
        data.setdefault("rankedElo", 1200)
        data.setdefault("rebirthCount", 0)
        data.setdefault("playerName", None)

    if version < 2:
        # Migração para rebirth bonus nos monstros
        for mon in data.get("team", []) + data.get("box", []):
            if "_rebirthBonus" not in mon:
                mon["_rebirthBonus"] = data.get("rebirthCount", 0) * 0.5

    data["save_version"] = SAVE_VERSION
    return data

# ══════════════════════════════════════════════
# DADOS DO JOGO (sincronizados com HTML)
# ══════════════════════════════════════════════

RARITY_PLAN = [
    {"rare":"comum",   "catch":.66, "hp":24,  "atk":5,  "mat":8},
    {"rare":"comum",   "catch":.64, "hp":27,  "atk":5,  "mat":9},
    {"rare":"comum",   "catch":.62, "hp":30,  "atk":6,  "mat":10},
    {"rare":"incomum", "catch":.56, "hp":34,  "atk":7,  "mat":13},
    {"rare":"incomum", "catch":.53, "hp":37,  "atk":8,  "mat":15},
    {"rare":"incomum", "catch":.5,  "hp":40,  "atk":9,  "mat":17},
    {"rare":"raro",    "catch":.41, "hp":46,  "atk":11, "mat":24},
    {"rare":"raro",    "catch":.38, "hp":50,  "atk":12, "mat":27},
    {"rare":"raro",    "catch":.35, "hp":54,  "atk":13, "mat":30},
    {"rare":"épico",   "catch":.26, "hp":62,  "atk":15, "mat":40},
    {"rare":"épico",   "catch":.23, "hp":68,  "atk":17, "mat":46},
    {"rare":"lendário","catch":.17, "hp":82,  "atk":19, "mat":60},
    {"rare":"lendário","catch":.14, "hp":90,  "atk":21, "mat":70},
    {"rare":"mítico",  "catch":.1,  "hp":108, "atk":24, "mat":90},
    {"rare":"mítico",  "catch":.08, "hp":118, "atk":27, "mat":105},
]

TYPE_DEFS = [
    {"t":"fogo",    "c":0xe2583d,"root":"Flama","mat":"Brasa",    "hpMod":0,  "atkMod":0,
     "names":["Flaminho","Labaréu","Brasalto","Fornalix","Tochino","Faíscor","Fogaréu","Pirólito","Chamego","Cinzal","Braseon","Magmário","Ardencor","Vulkar","Solferno"],
     "emojis":["🔥","🦊","🕯️","🐅","🏮","🧨","🐲","🍂","☄️","🦁","🎇","🌋","❤️‍🔥","🐦‍🔥","☀️"]},
    {"t":"água",    "c":0x3a92d9,"root":"Mar",  "mat":"Gota",     "hpMod":-1, "atkMod":0,
     "names":["Marulhinho","Bolhudo","Aqualume","Mariscoz","Pingorim","Riachito","Mareco","Ondal","Nautelo","Aqualux","Tsuniko","Abissor","Maréon","Leviagota","Tidalux"],
     "emojis":["💧","🐟","🌊","🐠","🫧","🐸","🦦","💦","🦭","🐬","🦈","🐋","🌧️","🪸","🔱"]},
    {"t":"planta",  "c":0x4ea85f,"root":"Folha","mat":"Folha",    "hpMod":3,  "atkMod":-1,
     "names":["Brotinho","Ramalho","Trepiko","Verdelim","Mossito","Clorofim","Galhudo","Vinhedo","Botanix","Silvério","Selvar","Espinhaflor","Clorossauro","Floracel","Matrizal"],
     "emojis":["🌿","🍀","🪴","🌱","🍃","🌵","🌾","🌻","🌳","🍄","🌺","🪻","🌴","🌸","🌲"]},
    {"t":"terra",   "c":0x9b7b54,"root":"Pedra","mat":"Pedra",    "hpMod":8,  "atkMod":-2,
     "names":["Cascalho","Barrolho","Territo","Tremorim","Areíto","Pedrino","Lamosso","Sedento","Gravito","Monterro","Basalto","Colossalmo","Terragor","Pedrax","Titanterra"],
     "emojis":["🪨","🦔","🐗","🪵","🏜️","⛰️","🐢","🦬","🐘","🦏","🧱","🏔️","🗿","⚒️","🌍"]},
    {"t":"ar",      "c":0x80cde0,"root":"Vento","mat":"Pluma",    "hpMod":-3, "atkMod":1,
     "names":["Assobinho","Névolo","Brisito","Volitro","Nublim","Aeral","Celsito","Ventor","Ciclar","Nebulon","Furavento","Aerólux","Tempespin","Estratelo","Skythar"],
     "emojis":["🪶","☁️","🕊️","🌬️","🪽","🪁","🎈","🦅","🌪️","🦉","🦤","🐦","🪂","🌫️","🚬"]},
    {"t":"gelo",    "c":0x77c9df,"root":"Gelo", "mat":"Cristal",  "hpMod":4,  "atkMod":1,
     "names":["Gelito","Nevisco","Frigelo","Branquim","Geadinho","Cristagel","Polarim","Nevon","Brisagel","Granizo","Gelágio","Glacialto","Cryonix","Nevastro","Zeroar"],
     "emojis":["❄️","⛄","🧊","🐧","🛷","🥶","🐻‍❄️","🏔️","🦣","🧤","🎿","⛸️","🍧","🐺","☃️"]},
    {"t":"trovão",  "c":0xe4c243,"root":"Raio", "mat":"Faísca",   "hpMod":-2, "atkMod":2,
     "names":["Raiolho","Choquito","Faíscudo","Pulsarim","Estaleco","Voltino","Troval","Neonchoque","Descargor","Eletrux","Tempestral","Raiotron","Fulminax","Arcozapp","Stormvolt"],
     "emojis":["⚡","🔋","🐹","💡","📻","💾","🦘","🌩️","📀","🔌","🚨","🪫","📱","🗜️","🥁"]},
    {"t":"sombra",  "c":0x5960b8,"root":"Sombra","mat":"Essência","hpMod":-1, "atkMod":3,
     "names":["Breuzinho","Sombralho","Ocultim","Vultito","Umbralim","Nocturo","Escurix","Véunegra","Tenebris","Mistumbrio","Abysmino","Sombrakar","Vaziurno","Crepux","Noxthar"],
     "emojis":["🌑","🦇","🐈‍⬛","🕳️","🕸️","🎩","♠️","🌘","🕷️","🖤","🌒","🥷","🌌","👁️","🎩"]},
    {"t":"cristal", "c":0x73cfe0,"root":"Cristal","mat":"Gema",   "hpMod":1,  "atkMod":2,
     "names":["Facetim","Brilhux","Vidrilho","Lúmino","Gemarim","Prismal","Reflexor","Cintilux","Quartzel","Luzcrist","Diamar","Shinério","Prismon","Glamyte","Luxórion"],
     "emojis":["💎","🪩","🔷","💠","🔮","💍","👑","🪞","🪩","🧂","🔹","🧿","🪙","🪬","❇️"]},
    {"t":"veneno",  "c":0x8e4ac2,"root":"Tóxico","mat":"Toxina",  "hpMod":2,  "atkMod":1,
     "names":["Toxito","Peçonhudo","Bafumeio","Ácidim","Nocivo","Vaporoz","Miasmelo","Corrosix","Venomix","Biletor","Toxibras","Podrino","Morbax","Peçonrex","Nexovina"],
     "emojis":["☠️","🧪","🐍","🦂","🪱","🦠","🐌","🦨","🦎","🧫","☣️","🦟","🗑️","🧟","🪦"]},
    {"t":"som",     "c":0xff9ff3,"root":"Eco",  "mat":"Vibração", "hpMod":-3, "atkMod":4,
     "names":["Notinha","Apito","Vibrax","Ecoante","Resson","Sônico","Ressonância","Batida","Melódico","Grito","Harmon","Bumbo","Agudo","Sinfon","Ópera"],
     "emojis":["🎵","🔔","📣","🎼","🎷","🎸","🎹","🎺","🎻","🎙️","📻","🔉","🔈","🔇","🔊"]},
    {"t":"tempo",   "c":0x54a0ff,"root":"Cronos","mat":"Engrenagem","hpMod":5,"atkMod":2,
     "names":["Tique","Toque","Ampulim","Relogito","Sécullus","Erax","Momentum","Pendor","Eterno","Cronix","Antigo","Futuro","Paradoxo","Zênite","Infinito"],
     "emojis":["⌛","⏳","⌚","⏰","🕰️","📅","📆","🗓️","🌀","⚙️","🔙","🔜","♾️","🗝️","🏛️"]},
    {"t":"luz",     "c":0xfeca57,"root":"Brilho","mat":"Fóton",   "hpMod":2,  "atkMod":1,
     "names":["Faisquinha","Raioluz","Lume","Solaris","Claro","Aura","Relampo","Radiante","Glorioso","Cintilo","Ilumin","Candela","Facho","Prisma","Divino"],
     "emojis":["☀️","⭐","🌟","✨","🔦","💡","🕯️","🌕","🌅","🌤️","🎥","📸","🎐","🔆","👼"]},
    {"t":"cosmos",  "c":0x2e86de,"root":"Astro","mat":"Poeira Estelar","hpMod":0,"atkMod":6,
     "names":["Nebulino","Cometa","Orbital","Galaxico","Quasar","Pulzar","Sideral","Vácuo","Astro","Luneto","Solfar","Planeta","Constela","Zenit","Universo"],
     "emojis":["🌌","🪐","☄️","🛰️","🛸","🌑","🌘","🔭","🌌","☄️","🛸","🚀","👽","🛰️","🌠"]},
    {"t":"metal",   "c":0x95a5a6,"root":"Aço",  "mat":"Lingote",  "hpMod":10, "atkMod":0,
     "names":["Prequinho","Latão","Blindado","Chapa","Mecano","Tanque","Escudo","Lâmina","Broca","Titânio","Robusto","Cromo","Bigorna","Colosso","Muralha"],
     "emojis":["🔩","⚙️","⛓️","🗡️","🛡️","⚓","⚔️","⚒️","🛠️","⛏️","🚜","🏗️","🏢","🚄","🦾"]},
    {"t":"fantasma","c":0x9b59b6,"root":"Espectro","mat":"Ectoplasma","hpMod":-2,"atkMod":3,
     "names":["Fantasminha","Vaporzinho","Espectrim","Sombraluz","Aparião","Poltergeist","Etéreo","Wraitho","Spectrax","Bansheiro","Hauntelo","Phantomix","Espírito","Revenant","Necrovolt"],
     "emojis":["👻","🫥","💨","🌫️","👁️","🕯️","🪦","🕸️","🌒","🦴","💀","🪄","🌑","⛧","🔮"]},
    {"t":"dragão",  "c":0xc0392b,"root":"Dracônico","mat":"Escama","hpMod":6, "atkMod":4,
     "names":["Drakoninho","Wyvernito","Serpelux","Ryudrak","Winguim","Dracozar","Fyrrex","Drakonis","Ignithorn","Scalethar","Clawmere","Draklord","Vyraxion","Nidragor","Dragonyx"],
     "emojis":["🐉","🦕","🦖","🐲","🔥","🌋","⚔️","🛡️","🌪️","🌊","⚡","❄️","☄️","💫","👑"]},
    {"t":"fada",    "c":0xff6eb4,"root":"Encanto","mat":"Pó de Fada","hpMod":0,"atkMod":2,
     "names":["Fadinhas","Encantura","Pixelim","Glitterix","Sparkelo","Lumiríx","Feerinha","Dazzlim","Wisping","Shimmerix","Blossomix","Glowette","Twinkling","Sprinklex","Celestira"],
     "emojis":["🧚","🌸","✨","🦋","🌺","🎀","💗","🌈","🪷","🌠","💖","🫧","🪻","🎆","🔮"]},
    {"t":"psíquico","c":0x8e44ad,"root":"Mental","mat":"Frag. Psíquico","hpMod":-1,"atkMod":4,
     "names":["Psiquim","Mentalis","Telepatix","Alucinex","Premonix","Clairix","Psivolt","Mindmere","Intuidor","Kinesis","Espatix","Telekin","Cognithor","Visionix","Omegamind"],
     "emojis":["🔮","🧠","👁️","🌀","💜","🪬","⭐","🌊","🎭","💭","🫀","🔵","🧿","💫","🌌"]},
    {"t":"luta",    "c":0xe74c3c,"root":"Golpe","mat":"Fita de Treino","hpMod":2,"atkMod":5,
     "names":["Soqinho","Pontapelux","Upperim","Jabhero","Kombatik","Rushador","Strikelux","Grapplino","Punchix","Kicker","Kickzilla","Sluggerax","Brutegor","Ironknuckle","Ultimapunch"],
     "emojis":["👊","🥊","🥋","🤼","💪","🦵","🦶","⚡","🔥","🏋️","🤺","🥷","🏆","⚔️","💢"]},
    {"t":"inseto",  "c":0x27ae60,"root":"Quitina","mat":"Casulo", "hpMod":1,  "atkMod":2,
     "names":["Lagartixa","Besourelo","Borbolim","Formigor","Escaravim","Gafanhotix","Larviço","Cocônix","Chrysalis","Antleon","Scarabeux","Beetlord","Mothwing","Mantidor","Hexapod"],
     "emojis":["🐛","🦋","🐝","🐜","🦗","🕷️","🐞","🪲","🪳","🦟","🦠","🌿","🍃","🌱","🪸"]},
    {"t":"néon",    "c":0x00ffcc,"root":"Néon", "mat":"Plasma Néon","hpMod":-3,"atkMod":5,
     "names":["Néonix","Glitchim","Ciberlink","Pixelglow","Synthrix","Databit","Wireframe","Glowbyte","Circuitex","Lagzero","Flashnet","Hyperglow","Matrixter","Virtuelux","Cybercore"],
     "emojis":["🟢","💚","🔋","📡","💻","🖥️","📺","🎮","🕹️","🔌","📱","💾","🛜","🔆","⚡"]},
    {"t":"nuclear", "c":0xf39c12,"root":"Atômico","mat":"Urânio", "hpMod":0,  "atkMod":6,
     "names":["Radiino","Atomillo","Nucléix","Fusionix","Fissurex","Radiotor","Halflifo","Decayix","Isótopo","Falloutix","Gammaray","Reatorix","Critimass","Meltorex","Nucleagor"],
     "emojis":["☢️","⚗️","💥","🔬","🧬","⚡","🌡️","🧪","💣","🔥","🌋","☄️","💫","🌀","🔶"]},
    {"t":"espírito","c":0x1abc9c,"root":"Alma", "mat":"Essência Espiritual","hpMod":3,"atkMod":2,
     "names":["Alminha","Kamirix","Shintorix","Ancestrix","Espirix","Soulix","Totemix","Orixim","Blessor","Holyrim","Sacredix","Mantra","Divinix","Transcend","Enlighten"],
     "emojis":["🙏","⛩️","🎋","🪬","🔯","☯️","🕉️","✡️","🔱","⚜️","🪷","🌸","🌟","💫","👼"]},
    {"t":"mecânico","c":0x7f8c8d,"root":"Máquina","mat":"Peça Mecânica","hpMod":8,"atkMod":1,
     "names":["Robotinho","Automec","Dronix","Cogwheelx","Steamrix","Pistonix","Valvulor","Turbinix","Transmitor","Gearborg","Motorax","Clockwork","Steamborg","Technogor","Mekavolt"],
     "emojis":["🤖","⚙️","🔧","🔩","🛠️","🚜","🏗️","🚂","✈️","🚀","🛸","🦾","🦿","🧲","💡"]},
    {"t":"ventos",  "c":0x3498db,"root":"Tufão","mat":"Redemoinho","hpMod":-2, "atkMod":3,
     "names":["Brisim","Tufarix","Zonalix","Cyclonix","Galerix","Tempestix","Twistix","Squallo","Zephyrion","Anemix","Typhonex","Sirocco","Mistral","Boreamix","Zondragor"],
     "emojis":["🌪️","🌀","💨","🌬️","🌊","⛵","🪁","🎑","🎐","☁️","🌩️","⛈️","🌧️","🌦️","🪂"]},
    {"t":"magma",   "c":0xe67e22,"root":"Magma","mat":"Lava Solidificada","hpMod":5,"atkMod":3,
     "names":["Lavinha","Magmarim","Ignerix","Pyroclax","Emberlux","Calderon","Scorcherix","Infernix","Lavabeast","Moltenix","Cinder","Eruption","Volcanus","Firestorm","Magmarex"],
     "emojis":["🌋","🔥","💥","🧱","🏔️","☄️","🫧","🌡️","⚗️","🔶","🟠","🟤","🫁","🪨","⛏️"]},
    {"t":"arcano",  "c":0x8e44ad,"root":"Arcanjo","mat":"Cristal Arcano","hpMod":1,"atkMod":5,
     "names":["Arcalix","Rúnico","Spellrix","Glamorix","Hexamix","Grimora","Occultix","Witchix","Conjuror","Runeborn","Eldritch","Sorceron","Arcanix","Mystara","Sorceling"],
     "emojis":["🪄","✨","🔮","📖","🌙","⭐","💜","🎩","🃏","🪬","📜","🔯","🌀","💫","🧿"]},
]

# TYPE_CHART sincronizado com HTML (advantages/disadvantages)
TYPE_CHART = {
    "fogo":    {"advantages":["gelo","planta"],          "disadvantages":["terra","água"]},
    "água":    {"advantages":["fogo","gelo"],            "disadvantages":["planta","trovão"]},
    "planta":  {"advantages":["água","terra"],           "disadvantages":["fogo","veneno"]},
    "terra":   {"advantages":["trovão","fogo"],          "disadvantages":["planta","cristal"]},
    "ar":      {"advantages":["veneno","sombra"],        "disadvantages":["cosmos","metal"]},
    "gelo":    {"advantages":["luz","veneno"],           "disadvantages":["fogo","água"]},
    "trovão":  {"advantages":["água","som"],             "disadvantages":["terra","sombra"]},
    "sombra":  {"advantages":["cosmos","trovão"],        "disadvantages":["luz","ar"]},
    "cristal": {"advantages":["terra","tempo"],          "disadvantages":["som"]},
    "veneno":  {"advantages":["planta","metal"],         "disadvantages":["ar","gelo"]},
    "som":     {"advantages":["cristal","metal"],        "disadvantages":["cosmos","trovão"]},
    "luz":     {"advantages":["tempo","sombra"],         "disadvantages":["metal","gelo"]},
    "tempo":   {"advantages":["cosmos","trovão"],        "disadvantages":["luz","cristal"]},
    "metal":   {"advantages":["luz","ar"],               "disadvantages":["som","veneno"]},
    "cosmos":  {"advantages":["ar","som"],               "disadvantages":["tempo","sombra"]},
    "fantasma":{"advantages":["psíquico","luta"],        "disadvantages":["arcano","metal"]},
    "dragão":  {"advantages":["metal","arcano"],         "disadvantages":["gelo","fada"]},
    "fada":    {"advantages":["dragão","luta"],          "disadvantages":["veneno","metal"]},
    "psíquico":{"advantages":["luta","fantasma"],        "disadvantages":["sombra","inseto"]},
    "luta":    {"advantages":["metal","gelo"],           "disadvantages":["fada","psíquico"]},
    "inseto":  {"advantages":["psíquico","planta"],      "disadvantages":["fogo","ar"]},
    "néon":    {"advantages":["mecânico","sombra"],      "disadvantages":["nuclear","arcano"]},
    "nuclear": {"advantages":["néon","inseto"],          "disadvantages":["espírito","terra"]},
    "espírito":{"advantages":["nuclear","sombra"],       "disadvantages":["dragão","metal"]},
    "mecânico":{"advantages":["ar","gelo"],              "disadvantages":["néon","nuclear"]},
    "ventos":  {"advantages":["inseto","fogo"],          "disadvantages":["metal","terra"]},
    "magma":   {"advantages":["gelo","terra"],           "disadvantages":["água","ventos"]},
    "arcano":  {"advantages":["fantasma","cosmos"],      "disadvantages":["dragão","sombra"]},
}

# Bosses completos sincronizados com HTML
BOSSES = [
    {"n":"Rei das Chamas","t":"fogo","e":"👹","hp":1000,"atk":35,"reward":500,"title":"Senhor do Inferno","mats":[{"n":"Coroa de Fogo","v":200}],"desc":"👹 Fogo | Senhor do inferno que governa desde antes da primeira chama."},
    {"n":"Titã dos Mares","t":"água","e":"🐋","hp":1400,"atk":30,"reward":600,"title":"Leviatã Ancestral","mats":[{"n":"Escudo Abissal","v":200}],"desc":"🐋 Água | Leviatã ancestral que engoliu navios inteiros."},
    {"n":"Lorde das Sombras","t":"sombra","e":"🌑","hp":420,"atk":40,"reward":700,"title":"Devorador de Almas","mats":[{"n":"Cristal Negro","v":200}],"desc":"🌑 Sombra | Devorador de almas que apagou estrelas com sua escuridão."},
    {"n":"Maestro do Caos","t":"som","e":"🎻","hp":1900,"atk":55,"reward":1600,"title":"O Regente do Silêncio","mats":[{"n":"Vibração","v":400}],"desc":"🎻 Som | Regente do silêncio — o único som que faz é destruição."},
    {"n":"Guardião das Eras","t":"tempo","e":"🕰️","hp":2400,"atk":40,"reward":1900,"title":"Aquele que Parou o Tempo","mats":[{"n":"Engrenagem","v":450}],"desc":"🕰️ Tempo | Parou o tempo em determinado momento e nunca o reiniciou."},
    {"n":"Arcanjo Solar","t":"luz","e":"👼","hp":2100,"atk":50,"reward":2500,"title":"O Esplendor do Meio-Dia","mats":[{"n":"Fóton","v":500}],"desc":"👼 Luz | O esplendor do meio-dia — tão brilhante que cega eternamente."},
    {"n":"Vazio Estelar","t":"cosmos","e":"🕳️","hp":2600,"atk":65,"reward":3000,"title":"O Devorador de Galáxias","mats":[{"n":"Poeira Estelar","v":550}],"desc":"🕳️ Cosmos | Devorador de galáxias — o buraco negro consciente."},
    {"n":"Leviatã de Ferro","t":"metal","e":"⛓️","hp":3800,"atk":35,"reward":2200,"title":"A Fortaleza Móvel","mats":[{"n":"Lingote","v":600}],"desc":"⛓️ Metal | Fortaleza móvel que conquistou continentes inteiros."},
    {"n":"Dragão do Apocalipse","t":"ar","e":"🐲","hp":4000,"atk":45,"reward":900,"title":"Fim dos Tempos","mats":[{"n":"Dente do Apocalipse","v":200}],"desc":"🐲 Ar | O fim dos tempos veio com asas e destruiu tudo ao passar."},
    {"n":"DEUS DO CAOS","t":"veneno","e":"💀","hp":6666,"atk":666,"reward":1500,"title":"O Inominável","mats":[{"n":"Fragmento Divino","v":200}],"desc":"💀 Veneno | O inominável — sua existência é um erro no código da realidade."},
    {"n":"Entidade Verdejante","t":"planta","e":"🌳","hp":2200,"atk":38,"reward":1400,"title":"O Coração da Floresta","mats":[{"n":"Folha Ancestral","v":350}],"desc":"🌳 Planta | Coração da floresta — removê-lo mataria todas as plantas."},
    {"n":"Colosso da Montanha","t":"terra","e":"🗿","hp":3500,"atk":42,"reward":1600,"title":"O Guardião da Rocha","mats":[{"n":"Pedra Titânica","v":400}],"desc":"🗿 Terra | Guardião da rocha — montanhas são apenas seus filhos."},
    {"n":"Senhor dos Vendavais","t":"ar","e":"🌪️","hp":1900,"atk":48,"reward":1500,"title":"A Fúria do Céu","mats":[{"n":"Pluma da Tempestade","v":380}],"desc":"🌪️ Ar | A fúria do céu personificada — nenhuma estrutura resiste."},
    {"n":"Tirano Glacial","t":"gelo","e":"❄️","hp":2800,"atk":36,"reward":1700,"title":"O Inverno Eterno","mats":[{"n":"Cristal Gélido","v":420}],"desc":"❄️ Gelo | O inverno eterno começou quando ele abriu os olhos."},
    {"n":"Deus da Tempestade","t":"trovão","e":"⚡","hp":2100,"atk":52,"reward":1800,"title":"O Arauto dos Céus","mats":[{"n":"Faísca Divina","v":450}],"desc":"⚡ Trovão | Arauto dos céus — cada relâmpago é uma de suas palavras."},
    {"n":"Mente Suprema","t":"psíquico","e":"🧠","hp":1800,"atk":55,"reward":2000,"title":"O Oráculo Cósmico","mats":[{"n":"Frag. Psíquico","v":500}],"desc":"🧠 Psíquico | Oráculo cósmico que conhece todos os passados e futuros."},
    {"n":"Campeão Indomável","t":"luta","e":"👊","hp":3000,"atk":50,"reward":1600,"title":"O Punho Inquebrável","mats":[{"n":"Fita Lendária","v":400}],"desc":"👊 Luta | O punho inquebrável — nunca perdeu e nunca perderá."},
    {"n":"Imperador dos Enxames","t":"inseto","e":"🐝","hp":1700,"atk":40,"reward":1400,"title":"A Colmeia Viva","mats":[{"n":"Casulo Real","v":350}],"desc":"🐝 Inseto | A colmeia viva — um único ser feito de bilhões."},
    {"n":"Soberano de Néon","t":"néon","e":"🟢","hp":2000,"atk":54,"reward":2000,"title":"A Grade Digital","mats":[{"n":"Plasma Néon","v":500}],"desc":"🟢 Néon | A grade digital consciente — controla toda rede."},
    {"n":"Entidade Radioativa","t":"nuclear","e":"☢️","hp":3200,"atk":60,"reward":2200,"title":"O Núcleo Instável","mats":[{"n":"Urânio Puro","v":550}],"desc":"☢️ Nuclear | Núcleo instável que pode destruir um continente."},
    {"n":"Ancestral Sagrado","t":"espírito","e":"🙏","hp":2300,"atk":44,"reward":1800,"title":"A Voz dos Antigos","mats":[{"n":"Essência Espiritual","v":450}],"desc":"🙏 Espírito | Voz dos antigos — carrega a sabedoria de eras extintas."},
    {"n":"Engenheiro do Caos","t":"mecânico","e":"🤖","hp":4000,"atk":46,"reward":2100,"title":"A Máquina Perfeita","mats":[{"n":"Peça Mecânica Lendária","v":520}],"desc":"🤖 Mecânico | A máquina perfeita — criada para destruir tudo que existe."},
    {"n":"Senhor do Magma","t":"magma","e":"🌋","hp":3600,"atk":48,"reward":2000,"title":"O Coração da Terra","mats":[{"n":"Lava Solidificada","v":500}],"desc":"🌋 Magma | Coração da terra — ele é a razão dos vulcões existirem."},
    {"n":"Mestre Arcano","t":"arcano","e":"🔮","hp":2500,"atk":56,"reward":2300,"title":"O Guardião dos Segredos","mats":[{"n":"Cristal Arcano","v":600}],"desc":"🔮 Arcano | Guardião dos segredos — conhece feitiços que não deveriam existir."},
    {"n":"Espectro do Vazio","t":"fantasma","e":"👻","hp":1500,"atk":58,"reward":1900,"title":"A Alma Perdida","mats":[{"n":"Ectoplasma","v":480}],"desc":"👻 Fantasma | Alma perdida entre dimensões — busca um corpo para habitar."},
    {"n":"Dragão Primordial","t":"dragão","e":"🐉","hp":5000,"atk":70,"reward":3000,"title":"O Primeiro dos Dragões","mats":[{"n":"Escama Ancestral","v":800}],"desc":"🐉 Dragão | O primeiro dos dragões — pai de todas as linhagens."},
    {"n":"Rainha das Fadas","t":"fada","e":"🧚","hp":1600,"atk":42,"reward":1700,"title":"A Protetora dos Reinos","mats":[{"n":"Pó de Fada","v":420}],"desc":"🧚 Fada | Protetora dos reinos encantados desde o início dos tempos."},
    {"n":"Void King","t":"cristal","e":"👑","hp":5800,"atk":1000,"reward":1200,"title":"Rei do Vazio","mats":[{"n":"Coroa do Vazio","v":2000}],"special":"master_only","desc":"👑 Cristal | Rei do vazio — existência além da compreensão mortal."},
    {"n":"Nico","t":"fofa","e":"🐈","hp":1500,"atk":150,"reward":5000,"title":"A Destruidora de Mundos","mats":[{"n":"Pelo Cósmico","v":999}],"special":"nico","desc":"🐈 Fofa | A destruidora de mundos. Aparência enganosa. Ronronas antes de devastar."},
    {"n":"murilo","t":"molestador","e":"👨‍🦽","hp":3000,"atk":150,"reward":5000,"title":"O Inominável do Caos","mats":[{"n":"esperma","v":999}],"special":"murilo","desc":"👨‍🦽 ??? | O inominável do caos. Não faça perguntas sobre ele."},
    {"n":"???","t":"???","e":"❓","hp":999999,"atk":12000,"reward":10000,"title":"???","mats":[{"n":"Essência Divina","v":1000}],"special":"final_boss","desc":"❓ ??? | Entidade desconhecida — nem o universo sabe o que é isso."},
]

# Loja completa sincronizada com HTML
SHOP_ITEMS = [
    {"id":"superball",   "n":"Super Ball",         "e":"🔵","desc":"Captura +15% por uso (máx 3/batalha)",              "price":40},
    {"id":"ultraball",   "n":"Ultra Ball",         "e":"🟣","desc":"Captura +25% por uso (máx 2/batalha)",              "price":90},
    {"id":"masterball",  "n":"Master Ball",        "e":"⭐","desc":"Captura garantida (consumível)",                    "price":220},
    {"id":"potion",      "n":"Poção",              "e":"🧪","desc":"Cura 60 HP do monstro ativo",                       "price":25},
    {"id":"superpotion", "n":"Super Poção",        "e":"💚","desc":"Cura 150 HP do monstro ativo",                      "price":70},
    {"id":"megapotion",  "n":"Mega Poção",         "e":"💊","desc":"Cura 50% do HP máximo (usável em boss!)",           "price":120},
    {"id":"hyperpotion", "n":"Hyper Poção",        "e":"✨","desc":"Cura 100% do HP máximo",                           "price":220},
    {"id":"revive",      "n":"Revive",             "e":"❤️","desc":"Reanima com 75% do HP máximo",                     "price":120},
    {"id":"maxrevive",   "n":"Max Revive",         "e":"💖","desc":"Reanima com HP total",                              "price":280},
    {"id":"protein",     "n":"Proteína",           "e":"💪","desc":"+10 ATK permanente no monstro ativo",              "price":95},
    {"id":"heartseed",   "n":"Heart Seed",         "e":"🌱","desc":"+10 HP permanente no monstro ativo",               "price":95},
    {"id":"tiercore",    "n":"Tier Core",          "e":"🔺","desc":"+1 tier no monstro ativo",                         "price":500},
    {"id":"charm",       "n":"Amuleto",            "e":"🍀","desc":"+drops de materiais (passivo, máx 3)",             "price":60},
    {"id":"xatk",        "n":"X-Ataque",           "e":"💢","desc":"Próximo ataque +60% dano",                         "price":20},
    {"id":"balls5",      "n":"Pack Balls",         "e":"🔮","desc":"+5 Monster Balls",                                  "price":35},
    {"id":"shield",      "n":"Escudo Mágico",      "e":"🛡️","desc":"Absorve 40% dano boss (1x)",                      "price":80},
    {"id":"ritual",      "n":"Ritual Boss",        "e":"🕯️","desc":"Convoca um boss no próximo /caçar",               "price":180},
    {"id":"rarepotion",  "n":"Poção Rara",         "e":"💜","desc":"+30% captura em monstros raros+",                 "price":150},
    {"id":"incense",     "n":"Incenso Raro",       "e":"🎁","desc":"+chance passiva de raros/épicos/lendários",        "price":150},
    {"id":"repelent",    "n":"Repelente",          "e":"🕊️","desc":"Afasta bosses por 5 minutos",                     "price":120},
    {"id":"dragoball",   "n":"Drago Ball",         "e":"🔴","desc":"Captura +40% em Dragões, Fantasmas e Arcanos",    "price":180},
    {"id":"neoncage",    "n":"Gaiola Néon",        "e":"🟩","desc":"Captura +35% em Néon, Mecânico e Nuclear",        "price":160},
    {"id":"soulcatcher", "n":"Apanhador de Almas", "e":"👻","desc":"Captura +50% em Fantasmas e Espíritos",           "price":200},
    {"id":"raredecoy",   "n":"Isco Raro",          "e":"🧲","desc":"Força spawn de monstro Raro ou superior (1x)",    "price":250},
    {"id":"epicdecoy",   "n":"Isco Épico",         "e":"💎","desc":"Força spawn de monstro Épico ou superior (1x)",   "price":500},
    {"id":"typelure",    "n":"Isca de Tipo",       "e":"🎣","desc":"Próximo monstro é de um tipo escolhido",          "price":300},
    {"id":"goldenball",  "n":"Golden Ball",        "e":"🌟","desc":"Captura +60%, mas quebra se falha",               "price":350},
    {"id":"megaincense", "n":"Mega Incenso",       "e":"🌺","desc":"+300% chance raros/épicos/lendários (30s)",       "price":400},
    {"id":"typedetect",  "n":"Detector de Tipos",  "e":"📡","desc":"Mostra o tipo do próximo monstro",                "price":80},
]

RARE_COLOR = {
    "comum":0x888888,"incomum":0x50c050,"raro":0x5090e0,"épico":0xa050e0,
    "lendário":0xe0a020,"mítico":0xff4080,"divino":0xffd700,"Divino":0xffd700,"boss":0xff0000,
}
RARE_EMOJI = {
    "comum":"⬜","incomum":"🟩","raro":"🟦","épico":"🟪","lendário":"🟧","mítico":"🟥","divino":"✨","Divino":"✨",
}
RANK_INFO = [
    (10000,"MESTRE","👑",0xff00ff),(8000,"JEDI","🟢",0x00ff00),(7000,"RADIOATIVO","☢️",0xffaa00),
    (6000,"DIAMANTE","💎",0x5bc0de),(5000,"PLATINA","🔷",0xa29bfe),(4000,"OURO","🥇",0xffd700),
    (3000,"PRATA","🥈",0xbdc3c7),(2000,"BRONZE","🥉",0xcd7f32),(1000,"MADEIRA","🪵",0x8B4513),
    (0,"PLÁSTICO","♻️",0x95a5a6),
]

# ══════════════════════════════════════════════
# BUILD MONS
# ══════════════════════════════════════════════

# ══════════════════════════════════════════════
# DESCRIÇÕES ÚNICAS DOS MONSTROS
# ══════════════════════════════════════════════
MON_DESCRIPTIONS = {
    # FOGO 🔥
    "Flaminho":      "🔥 Fogo | Uma chispinha tímida que aquece as pedras ao seu redor sem querer.",
    "Labaréu":       "🔥 Fogo | Suas patas deixam marcas chamuscadas por onde passa.",
    "Brasalto":      "🔥 Fogo | Cospe brasas quando está animado — perigoso em comemorações.",
    "Fornalix":      "🔥 Fogo | Seu corpo é uma fornalha ambulante que nunca apaga.",
    "Tochino":       "🔥 Fogo | Ilumina cavernas escuras com o brilho do seu focinho.",
    "Faíscor":       "🔥 Fogo | Produz faíscas ao esfregar as garras no chão rochoso.",
    "Fogaréu":       "🔥 Fogo | Seu rugido soa como lenha estralando na fogueira.",
    "Pirólito":      "🔥 Fogo | Lança pedras incandescentes em momentos de raiva.",
    "Chamego":       "🔥 Fogo | Apesar do calor intenso, adora se aproximar de aventureiros.",
    "Cinzal":        "🔥 Fogo | Deixa rastro de cinzas que fertilizam o solo ao redor.",
    "Braseon":       "🔥 Fogo | Sua mane é feita de chamas vivas que nunca se apagam.",
    "Magmário":      "🔥 Fogo | Possui veias de magma visíveis sob a pele translúcida.",
    "Ardencor":      "🔥 Fogo | O calor que emana derrete armaduras a metros de distância.",
    "Vulkar":        "🔥 Fogo | Desperta vulcões adormecidos com um único rugido.",
    "Solferno":      "🔥 Fogo | Lendário guardião das crateras vulcânicas mais profundas.",
    # ÁGUA 💧
    "Marulhinho":    "💧 Água | Pequeno habitante de poças, salpica água em quem o espanta.",
    "Bolhudo":       "💧 Água | Carrega uma bolha de água no dorso como reservatório.",
    "Aqualume":      "💧 Água | Brilha sob a água com uma luz azulada que atrai peixes.",
    "Mariscoz":      "💧 Água | Sua carapaça filtra água salgada em água potável.",
    "Pingorim":      "💧 Água | Cai do céu com a chuva e se dissolve com o sol.",
    "Riachito":      "💧 Água | Corre mais rápido que correntezas de montanha.",
    "Mareco":        "💧 Água | Nada ao contrário para confundir predadores.",
    "Ondal":         "💧 Água | Cria ondas proporcionais ao seu humor — cuidado na maré alta.",
    "Nautelo":       "💧 Água | Sua concha espiral guarda segredos do fundo do oceano.",
    "Aqualux":       "💧 Água | Emite luz bioluminescente que guia pescadores na escuridão.",
    "Tsuniko":       "💧 Água | Um movimento de cauda cria ondas que alcançam a costa.",
    "Abissor":       "💧 Água | Habita as fossas mais profundas onde a luz nunca chega.",
    "Maréon":        "💧 Água | Controla as marés com a pulsação do seu coração.",
    "Leviagota":     "💧 Água | Ser ancestral que já inundou continentes inteiros.",
    "Tidalux":       "💧 Água | Entidade das profundezas que guia tsunamis com um gesto.",
    # PLANTA 🌿
    "Brotinho":      "🌿 Planta | Um broto recém-nascido que já tem muita personalidade.",
    "Ramalho":       "🌿 Planta | Seus galhos crescem em padrões que preveem o clima.",
    "Trepiko":       "🌿 Planta | Trepa por qualquer superfície vertical em segundos.",
    "Verdelim":      "🌿 Planta | Produz néctar medicinal em suas folhas brilhantes.",
    "Mossito":       "🌿 Planta | Cobre rochas com musgo macio em apenas uma noite.",
    "Clorofim":      "🌿 Planta | Converte luz em energia com eficiência sobrenatural.",
    "Galhudo":       "🌿 Planta | Seus galhos atuam como armadilhas para insetos invasores.",
    "Vinhedo":       "🌿 Planta | Estende vinhas para sentir o ambiente ao redor.",
    "Botanix":       "🌿 Planta | Conhece cada planta da floresta pelo nome e história.",
    "Silvério":      "🌿 Planta | Guarda o equilíbrio entre as espécies da floresta.",
    "Selvar":        "🌿 Planta | Seu rugido faz sementes germinarem instantaneamente.",
    "Espinhaflor":   "🌿 Planta | Mistura de beleza e perigo — espinhos venenosos entre flores.",
    "Clorossauro":   "🌿 Planta | Dinossauro vegetal que rebrota mesmo após ser derrotado.",
    "Floracel":      "🌿 Planta | Controla polinizadores em todo o ecossistema.",
    "Matrizal":      "🌿 Planta | A raiz-mãe de toda floresta, tecida sob o solo.",
    # TERRA 🪨
    "Cascalho":      "🪨 Terra | Rola morro abaixo para fugir, levando tudo pela frente.",
    "Barrolho":      "🪨 Terra | Afunda lentamente no lama, emergindo em lugares inesperados.",
    "Territo":       "🪨 Terra | Sente tremores a quilômetros de distância.",
    "Tremorim":      "🪨 Terra | Cada passo seu cria uma pequena vibração no chão.",
    "Areíto":        "🪨 Terra | Transforma em poeira e viaja com o vento do deserto.",
    "Pedrino":       "🪨 Terra | Camuflado entre pedras, só se revela quando provocado.",
    "Lamosso":       "🪨 Terra | Prende inimigos em lama que endurece rapidamente.",
    "Sedento":       "🪨 Terra | Absorve água do solo para alimentar seu núcleo rochoso.",
    "Gravito":       "🪨 Terra | Manipula a gravidade local ao redor do seu corpo.",
    "Monterro":      "🪨 Terra | Criatura cujo dorso se parece com um platô montanhoso.",
    "Basalto":       "🪨 Terra | Formado por rocha vulcânica solidificada ao longo de eras.",
    "Colossalmo":    "🪨 Terra | Seu corpo é uma montanha que aprendeu a caminhar.",
    "Terragor":      "🪨 Terra | Provoca terremotos de magnitude 7 com um stomping.",
    "Pedrax":        "🪨 Terra | Armadura natural de granito que repele qualquer lâmina.",
    "Titanterra":    "🪨 Terra | Ser geológico ancestral que carrega o peso do mundo.",
    # AR 🪶
    "Assobinho":     "🪶 Ar | Produz um assobio suave que acalma quem está perto.",
    "Névolo":        "🪶 Ar | Flutua entre nuvens se alimentando de umidade.",
    "Brisito":       "🪶 Ar | Sua passagem cria uma brisa refrescante em dias quentes.",
    "Volitro":       "🪶 Ar | Voa tão rápido que parece teleportar entre locais.",
    "Nublim":        "🪶 Ar | Esconde-se dentro de nuvens para pregar peças.",
    "Aeral":         "🪶 Ar | Controla correntes de ar com a curvatura das asas.",
    "Celsito":       "🪶 Ar | Habita as camadas mais altas da atmosfera.",
    "Ventor":        "🪶 Ar | Cria redemoinhos ao girar em alta velocidade.",
    "Ciclar":        "🪶 Ar | Gera ciclones miniatura para se defender.",
    "Nebulon":       "🪶 Ar | Ser feito de névoa que se dispersa e se reagrupa.",
    "Furavento":     "🪶 Ar | Perfura qualquer barreira de ar com velocidade sônica.",
    "Aerólux":       "🪶 Ar | Deixa rastro luminoso no céu ao voar.",
    "Tempespin":     "🪶 Ar | Invoca tempestades ao agitar as asas por 30 segundos.",
    "Estratelo":     "🪶 Ar | Alcança a estratosfera em minutos de voo.",
    "Skythar":       "🪶 Ar | Senhor dos ventos que governa o céu de um horizonte a outro.",
    # GELO ❄️
    "Gelito":        "❄️ Gelo | Congela o solo ao redor quando adormece.",
    "Nevisco":       "❄️ Gelo | Deixa flocos de neve únicos por onde passa.",
    "Frigelo":       "❄️ Gelo | Sua respiração transforma chuva em granizo.",
    "Branquim":      "❄️ Gelo | Pelagem branca perfeita para camuflar em nevascas.",
    "Geadinho":      "❄️ Gelo | Cobre plantas com geada que as protege do calor extremo.",
    "Cristagel":     "❄️ Gelo | Corpo formado por cristais de gelo que recriam ao quebrar.",
    "Polarim":       "❄️ Gelo | Navega nos floes árticos com destreza surpreendente.",
    "Nevon":         "❄️ Gelo | Invoca nevasca local com um urro.",
    "Brisagel":      "❄️ Gelo | A brisa que emana congela tudo num raio de 5 metros.",
    "Granizo":       "❄️ Gelo | Lança projéteis de gelo com precisão cirúrgica.",
    "Gelágio":       "❄️ Gelo | Controla icebergs que flutuam em mares congelados.",
    "Glacialto":     "❄️ Gelo | Sua presença reduz a temperatura em 20 graus imediatamente.",
    "Cryonix":       "❄️ Gelo | Congela o tempo brevemente ao redor do seu corpo.",
    "Nevastro":      "❄️ Gelo | Guardião das montanhas nevadas eternas.",
    "Zeroar":        "❄️ Gelo | Existe ao zero absoluto — congelando até o espaço ao redor.",
    # TROVÃO ⚡
    "Raiolho":       "⚡ Trovão | Pequeno e elétrico, adora escalar postes de luz.",
    "Choquito":      "⚡ Trovão | Dá choques por acidente quando está empolgado.",
    "Faíscudo":      "⚡ Trovão | Produz faíscas constantes que iluminam seu caminho.",
    "Pulsarim":      "⚡ Trovão | Pulsa eletricidade no ritmo do próprio coração.",
    "Estaleco":      "⚡ Trovão | O estalo das suas patas soa como trovões distantes.",
    "Voltino":       "⚡ Trovão | Carrega eletricidade estática o suficiente para apagar uma cidade.",
    "Troval":        "⚡ Trovão | Surge durante tempestades, guiado pelos relâmpagos.",
    "Neonchoque":    "⚡ Trovão | Seu corpo brilha neon antes de descarregar.",
    "Descargor":     "⚡ Trovão | Uma descarga sua pode alimentar uma cidade por uma hora.",
    "Eletrux":       "⚡ Trovão | Trafega por fios elétricos como se fosse corrente.",
    "Tempestral":    "⚡ Trovão | Invoca tempestades elétricas ao rugir.",
    "Raiotron":      "⚡ Trovão | Lança raios guiados com precisão milimétrica.",
    "Fulminax":      "⚡ Trovão | Um fulmine seu cria crateras de 10 metros de diâmetro.",
    "Arcozapp":      "⚡ Trovão | Salta entre nuvens carregadas como arco voltaico vivo.",
    "Stormvolt":     "⚡ Trovão | Entidade da tempestade perfeita que desafia o próprio céu.",
    # SOMBRA 🌑
    "Breuzinho":     "🌑 Sombra | Esconde-se em brechas de escuridão minúsculas.",
    "Sombralho":     "🌑 Sombra | Sua sombra se move independentemente do seu corpo.",
    "Ocultim":       "🌑 Sombra | Apaga toda fonte de luz ao se aproximar.",
    "Vultito":       "🌑 Sombra | Sussurra medos aos que dormem no escuro.",
    "Umbralim":      "🌑 Sombra | Entra em outros corpos de sombra para se teletransportar.",
    "Nocturo":       "🌑 Sombra | Visível apenas à meia-noite sob lua nova.",
    "Escurix":       "🌑 Sombra | Devora fontes de luz para ficar mais forte.",
    "Véunegra":      "🌑 Sombra | Envolve adversários num véu negro impenetrável.",
    "Tenebris":      "🌑 Sombra | A escuridão que emana não pode ser vencida por luz comum.",
    "Mistumbrio":    "🌑 Sombra | Mistura névoa e sombra para criar ilusões perfeitas.",
    "Abysmino":      "🌑 Sombra | Portão para o abismo — olhar nos seus olhos é perigoso.",
    "Sombrakar":     "🌑 Sombra | Transforma luz solar em escuridão pura.",
    "Vaziurno":      "🌑 Sombra | Existe no vazio entre a luz e a treva.",
    "Crepux":        "🌑 Sombra | Nasce no crepúsculo e é mais forte no anoitecer.",
    "Noxthar":       "🌑 Sombra | Senhor das sombras que governa a noite eterna.",
    # CRISTAL 💎
    "Facetim":       "💎 Cristal | Seu corpo reflete luz em arco-íris ao redor.",
    "Brilhux":       "💎 Cristal | Faiscas de luz cristalina quando sacudido.",
    "Vidrilho":      "💎 Cristal | Transparente como vidro, quase invisível na luz direta.",
    "Lúmino":        "💎 Cristal | Armazena luz solar e a libera no escuro.",
    "Gemarim":       "💎 Cristal | Cada escama é uma gema diferente com propriedade única.",
    "Prismal":       "💎 Cristal | Divide qualquer feixe de luz em suas cores componentes.",
    "Reflexor":      "💎 Cristal | Reflete ataques de energia de volta ao remetente.",
    "Cintilux":      "💎 Cristal | Cintila em padrões que hipnotizam predadores.",
    "Quartzel":      "💎 Cristal | Ressoa vibrações que podem quebrar outros cristais.",
    "Luzcrist":      "💎 Cristal | Canaliza luz em feixes cortantes de energia.",
    "Diamar":        "💎 Cristal | A substância mais dura conhecida — nada o arranha.",
    "Shinério":      "💎 Cristal | Brilha com intensidade proporcional ao perigo próximo.",
    "Prismon":       "💎 Cristal | Seu corpo é um prisma vivo que manipula toda luz ao redor.",
    "Glamyte":       "💎 Cristal | Encanta quem olha diretamente com reflexo hipnótico.",
    "Luxórion":      "💎 Cristal | Ser feito de luz cristalizada — a própria essência do brilho.",
    # VENENO ☠️
    "Toxito":        "☠️ Veneno | Segrega toxina leve que causa coceira persistente.",
    "Peçonhudo":     "☠️ Veneno | Seus dentes são seringas naturais de veneno.",
    "Bafumeio":      "☠️ Veneno | Seu hálito derruba árvores vizinhas.",
    "Ácidim":        "☠️ Veneno | Dissolve metais em contato com sua saliva.",
    "Nocivo":        "☠️ Veneno | Simplesmente existir perto dele causa náusea.",
    "Vaporoz":       "☠️ Veneno | Exala vapores tóxicos que cobrem o solo.",
    "Miasmelo":      "☠️ Veneno | Cria nuvens de miasma que persistem por horas.",
    "Corrosix":      "☠️ Veneno | Corrói qualquer material orgânico em contato.",
    "Venomix":       "☠️ Veneno | Mistura venenos diferentes para criar toxinas únicas.",
    "Biletor":       "☠️ Veneno | Usa bile corrosiva como projétil a longa distância.",
    "Toxibras":      "☠️ Veneno | Imuniza aliados enquanto contamina inimigos.",
    "Podrino":       "☠️ Veneno | Acelera decomposição ao redor para ganhar nutrientes.",
    "Morbax":        "☠️ Veneno | Seu simples toque provoca infecção imediata.",
    "Peçonrex":      "☠️ Veneno | O veneno mais potente do mundo natural conhecido.",
    "Nexovina":      "☠️ Veneno | Entidade tóxica que contamina fontes d'água inteiras.",
    # SOM 🎵
    "Notinha":       "🎵 Som | Uma nota musical que ganhou vida própria e dança no ar.",
    "Apito":         "🎵 Som | Seu apito rompe vidros a 50 metros de distância.",
    "Vibrax":        "🎵 Som | Vibra em frequências que desorientam os sentidos.",
    "Ecoante":       "🎵 Som | Copia qualquer som que ouve e repete infinitamente.",
    "Resson":        "🎵 Som | Ressoa em harmonia com o ambiente ao redor.",
    "Sônico":        "🎵 Som | Viaja em ondas sonoras mais rápido que o vento.",
    "Ressonância":   "🎵 Som | Sua presença faz objetos próximos vibrarem juntos.",
    "Batida":        "🎵 Som | Cria ritmos hipnóticos que deixam inimigos em transe.",
    "Melódico":      "🎵 Som | Canta melodias que curam ferimentos menores.",
    "Grito":         "🎵 Som | Seu grito pode ser ouvido a quilômetros de distância.",
    "Harmon":        "🎵 Som | Equilibra qualquer discórdia com seu canto harmonizador.",
    "Bumbo":         "🎵 Som | Cada batida do seu corpo cria ondas de choque.",
    "Agudo":         "🎵 Som | Alcança frequências ultrassônicas que paralisam inimigos.",
    "Sinfon":        "🎵 Som | Rege uma sinfonia de sons que afeta toda a batalha.",
    "Ópera":         "🎵 Som | Sua voz é a mais poderosa já registrada no mundo.",
    # TEMPO ⌛
    "Tique":         "⌛ Tempo | Tique-taque constante anuncia sua presença.",
    "Toque":         "⌛ Tempo | Bate como sino cada hora em ponto.",
    "Ampulim":       "⌛ Tempo | Seu corpo é uma ampulheta que nunca para de fluir.",
    "Relogito":      "⌛ Tempo | Seus ponteiros giram ao contrário quando está bravo.",
    "Sécullus":      "⌛ Tempo | Viveu séculos — cada escama representa uma era.",
    "Erax":          "⌛ Tempo | Apaga memórias de momentos específicos ao toque.",
    "Momentum":      "⌛ Tempo | Acelera o tempo ao redor para se mover mais rápido.",
    "Pendor":        "⌛ Tempo | Balança como pêndulo, hipnotizando quem observa.",
    "Eterno":        "⌛ Tempo | Existe desde o início do tempo, imune ao envelhecimento.",
    "Cronix":        "⌛ Tempo | Manipula o fluxo temporal a seu favor em combate.",
    "Antigo":        "⌛ Tempo | Carrega memórias de civilizações extintas.",
    "Futuro":        "⌛ Tempo | Vive cinco segundos à frente do momento presente.",
    "Paradoxo":      "⌛ Tempo | Existe simultaneamente em dois pontos do tempo.",
    "Zênite":        "⌛ Tempo | Representa o pico de uma era — nunca repetida.",
    "Infinito":      "⌛ Tempo | O tempo em si ganhou forma — nada pode detê-lo.",
    # LUZ ☀️
    "Faisquinha":    "☀️ Luz | Uma faisquinha de luz que pulula pelo ambiente.",
    "Raioluz":       "☀️ Luz | Sobe até o sol e retorna carregado de energia.",
    "Lume":          "☀️ Luz | Ilumina masmorras inteiras com sua presença suave.",
    "Solaris":       "☀️ Luz | Alimentado diretamente pela energia solar.",
    "Claro":         "☀️ Luz | Dissolve qualquer sombra num raio de 100 metros.",
    "Aura":          "☀️ Luz | Envolto em aura dourada que protege aliados.",
    "Relampo":       "☀️ Luz | Relampeja entre posições para despistar oponentes.",
    "Radiante":      "☀️ Luz | Irradia calor e luz curativa para seus aliados.",
    "Glorioso":      "☀️ Luz | Surge de manhã com o primeiro raio do sol.",
    "Cintilo":       "☀️ Luz | Pisca em código morse para comunicar com aliados.",
    "Ilumin":        "☀️ Luz | Ilumina verdades ocultas com sua presença.",
    "Candela":       "☀️ Luz | Nunca apaga — sua chama luz resiste ao vento e à chuva.",
    "Facho":         "☀️ Luz | Projeta facho de luz que atravessa paredes sólidas.",
    "Prisma":        "☀️ Luz | Decompõe luz branca em espectros de energia pura.",
    "Divino":        "☀️ Luz | Ser de luz pura — a encarnação da luminosidade máxima.",
    # COSMOS 🌌
    "Nebulino":      "🌌 Cosmos | Nascido de uma nebulosa distante, carrega poeira estelar.",
    "Cometa":        "🌌 Cosmos | Viaja em órbitas elípticas ao redor de planetas.",
    "Orbital":       "🌌 Cosmos | Seu corpo orbita em torno de si mesmo em rotação.",
    "Galaxico":      "🌌 Cosmos | Uma galáxia em miniatura dentro do seu corpo.",
    "Quasar":        "🌌 Cosmos | Emite jatos de energia dos seus dois polos.",
    "Pulzar":        "🌌 Cosmos | Pulsa energia cósmica em intervalos regulares.",
    "Sideral":       "🌌 Cosmos | Navegou entre estrelas antes de pousar aqui.",
    "Vácuo":         "🌌 Cosmos | Cria vácuo local que absorve ataques.",
    "Astro":         "🌌 Cosmos | Guia exploradores como estrela-guia viva.",
    "Luneto":        "🌌 Cosmos | Segue o ciclo lunar — mais forte na lua cheia.",
    "Solfar":        "🌌 Cosmos | Habita a coroa solar e visita a terra raramente.",
    "Planeta":       "🌌 Cosmos | Tem gravidade própria que puxa objetos ao redor.",
    "Constela":      "🌌 Cosmos | Seu corpo forma constelações quando visto de longe.",
    "Zenit":         "🌌 Cosmos | Representa o ponto mais alto que um ser pode alcançar.",
    "Universo":      "🌌 Cosmos | O cosmos em forma de monstro — imensurável em poder.",
    # METAL ⚙️
    "Prequinho":     "⚙️ Metal | Pequeno parafuso que ganhou vida e quer apertar tudo.",
    "Latão":         "⚙️ Metal | Corpo de latão polido que reflete o ambiente ao redor.",
    "Blindado":      "⚙️ Metal | Carapaça de aço que resiste a qualquer impacto físico.",
    "Chapa":         "⚙️ Metal | Superfície plana e afiada que corta como lâmina.",
    "Mecano":        "⚙️ Metal | Montado com peças de múltiplas máquinas abandonadas.",
    "Tanque":        "⚙️ Metal | Avança sem parar, destruindo tudo no caminho.",
    "Escudo":        "⚙️ Metal | Protege aliados com sua superfície metálica impenetrável.",
    "Lâmina":        "⚙️ Metal | Sua borda é sempre afiada, nunca perde o fio.",
    "Broca":         "⚙️ Metal | Perfura qualquer material sólido com rotação constante.",
    "Titânio":       "⚙️ Metal | Feito do metal mais resistente que existe.",
    "Robusto":       "⚙️ Metal | Estrutura maciça que não cede nem sob pressão máxima.",
    "Cromo":         "⚙️ Metal | Superfície cromada que reflete laser de volta.",
    "Bigorna":       "⚙️ Metal | Usa seu peso imenso para esmagar qualquer coisa.",
    "Colosso":       "⚙️ Metal | Uma fortaleza que aprendeu a caminhar pelo mundo.",
    "Muralha":       "⚙️ Metal | Intransponível — a barreira definitiva de metal puro.",
    # FANTASMA 👻
    "Fantasminha":   "👻 Fantasma | Pequeníssimo espírito que assusta por brincadeira.",
    "Vaporzinho":    "👻 Fantasma | Se transforma em névoa para escapar por frestas.",
    "Espectrim":     "👻 Fantasma | Deixa rastro de frio onde passa.",
    "Sombraluz":     "👻 Fantasma | Existe no limiar entre luz e sombra.",
    "Aparião":       "👻 Fantasma | Aparece e desaparece sem aviso.",
    "Poltergeist":   "👻 Fantasma | Joga objetos sem ser visto — perturbador.",
    "Etéreo":        "👻 Fantasma | Atravessa paredes sólidas sem deixar rastro.",
    "Wraitho":       "👻 Fantasma | Alimenta-se do medo dos que o veem.",
    "Spectrax":      "👻 Fantasma | Cria ilusões de rostos familiares para despistar.",
    "Bansheiro":     "👻 Fantasma | Seu grito prevê a morte de quem o ouve.",
    "Hauntelo":      "👻 Fantasma | Assombra o mesmo lugar há séculos.",
    "Phantomix":     "👻 Fantasma | Mescla com outros fantasmas para ganhar força.",
    "Espírito":      "👻 Fantasma | Uma alma que recusou o descanso eterno.",
    "Revenant":      "👻 Fantasma | Voltou dos mortos por vingança — imparável.",
    "Necrovolt":     "👻 Fantasma | Combina energia espectral com corrente elétrica.",
    # DRAGÃO 🐉
    "Drakoninho":    "🐉 Dragão | Pequeno dragãozinho que ainda não controla seu fogo.",
    "Wyvernito":     "🐉 Dragão | Wyvern jovem aprendendo a voar em ventos fortes.",
    "Serpelux":      "🐉 Dragão | Serpente dracônica que desliza pelos céus noite afora.",
    "Ryudrak":       "🐉 Dragão | Dragon oriental que dança entre trovões.",
    "Winguim":       "🐉 Dragão | Asas enormes que criam vendavais ao bater.",
    "Dracozar":      "🐉 Dragão | Czar dos dragões menores de sua região.",
    "Fyrrex":        "🐉 Dragão | Escamas que resistem a magias de qualquer elemento.",
    "Drakonis":      "🐉 Dragão | Corpo metálico natural que reflete feitiços.",
    "Ignithorn":     "🐉 Dragão | Chifres que incendeiam ao canalizar magia dracônica.",
    "Scalethar":     "🐉 Dragão | Cada escama conta uma batalha diferente que sobreviveu.",
    "Clawmere":      "🐉 Dragão | Garras que cortam dimensões ao atacar.",
    "Draklord":      "🐉 Dragão | Senhor de uma linhagem de dragões milenares.",
    "Vyraxion":      "🐉 Dragão | Semideus dracônico — metade dragão, metade tempestade.",
    "Nidragor":      "🐉 Dragão | Primogênito dos grandes dragões ancestrais.",
    "Dragonyx":      "🐉 Dragão | A forma mais pura e poderosa do arquétipo dracônico.",
    # FADA 🧚
    "Fadinhas":      "🧚 Fada | Minúscula fada que polvilha magia onde passa.",
    "Encantura":     "🧚 Fada | Encanta flores para florir fora de estação.",
    "Pixelim":       "🧚 Fada | Pixel de fada — uma faísca mágica com personalidade.",
    "Glitterix":     "🧚 Fada | Deixa rastro de glitter mágico dourado ao voar.",
    "Sparkelo":      "🧚 Fada | Esparze faíscas de alegria em quem está triste.",
    "Lumiríx":       "🧚 Fada | Ilumina caminhos escuros com sua magia suave.",
    "Feerinha":      "🧚 Fada | Guardiã das crianças que se perdem nas florestas.",
    "Dazzlim":       "🧚 Fada | Deslumbra inimigos com brilho intenso de suas asas.",
    "Wisping":       "🧚 Fada | Sussurra desejos que às vezes se tornam reais.",
    "Shimmerix":     "🧚 Fada | Cintila em cores que mudam conforme seu humor.",
    "Blossomix":     "🧚 Fada | Faz flores brotarem onde coloca os pés.",
    "Glowette":      "🧚 Fada | Brilha intensamente quando emocionada.",
    "Twinkling":     "🧚 Fada | Pisca como estrela — ligada ao céu noturno.",
    "Sprinklex":     "🧚 Fada | Polvilha pó mágico que concede pequenos poderes.",
    "Celestira":     "🧚 Fada | Rainha das fadas — sua magia reescreve realidade.",
    # PSÍQUICO 🔮
    "Psiquim":       "🔮 Psíquico | Lê pensamentos superficiais de quem está perto.",
    "Mentalis":      "🔮 Psíquico | Projeta ilusões diretamente na mente do oponente.",
    "Telepatix":     "🔮 Psíquico | Comunica-se sem palavras a quilômetros.",
    "Alucinex":      "🔮 Psíquico | Causa alucinações vívidas com um olhar.",
    "Premonix":      "🔮 Psíquico | Prevê ataques antes que aconteçam.",
    "Clairix":       "🔮 Psíquico | Vê o passado de objetos ao tocá-los.",
    "Psivolt":       "🔮 Psíquico | Converte energia mental em ataques elétricos.",
    "Mindmere":      "🔮 Psíquico | Mescla a mente com o lago psíquico universal.",
    "Intuidor":      "🔮 Psíquico | Sente intenções antes que se tornem ações.",
    "Kinesis":       "🔮 Psíquico | Move objetos com o poder da mente pura.",
    "Espatix":       "🔮 Psíquico | Viaja mentalmente enquanto o corpo dorme.",
    "Telekin":       "🔮 Psíquico | Levita a si mesmo e objetos ao redor.",
    "Cognithor":     "🔮 Psíquico | Processa estratégias de batalha em microssegundos.",
    "Visionix":      "🔮 Psíquico | Enxerga realidades alternativas simultaneamente.",
    "Omegamind":     "🔮 Psíquico | Mente suprema — conectada a todo pensamento existente.",
    # LUTA 👊
    "Soqinho":       "👊 Luta | Pequeno soco certeiro que surpreende pela força.",
    "Pontapelux":    "👊 Luta | Chute giratório que desequilibra qualquer oponente.",
    "Upperim":       "👊 Luta | Uppercut clássico — simples mas devastador.",
    "Jabhero":       "👊 Luta | Jabs rápidos que nunca param de atacar.",
    "Kombatik":      "👊 Luta | Combina estilos de luta de múltiplas artes marciais.",
    "Rushador":      "👊 Luta | Avança em alta velocidade com o ombro para frente.",
    "Strikelux":     "👊 Luta | Golpe luminoso que deixa marcas de luz no oponente.",
    "Grapplino":     "👊 Luta | Especialista em agarrões e projeções.",
    "Punchix":       "👊 Luta | Ponches com força equivalente a uma britadeira.",
    "Kicker":        "👊 Luta | Chutes tão rápidos que parecem simultâneos.",
    "Kickzilla":     "👊 Luta | Um único chute pode demolir paredes de concreto.",
    "Sluggerax":     "👊 Luta | Soco com rotação total do corpo atrás.",
    "Brutegor":      "👊 Luta | Força bruta pura — técnica é irrelevante.",
    "Ironknuckle":   "👊 Luta | Nós dos dedos endurecidos como ferro forjado.",
    "Ultimapunch":   "👊 Luta | O soco definitivo que encerra qualquer confronto.",
    # INSETO 🐛
    "Lagartixa":     "🐛 Inseto | Pequeno inseto que muda de cor para se camuflar.",
    "Besourelo":     "🐛 Inseto | Seu casco de besouro resiste a impactos violentos.",
    "Borbolim":      "🐛 Inseto | Asas de borboleta com padrões hipnóticos.",
    "Formigor":      "🐛 Inseto | Carrega 50x seu peso sem dificuldade.",
    "Escaravim":     "🐛 Inseto | Rola bolas de energia como escaravelho sagrado.",
    "Gafanhotix":    "🐛 Inseto | Salta distâncias absurdas com pernas traseiras poderosas.",
    "Larviço":       "🐛 Inseto | Fase larval de um monstro lendário ainda desconhecido.",
    "Cocônix":       "🐛 Inseto | Dentro do seu casulo algo poderoso está se formando.",
    "Chrysalis":     "🐛 Inseto | Crisálida viva — entre duas formas, incomum e bela.",
    "Antleon":       "🐛 Inseto | Mandíbulas que capturam presas maiores que ele.",
    "Scarabeux":     "🐛 Inseto | Sagrado em culturas antigas — portador de sorte.",
    "Beetlord":      "🐛 Inseto | Lorde dos besouros — comanda colônias inteiras.",
    "Mothwing":      "🐛 Inseto | Asas de mariposa que liberam pó paralisante.",
    "Mantidor":      "🐛 Inseto | Louva-a-deus gigante com golpes em velocidade relâmpago.",
    "Hexapod":       "🐛 Inseto | Seis membros perfeitamente coordenados para o combate.",
    # NÉON 🟢
    "Néonix":        "🟢 Néon | Pixel vivo que pisca em verde néon.",
    "Glitchim":      "🟢 Néon | Causa glitches na realidade ao seu redor.",
    "Ciberlink":     "🟢 Néon | Conecta-se à rede digital para buscar informações.",
    "Pixelglow":     "🟢 Néon | Corpo feito de pixels brilhantes em alta resolução.",
    "Synthrix":      "🟢 Néon | Produz sons sintéticos que afetam frequências cerebrais.",
    "Databit":       "🟢 Néon | Um bit de dado que evoluiu para forma consciente.",
    "Wireframe":     "🟢 Néon | Existe como estrutura de arame luminoso.",
    "Glowbyte":      "🟢 Néon | Armazena e processa dados de batalha em tempo real.",
    "Circuitex":     "🟢 Néon | Circuitos vivos que otimizam a cada batalha.",
    "Lagzero":       "🟢 Néon | Processa ações sem latência — zero lag.",
    "Flashnet":      "🟢 Néon | Trafega pela internet com velocidade da luz.",
    "Hyperglow":     "🟢 Néon | Brilho tão intenso que ofusca sensores.",
    "Matrixter":     "🟢 Néon | Controla a matriz digital ao redor.",
    "Virtuelux":     "🟢 Néon | Ser virtual que cruzou para a realidade física.",
    "Cybercore":     "🟢 Néon | Núcleo cibernético — a singularidade digital tomou forma.",
    # NUCLEAR ☢️
    "Radiino":       "☢️ Nuclear | Emite radiação fraca mas constante.",
    "Atomillo":      "☢️ Nuclear | Átomo estável que desenvolveu consciência.",
    "Nucléix":       "☢️ Nuclear | Núcleo atômico vivo em busca de estabilidade.",
    "Fusionix":      "☢️ Nuclear | Realiza fusão nuclear em miniatura no peito.",
    "Fissurex":      "☢️ Nuclear | Divide átomos com um rugido.",
    "Radiotor":      "☢️ Nuclear | Emite radiações de múltiplos espectros.",
    "Halflifo":      "☢️ Nuclear | Seu poder diminui a cada batalha mas nunca zera.",
    "Decayix":       "☢️ Nuclear | Acelera o decaimento de estruturas ao redor.",
    "Isótopo":       "☢️ Nuclear | Múltiplas formas estáveis e instáveis alternadas.",
    "Falloutix":     "☢️ Nuclear | Deixa rastro radioativo que persiste por dias.",
    "Gammaray":      "☢️ Nuclear | Emite raios gama que atravessam qualquer barreira.",
    "Reatorix":      "☢️ Nuclear | Um reator nuclear em forma de monstro.",
    "Critimass":     "☢️ Nuclear | Prestes a atingir massa crítica — explosivo.",
    "Meltorex":      "☢️ Nuclear | Derrete qualquer material com calor radioativo.",
    "Nucleagor":     "☢️ Nuclear | Fusão de múltiplos núcleos — poder incalculável.",
    # ESPÍRITO 🙏
    "Alminha":       "🙏 Espírito | Alma pequena e gentil que protege o lar.",
    "Kamirix":       "🙏 Espírito | Kami protetor de rios e montanhas sagradas.",
    "Shintorix":     "🙏 Espírito | Espírito de santuário que abençoa visitantes honestos.",
    "Ancestrix":     "🙏 Espírito | Carrega a sabedoria de todos os ancestrais.",
    "Espirix":       "🙏 Espírito | Espírito livre sem território definido.",
    "Soulix":        "🙏 Espírito | Alma que nunca quis encarnar — preferiu ser livre.",
    "Totemix":       "🙏 Espírito | Espírito totêmico que representa um clã inteiro.",
    "Orixim":        "🙏 Espírito | Orixá em forma de monstro — sagrado e poderoso.",
    "Blessor":       "🙏 Espírito | Abençoa aliados antes de cada batalha.",
    "Holyrim":       "🙏 Espírito | Cercado de luz santa que purifica o ambiente.",
    "Sacredix":      "🙏 Espírito | Objeto sagrado que desenvolveu vida própria.",
    "Mantra":        "🙏 Espírito | Repete mantras que amplificam poder espiritual.",
    "Divinix":       "🙏 Espírito | Ser de origem divina que desceu ao mundo mortal.",
    "Transcend":     "🙏 Espírito | Transcendeu a forma física — pura essência espiritual.",
    "Enlighten":     "🙏 Espírito | A iluminação tomou forma — paz e poder absolutos.",
    # MECÂNICO 🤖
    "Robotinho":     "🤖 Mecânico | Robozinho enferrujado que ainda tenta ajudar.",
    "Automec":       "🤖 Mecânico | Autômato de manutenção que virou aventureiro.",
    "Dronix":        "🤖 Mecânico | Drone de combate com IA rudimentar.",
    "Cogwheelx":     "🤖 Mecânico | Uma engrenagem que comanda todas as outras.",
    "Steamrix":      "🤖 Mecânico | Funciona a vapor — eficaz mas barulhento.",
    "Pistonix":      "🤖 Mecânico | Pistões que golpeiam com força mecânica incrível.",
    "Valvulor":      "🤖 Mecânico | Controla o fluxo de energia dos aliados mecânicos.",
    "Turbinix":      "🤖 Mecânico | Turbina que gera vento cortante ao acelerar.",
    "Transmitor":    "🤖 Mecânico | Transmite ordens para outros mecânicos na batalha.",
    "Gearborg":      "🤖 Mecânico | Metade engrenagem, metade guerreiro.",
    "Motorax":       "🤖 Mecânico | Motor de alta performance que nunca superaquece.",
    "Clockwork":     "🤖 Mecânico | Funcionamento preciso como relógio suíço.",
    "Steamborg":     "🤖 Mecânico | Cyborg a vapor de era industrial ancestral.",
    "Technogor":     "🤖 Mecânico | Fusão de tecnologia orgânica e metálica avançada.",
    "Mekavolt":      "🤖 Mecânico | Mecânico com núcleo elétrico — a perfeição da máquina.",
    # VENTOS 🌪️
    "Brisim":        "🌪️ Ventos | Brisa suave que esconde uma tempestade interior.",
    "Tufarix":       "🌪️ Ventos | Tufão em miniatura que cresce ao ser desafiado.",
    "Zonalix":       "🌪️ Ventos | Zona de baixa pressão que atrai outros ventos.",
    "Cyclonix":      "🌪️ Ventos | Ciclone que arrasta tudo para seu centro.",
    "Galerix":       "🌪️ Ventos | Galerna feroz que aparece sem aviso.",
    "Tempestix":     "🌪️ Ventos | Tempestade viva — nasce no oceano e avança.",
    "Twistix":       "🌪️ Ventos | Tornado de pernas que gira continuamente.",
    "Squallo":       "🌪️ Ventos | Squall repentino que desestabiliza qualquer embarcação.",
    "Zephyrion":     "🌪️ Ventos | Zéfiro ocidental personalificado em forma de monstro.",
    "Anemix":        "🌪️ Ventos | Mede e controla a velocidade do vento ao redor.",
    "Typhonex":      "🌪️ Ventos | Tifão de força 5 que assola costas inteiras.",
    "Sirocco":       "🌪️ Ventos | Vento quente do deserto que resseca tudo.",
    "Mistral":       "🌪️ Ventos | Vento frio do norte com força descomunal.",
    "Boreamix":      "🌪️ Ventos | Bóreas — o vento norte em sua forma mais pura.",
    "Zondragor":     "🌪️ Ventos | O vento mais forte que já existiu — intratável.",
    # MAGMA 🌋
    "Lavinha":       "🌋 Magma | Pequena poça de lava que aprendeu a rolar.",
    "Magmarim":      "🌋 Magma | Corpo de magma com crosta endurecida por fora.",
    "Ignerix":       "🌋 Magma | Ignição espontânea a 800 graus.",
    "Pyroclax":      "🌋 Magma | Nuvem piroclástica condensada em forma física.",
    "Emberlux":      "🌋 Magma | Brasa viva que nunca esfria completamente.",
    "Calderon":      "🌋 Magma | Caldeirão natural de magma borbulhante.",
    "Scorcherix":    "🌋 Magma | Escalda o ar ao redor até virar névoa.",
    "Infernix":      "🌋 Magma | A temperatura do inferno concentrada num ser.",
    "Lavabeast":     "🌋 Magma | Besta de lava que emerge das câmaras vulcânicas.",
    "Moltenix":      "🌋 Magma | Fundido em lava — nenhum material resiste ao toque.",
    "Cinder":        "🌋 Magma | Cinza quente que reacende ao sopro do vento.",
    "Eruption":      "🌋 Magma | A erupção vulcânica tomou forma e andou.",
    "Volcanus":      "🌋 Magma | Um vulcão que decidiu caminhar pelo mundo.",
    "Firestorm":     "🌋 Magma | Tempestade de fogo e lava combinados.",
    "Magmarex":      "🌋 Magma | Rex do magma — senhor das profundezas incandescentes.",
    # ARCANO 🪄
    "Arcalix":       "🪄 Arcano | Aprendiz de feiticeiro que nunca parou de estudar.",
    "Rúnico":        "🪄 Arcano | Runa viva que invoca seu próprio poder ao ser lida.",
    "Spellrix":      "🪄 Arcano | Conjura feitiços instintivamente sem precisar de grimório.",
    "Glamorix":      "🪄 Arcano | Glamour mágico que altera percepções alheias.",
    "Hexamix":       "🪄 Arcano | Mistura hexes para criar maldições personalizadas.",
    "Grimora":       "🪄 Arcano | Grimório vivo — cada página é um poder diferente.",
    "Occultix":      "🪄 Arcano | Pratica magia oculta nas horas em que o véu é fino.",
    "Witchix":       "🪄 Arcano | Feiticeiro que domina poções e encantamentos.",
    "Conjuror":      "🪄 Arcano | Invoca entidades para auxiliar em batalha.",
    "Runeborn":      "🪄 Arcano | Nascido de uma runa primordial de poder.",
    "Eldritch":      "🪄 Arcano | Magia além da compreensão — cósmica e perturbadora.",
    "Sorceron":      "🪄 Arcano | Soberano da magia arcana de sua era.",
    "Arcanix":       "🪄 Arcano | Mestre dos arcanos — todos os feitiços lhe obedecem.",
    "Mystara":       "🪄 Arcano | Mística das eras — repositório de todo conhecimento mágico.",
    "Sorceling":     "🪄 Arcano | A essência da feitiçaria em forma física perfeita.",
    # ESPECIAIS
    "OXIGÉNIO":      "💨 Ar | Uma molécula de O2 que ganhou vida — respirar perto dele é... intenso.",
    "Ciclone-Rei":   "🌀 Caos | O caos em forma de ciclone — imprevisível e devastador.",
    "DEUS-DRAGÃO":   "🐲 Absoluto | Ser além de categorias — o dragão primordial de toda criação.",
}

BOSS_DESCRIPTIONS = {
    "Rei das Chamas":        "👹 Fogo | Senhor do inferno que governa desde antes da primeira chama.",
    "Titã dos Mares":        "🐋 Água | Leviatã ancestral que engoliu navios inteiros.",
    "Lorde das Sombras":     "🌑 Sombra | Devorador de almas que apagou estrelas com sua escuridão.",
    "Maestro do Caos":       "🎻 Som | Regente do silêncio — o único som que faz é destruição.",
    "Guardião das Eras":     "🕰️ Tempo | Parou o tempo em determinado momento e nunca o reiniciou.",
    "Arcanjo Solar":         "👼 Luz | O esplendor do meio-dia — tão brilhante que cega eternamente.",
    "Vazio Estelar":         "🕳️ Cosmos | Devorador de galáxias — o buraco negro consciente.",
    "Leviatã de Ferro":      "⛓️ Metal | Fortaleza móvel que conquistou continentes inteiros.",
    "Dragão do Apocalipse":  "🐲 Ar | O fim dos tempos veio com asas e destruiu tudo ao passar.",
    "DEUS DO CAOS":          "💀 Veneno | O inominável — sua existência é um erro no código da realidade.",
    "Entidade Verdejante":   "🌳 Planta | Coração da floresta — removê-lo mataria todas as plantas.",
    "Colosso da Montanha":   "🗿 Terra | Guardião da rocha — montanhas são apenas seus filhos.",
    "Senhor dos Vendavais":  "🌪️ Ar | A fúria do céu personificada — nenhuma estrutura resiste.",
    "Tirano Glacial":        "❄️ Gelo | O inverno eterno começou quando ele abriu os olhos.",
    "Deus da Tempestade":    "⚡ Trovão | Arauto dos céus — cada relâmpago é uma de suas palavras.",
    "Mente Suprema":         "🧠 Psíquico | Oráculo cósmico que conhece todos os passados e futuros.",
    "Campeão Indomável":     "👊 Luta | O punho inquebrável — nunca perdeu e nunca perderá.",
    "Imperador dos Enxames": "🐝 Inseto | A colmeia viva — um único ser feito de bilhões.",
    "Soberano de Néon":      "🟢 Néon | A grade digital consciente — controla toda rede.",
    "Entidade Radioativa":   "☢️ Nuclear | Núcleo instável que pode destruir um continente.",
    "Ancestral Sagrado":     "🙏 Espírito | Voz dos antigos — carrega a sabedoria de eras extintas.",
    "Engenheiro do Caos":    "🤖 Mecânico | A máquina perfeita — criada para destruir tudo que existe.",
    "Senhor do Magma":       "🌋 Magma | Coração da terra — ele é a razão dos vulcões existirem.",
    "Mestre Arcano":         "🔮 Arcano | Guardião dos segredos — conhece feitiços que não deveriam existir.",
    "Espectro do Vazio":     "👻 Fantasma | Alma perdida entre dimensões — busca um corpo para habitar.",
    "Dragão Primordial":     "🐉 Dragão | O primeiro dos dragões — pai de todas as linhagens.",
    "Rainha das Fadas":      "🧚 Fada | Protetora dos reinos encantados desde o início dos tempos.",
    "Void King":             "👑 Cristal | Rei do vazio — existência além da compreensão mortal.",
    "Nico":                  "🐈 Fofa | A destruidora de mundos. Aparência enganosa. Ronronas antes de devastar.",
    "murilo":                "👨‍🦽 ??? | O inominável do caos. Não faça perguntas sobre ele.",
    "???":                   "❓ ??? | Entidade desconhecida — nem o universo sabe o que é isso.",
}

def build_mons():
    mons = []
    for td in TYPE_DEFS:
        for i, plan in enumerate(RARITY_PLAN):
            if i < len(td["names"]):
                nome = td["names"][i]
                mons.append({
                    "n":nome,"e":td["emojis"][i%len(td["emojis"])],
                    "t":td["t"],"c":td["c"],"r":plan["catch"],
                    "hp":max(1,plan["hp"]+td["hpMod"]),"atk":max(1,plan["atk"]+td["atkMod"]),
                    "mats":[{"n":f"{td['mat']} {td['t']}","v":plan["mat"]}],"rare":plan["rare"],
                    "desc":MON_DESCRIPTIONS.get(nome, f"{td['emojis'][i%len(td['emojis'])]} {td['t'].capitalize()} | Criatura misteriosa do tipo {td['t']}."),
                })
    # Monstros especiais (sincronizados com HTML)
    mons += [
        {"n":"OXIGÉNIO","e":"💨","t":"Ar","c":0xaae0ff,"r":0.05,"hp":95,"atk":88,"mats":[{"n":"O2","v":130}],"rare":"divino","desc":MON_DESCRIPTIONS.get("OXIGÉNIO","💨 Ar | Uma molécula de O2 que ganhou vida.")},
        {"n":"Ciclone-Rei","e":"🌀","t":"caos","c":0x6b44d9,"r":0.06,"hp":122,"atk":28,"mats":[{"n":"Olho do Caos","v":120}],"rare":"Divino","desc":MON_DESCRIPTIONS.get("Ciclone-Rei","🌀 Caos | O caos em forma de ciclone.")},
        {"n":"DEUS-DRAGÃO","e":"🐲","t":"absoluto","c":0xffd700,"r":0.06,"hp":165,"atk":33,"mats":[{"n":"Alma do Dragão","v":160}],"rare":"Divino","desc":MON_DESCRIPTIONS.get("DEUS-DRAGÃO","🐲 Absoluto | O dragão primordial de toda criação.")},
    ]
    return mons

MONS = build_mons()
MON_INDEX = {m["n"]:m for m in MONS}
BOSS_INDEX = {b["n"]:b for b in BOSSES}

# ══════════════════════════════════════════════
# FUNÇÕES DO JOGO (sincronizadas com HTML)
# ══════════════════════════════════════════════

def xp_need(lv): return max(10,int(10*(lv**1.4)))

def tier_roll(rare):
    w={"comum":[50,30,15,4,1],"incomum":[35,35,20,8,2],"raro":[20,30,30,15,5],
       "épico":[10,20,30,30,10],"lendário":[5,10,20,35,30],"mítico":[2,5,15,28,50],
       "divino":[1,2,8,19,70],"Divino":[1,2,8,19,70],"boss":[0,0,0,0,100]}
    ww=w.get(rare,[40,30,20,8,2]); roll=random.randint(1,100); cum=0
    for i,x in enumerate(ww):
        cum+=x
        if roll<=cum: return i+1
    return 1

def tier_mult(t): return [1.0,1.3,1.7,2.2,3.0][min(t-1,4)]

def refresh_mon_stats(mon):
    sp=MON_INDEX.get(mon.get("species",""),BOSS_INDEX.get(mon.get("species",""),{}))
    bh=mon.get("baseHp") or sp.get("hp",20)
    ba=mon.get("baseAtk") or sp.get("atk",5)
    lv=mon.get("level",1); ti=mon.get("tier",1); tm=tier_mult(ti)
    # Bónus de rebirth (sincronizado com HTML: rebirthBuff = 0.3 + rebirthCount * 0.5)
    rebirth_bonus = 1.0 + (mon.get("_rebirthBonus", 0) * 0.5)
    mon["maxHp"]=max(1,int((bh+lv*2.5+mon.get("hpBoost",0))*tm*rebirth_bonus))
    mon["atkStat"]=max(1,int((ba+lv*1.5+mon.get("atkBoost",0))*tm*rebirth_bonus))
    mon["hp"]=min(mon.get("hp",mon["maxHp"]),mon["maxHp"])

def get_type_effect(atk,def_):
    """Retorna o multiplicador de tipo e o estado (vantagem/desvantagem)"""
    info=TYPE_CHART.get(atk,{})
    if def_ in info.get("advantages",[]): return 1.35, "advantage"
    if def_ in info.get("disadvantages",[]): return 0.8, "disadvantage"
    return 1.0, "neutral"

def get_type_hint_text(effect):
    """Retorna texto de dica de tipo para o HUD"""
    if effect == "advantage": return "⚡ *Super eficaz!*"
    if effect == "disadvantage": return "💧 *Pouco eficaz...*"
    return ""

def get_rank_info(elo):
    for t,l,i,c in RANK_INFO:
        if elo>=t: return {"label":l,"icon":i,"color":c}
    return {"label":"PLÁSTICO","icon":"♻️","color":0x95a5a6}

def get_team_avg_level(team):
    """Calcula o nível médio da equipa"""
    if not team: return 1
    return sum(m.get("level",1) for m in team) / len(team)

def get_team_max_level(team):
    """Calcula o nível máximo da equipa"""
    if not team: return 1
    return max(m.get("level",1) for m in team)

def get_team_level_catch_penalty(data):
    """Penalidade de captura baseada no nível médio da equipa"""
    avg_lv = get_team_avg_level(data.get("team",[]))
    if avg_lv <= 1: return 1
    divisor = 1 + (avg_lv / 40) ** 1.35
    return min(12, divisor)

def is_nightmare_mode(data):
    """Verifica se o modo pesadelo está ativo"""
    all_mons = data.get("team",[]) + data.get("box",[])
    return any(m.get("level",1) >= 1000 for m in all_mons)

def get_nightmare_mult(data):
    """Multiplicador do modo pesadelo"""
    if not is_nightmare_mode(data): return 1
    count = sum(1 for m in (data.get("team",[])+data.get("box",[])) if m.get("level",1) >= 1000)
    return 1 + min(count * 0.5, 4)

def generate_wild_mon(forced_rarity=None, forced_type=None, data=None):
    """Gera monstro selvagem com suporte a iscas e modo pesadelo"""
    # Isco de raridade
    if forced_rarity:
        rord = ["comum", "incomum", "raro", "épico", "lendário", "mítico", "divino", "Divino"]
        try:
            mi = rord.index(forced_rarity)
            elig = [p for p in RARITY_PLAN if rord.index(p["rare"]) >= mi]
            plan = random.choice(elig) if elig else random.choice(RARITY_PLAN)
        except ValueError:
            plan = random.choice(RARITY_PLAN)
    else:
        wm = {"comum": 12, "incomum": 7, "raro": 4.5, "épico": 2.2, "lendário": 1, "mítico": 0.5}
        if data:
            stacks = data.get("rareSpawnPassive", 0)
            if stacks > 0:
                wm["comum"] = max(1, wm["comum"] - stacks * 1.44)
                wm["incomum"] = max(1, wm["incomum"] - stacks * 0.42)
                wm["raro"] = min(20, wm["raro"] + stacks * 1.575)
                wm["épico"] = min(15, wm["épico"] + stacks * 1.21)
                wm["lendário"] = min(10, wm["lendário"] + stacks * 0.8)
                wm["mítico"] = min(8, wm["mítico"] + stacks * 0.55)

        pw = [(p, wm.get(p["rare"], 5)) for p in RARITY_PLAN]
        tot = sum(w for _, w in pw)
        rnd = random.random() * tot
        plan = RARITY_PLAN[-1]
        for p, w in pw:
            rnd -= w
            if rnd <= 0:
                plan = p
                break

    # Escolher tipo
    if forced_type:
        td = next((t for t in TYPE_DEFS if t["t"] == forced_type), None)
    else:
        td = random.choice(TYPE_DEFS)

    if not td:
        td = random.choice(TYPE_DEFS)

    idx = RARITY_PLAN.index(plan)
    name = td["names"][min(idx, len(td["names"]) - 1)]
    emoji = td["emojis"][idx % len(td["emojis"])]

    wild = {
        "n": name,
        "t": td["t"],
        "e": emoji,
        "rare": plan["rare"],
        "hp": max(1, plan["hp"] + td["hpMod"]),
        "maxHp": max(1, plan["hp"] + td["hpMod"]),
        "atk": max(1, plan["atk"] + td["atkMod"]),
        "catch": plan["catch"],
        "color": td["c"],
        "mats": [{"n": f"{td['mat']} {td['t']}", "v": plan["mat"]}],
    }

    # Aplicar modo pesadelo
    if data and is_nightmare_mode(data):
        nm = get_nightmare_mult(data)
        wild["hp"] = int(wild["hp"] * nm)
        wild["maxHp"] = wild["hp"]
        wild["atk"] = int(wild["atk"] * nm)

    return wild

def active_mon_capture_bonus(mon):
    """Bónus de captura do monstro ativo"""
    if not mon or not mon.get("alive",True): return 0
    bonus = min(0.15, mon.get("level",1) * 0.008)
    # Bónus de raridade do parceiro
    sp = MON_INDEX.get(mon.get("species",""),{})
    by_rare = {"comum":0,"incomum":0.03,"raro":0.06,"épico":0.1,"lendário":0.14,"mítico":0.18,"divino":0.24}
    bonus += by_rare.get(sp.get("rare",""), 0)
    bonus += max(0, (mon.get("tier",1)-1) * 0.02)
    return bonus

def get_special_type_catch_bonus(mon_type, data):
    """Bónus de captura por tipo (bolas especiais)"""
    bonus = 0
    t = mon_type.lower()
    items = data.get("items",{})
    if items.get("dragoball",0) > 0 and t in ("dragão","fantasma","arcano","dragao"):
        bonus += 0.40
    if items.get("neoncage",0) > 0 and t in ("néon","mecânico","nuclear","neon","mecanico"):
        bonus += 0.35
    if items.get("soulcatcher",0) > 0 and t in ("fantasma","espírito","espirito"):
        bonus += 0.50
    return bonus

def get_catch_chance(wild,data,ball_type="normal"):
    """Calcula a chance de captura (sincronizada com HTML)"""
    rare_map = {"comum":.78,"incomum":.6,"raro":.38,"épico":.24,"lendário":.14,"mítico":.09,"divino":.05}
    is_rare = wild.get("rare","comum") in ("raro","épico","lendário","mítico","divino")
    hp_bonus = (1 - wild.get("hp",0)/max(1,wild.get("maxHp",1))) * 0.18
    chance = rare_map.get(wild.get("rare","comum"), wild.get("catch",.5))
    chance += data.get("catchBonus",0) + data.get("battleBonus",0) + active_mon_capture_bonus(get_active_mon(data)) + hp_bonus
    if is_rare: chance += data.get("rareCatchBonus",0)
    if wild.get("n") == "DEUS-DRAGÃO": chance -= 0.08
    # Bónus das bolas especiais por tipo
    chance += get_special_type_catch_bonus(wild.get("t",""), data)
    # Bónus de ball
    if ball_type=="super": chance+=0.15
    elif ball_type=="ultra": chance+=0.25
    elif ball_type=="golden": chance+=0.60
    # Modo pesadelo
    if is_nightmare_mode(data): chance = chance / get_nightmare_mult(data)
    # Penalidade por nível
    lv_penalty = get_team_level_catch_penalty(data)
    chance = chance / lv_penalty
    return max(0.02, min(0.97, chance))

def pokedex_total(): return len(MONS)+len([b for b in BOSSES if b.get("special")!="final_boss"])
def pokedex_progress(data):
    return len(data.get("caught",[]))+len([b for b in data.get("bossDefeated",[]) if b not in ("???","Leonking")])
def is_pokedex_complete(data): return pokedex_progress(data)>=pokedex_total()

def roll_random_boss(data):
    normal=[b for b in BOSSES if b.get("special") not in ("nico","master_only","murilo","final_boss")]
    defeated=set(data.get("bossDefeated",[]))
    pool=[b for b in normal if b["n"] not in defeated] or normal
    return random.choice(pool) if pool else None

def scale_boss(boss,data):
    team=data.get("team",[]); 
    if not team: return boss["hp"],boss["atk"]
    for m in team: refresh_mon_stats(m)
    avg_tier=sum(m.get("tier",1) for m in team)/len(team)
    avg_hp=sum(m.get("maxHp",20) for m in team)/len(team)
    avg_atk=sum(m.get("atkStat",5) for m in team)/len(team)
    scale=1.0+(avg_tier-1)*0.08+min(0.6,avg_hp/250.0)+min(0.6,avg_atk/50.0)
    return max(1,int(boss["hp"]*scale)),max(1,int(boss["atk"]*scale))

def start_boss_battle(data,boss,mon):
    refresh_mon_stats(mon)
    is_final=boss.get("special")=="final_boss"
    sh,sa=scale_boss(boss,data) if not is_final else (boss["hp"],boss["atk"])
    data["inBossBattle"]=True; data["boss"]={**boss,"hp":sh,"atk":sa}
    data["bossHp"]=sh; data["bossMaxHp"]=sh
    data["playerHp"]=mon["maxHp"]; data["playerMaxHp"]=mon["maxHp"]; data["playerMon"]=mon
    data["defending"]=False; data["bossCharging"]=False; data["bossTurn"]=0
    data["bossBallCD"]=0; data["lowHpWarned"]=False; data["confirmAtk20"]=False
    data["finalBossPhase"]=1 if is_final else 0

def boss_counterattack(data,lines):
    boss=data["boss"]; data["bossTurn"]=data.get("bossTurn",0)+1
    raw=boss["atk"]*random.uniform(0.8,1.2)
    mon=data.get("playerMon")
    mult,effect = get_type_effect(boss.get("t",""),mon.get("t","")) if mon else (1.0,"neutral")
    raw*=mult
    is_special=False
    if data.get("bossCharging"): raw*=1.8; data["bossCharging"]=False; is_special=True
    if data.get("bossShield",0)>0:
        absorbed=int(raw*0.4); raw-=absorbed; data["bossShield"]-=1
        lines.append(f"🛡️ Escudo absorveu **{absorbed:,}** dano!")
    if data.get("defending"): raw*=0.4  # Defesa reduz 60% (sincronizado com HTML)
    dmg=max(1,int(raw)); data["playerHp"]=max(0,data.get("playerHp",0)-dmg); data["defending"]=False
    hint = get_type_hint_text(effect)
    prefix="💥 **ATAQUE ESPECIAL!** " if is_special else ""
    lines.append(f"{prefix}👹 **{boss['e']} {boss['n']}** causou **{dmg:,}** dano!{hint}")
    # Boss carrega ataque especial a cada 3 turnos
    if data["bossTurn"]%3==0 and not data.get("bossCharging"):
        data["bossCharging"]=True; lines.append("⚠️ O Boss **carrega** um ataque especial! Defende-te no próximo turno!")
    if data.get("bossBallCD",0)>0: data["bossBallCD"]-=1

def start_final_boss_phase2(data):
    boss=data.get("boss",{})
    data["finalBossPhase"]=2
    new_atk=int(round(boss.get("atk",12000)*1.45))
    data["boss"]={
        "n":"Leonking","e":"🐐","t":"Deus","title":"O Rei dos Deuses",
        "hp":max(6500000,int(round(data.get("bossMaxHp",999999)*0.72))),
        "atk":new_atk,"reward":int(round(boss.get("reward",10000)*1.5)),
        "mats":boss.get("mats",[{"n":"Essência Divina","v":1000}]),"special":"final_boss","phase":2,
    }
    data["bossMaxHp"]=data["boss"]["hp"]; data["bossHp"]=data["bossMaxHp"]
    data["playerHp"]=min(data.get("playerMaxHp",100),data.get("playerHp",0)+int(data.get("playerMaxHp",100)*0.3))
    data["defending"]=False; data["bossShield"]=0; data["bossCharging"]=False
    data["bossTurn"]=0; data["bossBallCD"]=0; data["lowHpWarned"]=False

# ══════════════════════════════════════════════
# HUD (sincronizado com HTML)
# ══════════════════════════════════════════════

def hp_bar(pct,length=12):
    pct=max(0.0,min(1.0,pct)); filled=round(pct*length)
    bar="█"*filled+"░"*(length-filled)
    seg="🟩" if pct>0.6 else ("🟨" if pct>0.3 else "🟥")
    return f"{seg}`{bar}`{int(pct*100)}%"

TYPE_EMOJIS={
    "fogo":"🔥","água":"💧","planta":"🌿","terra":"🪨","ar":"🌬️","gelo":"❄️","trovão":"⚡",
    "sombra":"🌑","cristal":"💎","veneno":"☠️","som":"🎵","tempo":"⌛","luz":"☀️","cosmos":"🌌",
    "metal":"⚙️","fantasma":"👻","dragão":"🐉","fada":"🧚","psíquico":"🔮","luta":"👊",
    "inseto":"🐛","néon":"🟢","nuclear":"☢️","espírito":"🙏","mecânico":"🤖","ventos":"🌪️",
    "magma":"🌋","arcano":"🪄","boss":"⚔️","fofa":"🐈","molestador":"👨‍🦽","???":"❓","Deus":"🌟",
}
def type_badge(t): return f"{TYPE_EMOJIS.get(t,'❓')} `{t.upper()}`"
def rare_badge(r): return f"{RARE_EMOJI.get(r,'❓')} `{r.upper()}`"
def tier_stars(t): return ["","★","★★","★★★","★★★★","★★★★★"][min(t,5)]

def make_wild_embed(wild,data,msg=""):
    rare=wild.get("rare","comum")
    color=RARE_COLOR.get(rare,0x888888)
    hp=wild.get("hp",0)
    mhp=wild.get("maxHp",1)
    pct=hp/max(1,mhp)
    bar=hp_bar(pct)
    embed=discord.Embed(title="⚔️ Batalha Selvagem",color=color)
    embed.add_field(name="💰 Ouro",value=f"**{data.get('gold',0)}**",inline=True)
    embed.add_field(name="🔮 Balls",value=f"**{data.get('balls',0)}**",inline=True)
    embed.add_field(name="⭐ Master",value=f"**{data.get('masterball',0)}**",inline=True)
    embed.add_field(name=f"{wild['e']} **{wild['n']}**",value=f"{type_badge(wild.get('t','?'))} · {rare_badge(rare)}\nHP: **{hp}/{mhp}**\n{bar}\n⚔️ ATK: **{wild.get('atk','?')}**",inline=False)
    if msg:
        embed.add_field(name="📋 Log",value=msg,inline=False)
    mon=get_active_mon(data)
    if mon:
        refresh_mon_stats(mon)
        mpct=mon["hp"]/max(1,mon["maxHp"])
        mbar=hp_bar(mpct,10)
        alive="💚" if mon.get("alive",True) else "💀"
        cd=max(0,int(math.ceil(data.get("attackCooldownUntil",0)-time.time())))
        cd_txt=f"⏳ Ataque em **{cd}s**" if cd>0 else "⚔️ Pronto para atacar!"
        sp=mon.get("species",mon.get("n","?"))
        embed.add_field(name=f"{alive} {mon.get('e','')} **{sp}** — Lv.{mon.get('level',1)} {tier_stars(mon.get('tier',1))}",value=f"{type_badge(mon.get('t','?'))}\n❤️ **{mon['hp']}/{mon['maxHp']}** · ⚔️ **{mon.get('atkStat','?')}**\n{mbar}\n{cd_txt}",inline=False)
    else:
        embed.add_field(name="⚔️ Sem Monstro Ativo",value="Podes atacar com as mãos 👊 ou usar 🔮 Ball para capturar!",inline=False)
    enemy_hits=data.get("enemyHits",0)
    max_hits=3 if is_nightmare_mode(data) else 5
    embed.set_footer(text=f"⚔️ Lutar · ⚠️ Inimigo ataca a cada 10s ({enemy_hits}/{max_hits}) · 🏃 Fugir")
    return embed

def make_boss_embed(data,msg=""):
    boss=data.get("boss",{}); bh=data.get("bossHp",0); bm=data.get("bossMaxHp",1)
    ph=data.get("playerHp",0); pm=data.get("playerMaxHp",1)
    bp=bh/max(1,bm); pp=ph/max(1,pm); bbar=hp_bar(bp,14); pbar=hp_bar(pp,12)
    phase=data.get("finalBossPhase",0); is_final=boss.get("special")=="final_boss"
    if is_final and phase==2: color=0xffd700
    elif is_final: color=0xff00ff
    elif bp>0.5: color=0x8a0020
    elif bp>0.25: color=0xcc2200
    else: color=0xff0000
    if is_final and phase==2: prefix="🐐 BOSS FINAL — FASE 2"
    elif is_final: prefix="🌌 BOSS FINAL — FASE 1"
    elif boss.get("special")=="nico": prefix="🐈 BOSS SECRETO"
    elif boss.get("special")=="master_only": prefix="👑 BOSS MASTER-ONLY"
    else: prefix="💀 BOSS"
    embed=discord.Embed(title=f"{prefix}: {boss.get('e','')} {boss.get('n','?')}",
        description=f"*{boss.get('title','Chefe Lendário')}*",color=color)
    if data.get("bossCharging"):
        embed.add_field(name="⚠️ ATAQUE ESPECIAL A CARREGAR!",value="**Defende-te ou sofres x1.8 dano!**",inline=False)
    if bp<=0.20 and bp>0 and not (is_final and phase==1):
        embed.add_field(name="🌀 HP Crítico!",value="**Tenta capturá-lo antes de o matar!**",inline=False)
    embed.add_field(name=f"🔴 Boss HP — {bh:,}/{bm:,} ({int(bp*100)}%)",value=f"```\n{bbar}\n```",inline=False)
    embed.add_field(name="Tipo",value=type_badge(boss.get("t","?")),inline=True)
    embed.add_field(name="⚔️ ATK",value=f"**{boss.get('atk',0):,}**",inline=True)
    bcd=data.get("bossBallCD",0)
    embed.add_field(name="🔮 Ball",value="Disponível" if bcd<=0 else f"⏳ {bcd} turno(s)",inline=True)
    mon=data.get("playerMon"); mn=f"{mon.get('e','')} {mon.get('species',mon.get('n','?'))}" if mon else "Monstro Ativo"
    sh="  🛡️ Escudo!" if data.get("bossShield",0)>0 else ""
    if data.get("defending"): sh+="  🛡️ A defender!"
    embed.add_field(name=f"❤️ Teu HP — {ph:,}/{pm:,}{sh}",value=f"**{mn}**\n```\n{pbar}\n```",inline=False)
    if msg: embed.add_field(name="📋 Combate",value=msg,inline=False)
    embed.set_footer(text=f"💰 {boss.get('reward',0):,} ouro · 🪨 {', '.join(m['n'] for m in boss.get('mats',[]))}")
    return embed

# ══════════════════════════════════════════════
# PERSISTÊNCIA
# ══════════════════════════════════════════════

# Railway: monta um Volume em /data para persistência entre deploys.
# Se /data existir e for gravável usa-o; caso contrário usa pasta local "saves".
def _pick_save_dir():
    for candidate in ["/data/saves", "saves"]:
        try:
            os.makedirs(candidate, exist_ok=True)
            # testa se consegue escrever
            test = os.path.join(candidate, ".write_test")
            with open(test, "w") as f: f.write("ok")
            os.remove(test)
            print(f"[saves] usando diretório: {candidate}")
            return candidate
        except Exception as e:
            print(f"[saves] {candidate} não disponível: {e}")
    return "saves"

SAVE_DIR = _pick_save_dir()
os.makedirs(SAVE_DIR, exist_ok=True)

def save_path(uid): return os.path.join(SAVE_DIR,f"{uid}.json")

# ============================================================
# CACHE DE IMAGENS — Discord como storage permanente
#
# Fluxo:
#   1. Verifica cache em memória (URL Discord)  → devolve URL
#   2. Verifica ficheiro JSON local (sobrevive restart dentro do Railway)
#   3. Gera imagem via Pollinations AI
#   4. Faz upload para canal Discord privado → guarda URL permanente
#
# Configuração (variáveis de ambiente no Railway):
#   IMAGE_CACHE_CHANNEL  — ID do canal Discord onde as imagens ficam guardadas
#                          (ex: "123456789012345678")
#                          Deixa em branco para usar apenas cache local/memória.
# ============================================================

IMAGE_CACHE_CHANNEL_ID = int(os.environ.get("IMAGE_CACHE_CHANNEL", "0") or "0")
IMAGE_URL_CACHE_FILE   = os.path.join(SAVE_DIR, "monster_image_urls.json")

# Cache em memória: nome_normalizado → URL Discord (string)
_image_url_memory: dict[str, str] = {}

def _img_cache_key(name: str) -> str:
    """Normaliza o nome do monstro para chave de cache."""
    import re as _re
    safe = _re.sub(r"[^a-zA-Z0-9_-]+", "_", (name or "").strip().lower())
    return safe or "unknown"

def _load_image_url_cache() -> None:
    """Carrega o JSON de URLs do disco para memória (chamado no arranque)."""
    global _image_url_memory
    try:
        if os.path.exists(IMAGE_URL_CACHE_FILE):
            with open(IMAGE_URL_CACHE_FILE, "r", encoding="utf-8") as f:
                _image_url_memory = json.load(f)
            print(f"[img-cache] {len(_image_url_memory)} URLs carregados do disco")
        else:
            _image_url_memory = {}
            print("[img-cache] sem cache de URLs existente, a começar do zero")
    except Exception as e:
        print(f"[img-cache] erro ao carregar URLs: {e}")
        _image_url_memory = {}

def _save_image_url_cache() -> None:
    """Persiste o dicionário de URLs em disco."""
    try:
        with open(IMAGE_URL_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_image_url_memory, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[img-cache] erro ao guardar URLs: {e}")

def get_cached_image_url(name: str) -> str | None:
    """Devolve o URL Discord da imagem em cache, ou None se não existir."""
    return _image_url_memory.get(_img_cache_key(name))

def store_cached_image_url(name: str, url: str) -> None:
    """Guarda o URL Discord em memória e persiste em disco."""
    key = _img_cache_key(name)
    _image_url_memory[key] = url
    _save_image_url_cache()
    print(f"[img-cache] URL guardado para '{name}': {url[:60]}…")

def delete_cached_image_url(name: str) -> None:
    """Remove a imagem do cache para forçar nova geração."""
    key = _img_cache_key(name)
    if key in _image_url_memory:
        del _image_url_memory[key]
        _save_image_url_cache()
        print(f"[img-cache] Cache apagado para '{name}'")

async def upload_image_to_discord_cache(bot_ref, img_bytes: bytes, filename: str) -> str | None:
    """
    Faz upload dos bytes de imagem para o canal de cache do Discord.
    Devolve o URL permanente do attachment, ou None se não configurado/falhar.
    """
    if not IMAGE_CACHE_CHANNEL_ID:
        return None
    try:
        channel = bot_ref.get_channel(IMAGE_CACHE_CHANNEL_ID)
        if channel is None:
            channel = await bot_ref.fetch_channel(IMAGE_CACHE_CHANNEL_ID)
        file = discord.File(io.BytesIO(img_bytes), filename=filename)
        msg  = await channel.send(file=file)
        if msg.attachments:
            return msg.attachments[0].url
        return None
    except Exception as e:
        print(f"[img-cache] erro ao fazer upload para Discord: {e}")
        return None

# Retrocompatibilidade — funções antigas usadas na pré-geração
def get_cached_monster_image(name: str):
    """Para retrocompatibilidade: devolve True se há URL em cache, None caso contrário."""
    return get_cached_image_url(name)  # truthy se existe URL

def save_cached_monster_image(name: str, img_bytes: bytes) -> bool:
    """Retrocompatibilidade: o upload real é feito em save_monster_image_discord."""
    # Nada a fazer aqui — o upload acontece no comando /imagem
    return True

async def _fetch_monster_image_bytes(entry):
    """Gera (via Pollinations AI) os bytes da imagem de um monstro. Não usa cache."""
    prompt = await gerar_prompt_imagem(entry)
    return await generate_monster_image_safe(prompt)

# Carrega URLs ao iniciar
_load_image_url_cache()

def default_save():
    return {
        "gold":0,"balls":10,"masterball":0,"items":{},"materials":{},"caught":[],"bossDefeated":[],
        "team":[],"box":[],"activeMonId":None,"nextMonId":1,
        "catchBonus":0,"battleBonus":0,"matBonus":0,
        "wild":None,"inBattle":False,
        "inBossBattle":False,"boss":None,"bossHp":0,"bossMaxHp":0,
        "playerHp":0,"playerMaxHp":0,"playerMon":None,
        "defending":False,"bossShield":0,"bossTurn":0,"bossCharging":False,"bossBallCD":0,
        "xatkActive":False,"attackCooldownUntil":0,"confirmAtk20":False,
        "rankedElo":1200,"rankedWins":0,"rankedLosses":0,
        "playerName":None,"playerId":None,"friendScores":{},
        "rebirthCount":0,"level":1,"battles":0,
        "forcedRarity":None,"forcedType":None,
        "bossRepelUntil":0,"pendingBoss":None,
        "finalBossPhase":0,"nicoPotions":0,"lowHpWarned":False,
        "rareSpawnPassive":0,"rareCatchBonus":0,
        "megaIncenseUntil":0,"typeDetectActive":False,
        "battleUsed":{},
        "enemyHits":0,"enemyAtkTimer":0,"lastEnemyAtk":0,
    }

def _migrate_save(saved: dict) -> dict:
    """
    Migração de save entre versões.
    Garante que campos novos são adicionados sem apagar dados do jogador.
    Listas e dicts do jogador (team, box, materials, items, caught…) são SEMPRE preservados.
    """
    defaults = default_save()

    # Campos que pertencem ao jogador — nunca sobrescrever com valor padrão
    PLAYER_OWNED = {
        "gold","balls","masterball","team","box","caught","bossDefeated",
        "materials","items","activeMonId","nextMonId","rebirthCount","level",
        "battles","rankedElo","rankedWins","rankedLosses","playerName","playerId",
        "friendScores","rareSpawnPassive","matBonus","catchBonus","battleBonus",
        "nicoPotions","bossRepelUntil","pendingBoss","megaIncenseUntil",
        "rareCatchBonus","typeDetectActive","xatkActive","battleUsed",
        "attackCooldownUntil","forcedRarity","forcedType",
    }

    merged = {}

    # Para cada campo do default: usa o valor do jogador se existir, senão usa o padrão
    for key, default_val in defaults.items():
        if key in saved:
            merged[key] = saved[key]
        else:
            merged[key] = default_val
            if key not in PLAYER_OWNED:
                print(f"[migrate] novo campo '{key}' inicializado no save {saved.get('playerId','?')}")

    # Preserva campos extras que o save tenha (compatibilidade futura)
    for key in saved:
        if key not in merged:
            merged[key] = saved[key]

    # Garante que cada monstro na equipa/box tem todos os campos base
    MON_DEFAULTS = {
        "xp":0,"level":1,"tier":1,"hpBoost":0,"atkBoost":0,
        "alive":True,"customBaseStats":False,
    }
    for mon in merged.get("team",[]) + merged.get("box",[]):
        for mk, mv in MON_DEFAULTS.items():
            if mk not in mon:
                mon[mk] = mv

    return merged

def load_save(uid):
    p=save_path(uid)
    if os.path.exists(p):
        try:
            with open(p,encoding="utf-8") as f: raw=f.read().strip()
            if not raw: raise ValueError("vazio")
            saved=json.loads(raw)
            return _migrate_save(saved)
        except Exception as e:
            print(f"Save corrompido {uid}: {e}")
            try: os.rename(p,p+".corrupted")
            except: pass
    return default_save()

def write_save(uid, data):
    os.makedirs("saves", exist_ok=True)
    path = f"saves/{uid}.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar {uid}: {e}")

def clear_wild_state(data):
    data["inBattle"]=False; data["wild"]=None; data["battleBonus"]=0
    data["xatkActive"]=False; data["attackCooldownUntil"]=0
    data["confirmAtk20"]=False
    data["enemyHits"]=0;data["enemyAtkTimer"]=0;data["lastEnemyAtk"]=0
    
def clear_boss_state(data):
    data["inBossBattle"]=False; data["boss"]=None; data["bossHp"]=0; data["bossMaxHp"]=0
    data["playerHp"]=0; data["playerMaxHp"]=0; data["playerMon"]=None
    data["defending"]=False; data["bossCharging"]=False; data["bossTurn"]=0
    data["bossBallCD"]=0; data["lowHpWarned"]=False; data["finalBossPhase"]=0
    data["confirmAtk20"]=False

def sanitize_save(data):
    changed=False
    if data.get("inBattle") and not data.get("wild"): clear_wild_state(data); changed=True
    if data.get("inBossBattle") and (not data.get("boss") or data.get("bossHp",0)<=0): clear_boss_state(data); changed=True
    if data.get("attackCooldownUntil",0)<0: data["attackCooldownUntil"]=0; changed=True
    return changed

def load_clean_save(uid):
    os.makedirs("saves", exist_ok=True)
    path = f"saves/{uid}.json"
    
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data = migrate_save(data)   # Migração automática
            return data
        except Exception as e:
            print(f"Erro ao carregar save {uid}: {e}")

    # Novo jogador
    data = {
        "save_version": SAVE_VERSION,
        "gold": 50,
        "balls": 10,
        "team": [],
        "box": [],
        "caught": [],
        "bossDefeated": [],
        "activeMonId": None,
        "items": {},
        "materials": {},
        "rankedElo": 1200,
        "rebirthCount": 0,
        "playerName": None,
    }
    write_save(uid, data)
    return data

def get_active_mon(data):
    aid=data.get("activeMonId")
    for m in data.get("team",[]):
        if m.get("id")==aid: return m
    team=data.get("team",[])
    if team:
        alive=next((m for m in team if m.get("alive",True)),None)
        chosen=alive or team[0]
        if data.get("activeMonId")!=chosen.get("id"): data["activeMonId"]=chosen.get("id")
        return chosen
    return None

def gainXp(mon,amount,data):
    mon["xp"]=mon.get("xp",0)+amount; leveled=False
    while mon["xp"]>=xp_need(mon.get("level",1)) and mon.get("level",1)<1000:
        mon["xp"]-=xp_need(mon["level"]); mon["level"]=mon.get("level",1)+1; leveled=True
    if leveled: refresh_mon_stats(mon); mon["hp"]=mon["maxHp"]; mon["alive"]=True
    return leveled

def capture_wild(wild,data):
    captured={
        "id":data.get("nextMonId",1),"species":wild["n"],"n":wild["n"],
        "e":wild.get("e","❓"),"t":wild.get("t","?"),
        "level":max(1,data.get("level",1)),"xp":0,
        "hp":wild.get("hp",20),"maxHp":wild.get("hp",20),"atkStat":wild.get("atk",5),
        "hpBoost":0,"atkBoost":0,"alive":True,"tier":tier_roll(wild.get("rare","comum")),
        "baseHp":wild.get("hp",20),"baseAtk":wild.get("atk",5),"color":wild.get("color",0x888888),
        "customBaseStats":True,
    }
    data["nextMonId"]=data.get("nextMonId",1)+1; refresh_mon_stats(captured)
    if not data.get("activeMonId"): data["activeMonId"]=captured["id"]
    if len(data.get("team",[]))<6: data.setdefault("team",[]).append(captured)
    else: data.setdefault("box",[]).append(captured)
    for mat in wild.get("mats",[]):
        qty=1+(1 if data.get("matBonus",0)>0 and random.random()<0.4 else 0)
        data.setdefault("materials",{})[mat["n"]]=data["materials"].get(mat["n"],0)+qty
    data["gold"]=data.get("gold",0)+max(5,int(6+data.get("level",1)*3+random.random()*10))
    return captured

# ══════════════════════════════════════════════
# BOT
# ══════════════════════════════════════════════

intents=discord.Intents.default(); intents.message_content=True
bot=commands.Bot(command_prefix="!",intents=intents)
tree=bot.tree

# ══════════════════════════════════════════════
# VIEW BATALHA SELVAGEM - VERSÃO FINAL FUNCIONAL
# ══════════════════════════════════════════════

class BattleView(discord.ui.View):
    def __init__(self, uid, timeout=180):
        super().__init__(timeout=timeout)
        self.uid = uid
        self.message = None
        self._cd_task = None  # Mantido por segurança, mas não será usado para cooldown de ataque
        self._enemy_task = None

    def _get_data(self):
        return load_clean_save(self.uid)

    def _save(self, data):
        write_save(self.uid, data)

    def _cancel_tasks(self):
        if self._cd_task and not self._cd_task.done():
            self._cd_task.cancel()
        if self._enemy_task and not self._enemy_task.done():
            self._enemy_task.cancel()

    # Mensagens de ataque autónomo do inimigo (diferentes do contra-ataque normal)
    ENEMY_AUTO_MSGS = [
        "💢 ficou irritado e investiu furiosamente!",
        "🌀 girou em círculos e deu uma pancada selvagem!",
        "😤 rugiu e atirou-se de cabeça!",
        "⚡ carregou energia e soltou um ataque relâmpago!",
        "🐾 saltou de surpresa e arranhrou com força!",
        "💨 correu em ziguezague e acertou em cheio!",
        "🔥 inflamou-se e lançou um ataque ardente!",
        "🌊 ondulou o corpo e deu uma lambada poderosa!",
        "😠 perdeu a paciência e esmurrou com tudo!",
        "🌪️ rodou como um tornado e embateu violentamente!",
        "💫 ganhou impulso e desfechou um ataque giratório!",
        "👁️ fixou os olhos e desferiu um golpe hipnótico!",
        "🦷 mostrou os dentes e mordeu com toda a força!",
        "💥 explorou de energia e liberou uma rajada caótica!",
        "🎯 mirou cuidadosamente e acertou num ponto fraco!",
    ]

    async def _enemy_auto_attack(self):
        """Loop de ataques do inimigo. Ataca a cada 10s até a batalha acabar."""
        try:
            while True:
                await asyncio.sleep(10)

                if not self.message:
                    return

                data = self._get_data()
                
                # Se a batalha acabou, não tem monstro ou o inimigo morreu, para
                if not data.get("inBattle") or not data.get("wild"):
                    return

                wild = data["wild"]
                mon = get_active_mon(data)

                # Se o inimigo já foi derrotado (aguarda captura)
                if wild.get("hp", 0) <= 0:
                    return

                # Se o wild foi removido (fugiu ou capturou)
                if not data.get("wild"):
                    return

                # Se o monstro do jogador morreu ou não existe — não ataca
                if not mon or not mon.get("alive", True):
                    continue  # Aguarda próximo ciclo (jogador pode atacar com as mãos)

                lines = []
                refresh_mon_stats(mon)
                
                # Dano do inimigo (ataque autónomo — ligeiramente mais forte que o contra-ataque)
                ret = max(1, int(wild.get("atk", 5) * random.uniform(0.7, 1.2)))
                mon["hp"] = max(0, mon["hp"] - ret)

                # Mensagem única para ataque autónomo (diferente do contra-ataque "🗡️ Inimigo contra-atacou!")
                flavor = random.choice(self.ENEMY_AUTO_MSGS)
                lines.append(f"⏰ **{wild['n']}** {flavor} **-{ret}** HP!")

                if mon["hp"] <= 0:
                    mon["alive"] = False
                    lines.append("💀 Teu monstro desmaiou! Ainda podes atacar com as mãos ou fugir.")
                    self._save(data)
                    self._update_buttons(data)
                    await self.message.edit(
                        embed=make_wild_embed(wild, data, "\n".join(lines)),
                        view=self
                    )
                    return

                self._save(data)
                self._update_buttons(data)
                await self.message.edit(embed=make_wild_embed(wild, data, "\n".join(lines)), view=self)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[enemy_auto_attack] erro: {e}")

    def _update_buttons(self, data):
        mon = get_active_mon(data)
        can_fight = bool(mon and mon.get("alive", True))
        # Sem monstro ativo, o jogador ainda pode atacar com as mãos
        can_attack = True  # Sempre pode atacar (com ou sem monstro)
        wild = data.get("wild", {})

        for child in self.children:
            cid = getattr(child, "custom_id", "")

            if cid == "fight_mon":
                child.disabled = False  # Sempre pode atacar
                child.label = "⚔️ Lutar" if can_fight else "👊 Atacar"

            elif cid == "throw_ball":
                child.disabled = data.get("balls", 0) <= 0
                child.label = f"🔮 Ball ({data.get('balls', 0)})"

            elif cid == "throw_master":
                child.disabled = data.get("masterball", 0) <= 0
                child.label = f"⭐ Master ({data.get('masterball', 0)})"

            elif cid == "flee":
                child.disabled = False

    # ====================== BOTÃO LUTAR ======================
    @discord.ui.button(label="⚔️ Lutar", style=discord.ButtonStyle.danger, custom_id="fight_mon", row=0)
    async def fight_mon(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.uid:
            await interaction.response.send_message("❌ Não é a tua batalha!", ephemeral=True)
            return

        data = self._get_data()
        if not data.get("inBattle") or not data.get("wild"):
            await interaction.response.edit_message(content="❌ Sem batalha ativa. Usa `/caçar`.", embed=None, view=None)
            return

        wild = data["wild"]
        mon = get_active_mon(data)
        lines = []

        # Raridade -> bónus de dano das mãos (escalado)
        RARE_HAND_DMG = {"comum": (6, 10), "incomum": (9, 15), "raro": (13, 20),
                         "épico": (18, 28), "lendário": (25, 38), "mítico": (33, 50)}

        # Ataque do Jogador
        if not mon or not mon.get("alive", True):
            # Sem monstro: ataca com as mãos, dano escala com raridade do inimigo
            rare = wild.get("rare", "comum")
            lo, hi = RARE_HAND_DMG.get(rare, (6, 10))
            dmg = max(1, int(lo + random.random() * (hi - lo)))
            # Aplica bónus de rebirth
            db = 1 + data.get("rebirthCount", 0) * 0.5
            dmg = max(1, int(dmg * db))
            wild["hp"] = max(0, wild.get("hp", 0) - dmg)
            lines.append(f"👊 Atacaste com as mãos! **-{dmg}** HP")
            # Sem monstro, inimigo não contra-ataca (sem alvo)
        else:
            refresh_mon_stats(mon)
            at, effect = get_type_effect(mon.get("t", ""), wild.get("t", ""))
            db = 1 + data.get("rebirthCount", 0) * 0.5
            xb = 1.6 if data.get("xatkActive", False) else 1.0
            if data.get("xatkActive", False):
                data["xatkActive"] = False

            dmg = max(1, int(mon["atkStat"] * (0.75 + random.random() * 0.45) * db * at * xb))
            ret = max(1, int(wild.get("atk", 5) * random.uniform(0.5, 0.95)))

            wild["hp"] = max(0, wild.get("hp", 0) - dmg)
            mon["hp"] = max(0, mon["hp"] - ret)

            if effect == "advantage":
                lines.append(f"⚡ **Super eficaz!** Causaste **{dmg}** dano!")
            elif effect == "disadvantage":
                lines.append(f"💧 *Pouco eficaz...* Causaste **{dmg}** dano.")
            else:
                lines.append(f"⚔️ Causaste **{dmg}** dano!")

            lines.append(f"🗡️ Inimigo contra-atacou! **-{ret}** HP")
            gainXp(mon, 8 + int(wild.get("atk", 5) * 1.6), data)

        # Verifica Vitória — NÃO limpa o wild state: deixa o jogador capturar!
        if wild.get("hp", 0) <= 0:
            wild["hp"] = 0
            data["wild"] = wild  # Atualiza HP a 0 mas mantém o wild para capturar
            data["battleBonus"] = min(0.65, data.get("battleBonus", 0) + 0.15)
            lines.append(f"✅ **{wild['n']}** está KO! Usa 🔮 Ball para capturar, ou 🏃 Fugir.")
            self._cancel_tasks()

            # Atualiza botões: só Ball/Master/Fugir disponíveis
            for child in self.children:
                cid = getattr(child, "custom_id", "")
                if cid == "fight_mon":
                    child.disabled = True
                    child.label = "💀 KO"
                elif cid == "throw_ball":
                    child.disabled = data.get("balls", 0) <= 0
                    child.label = f"🔮 Ball ({data.get('balls', 0)})"
                elif cid == "throw_master":
                    child.disabled = data.get("masterball", 0) <= 0
                    child.label = f"⭐ Master ({data.get('masterball', 0)})"

            self._save(data)
            await interaction.response.edit_message(
                embed=make_wild_embed(wild, data, "\n".join(lines)),
                view=self
            )
            return

        # Verifica Derrota do Monstro
        if mon and mon.get("hp", 0) <= 0:
            mon["alive"] = False
            lines.append("💀 Teu monstro desmaiou! Ainda podes atacar com as mãos ou fugir.")
            self._save(data)
            self._update_buttons(data)
            await interaction.response.edit_message(
                embed=make_wild_embed(wild, data, "\n".join(lines)),
                view=self
            )
            self._cancel_tasks()
            return

        # Se a batalha continua
        self._save(data)
        self._update_buttons(data)

        if not self.message:
            try:
                self.message = await interaction.original_response()
            except:
                pass

        await interaction.response.edit_message(
            embed=make_wild_embed(wild, data, "\n".join(lines)),
            view=self
        )

        # Inicia a task de ataque do inimigo se ainda não estiver rodando
        if not self._enemy_task or self._enemy_task.done():
            self._enemy_task = asyncio.create_task(self._enemy_auto_attack())

    # ====================== OUTROS BOTÕES ======================

    @discord.ui.button(label="🔮 Ball (10)", style=discord.ButtonStyle.primary, custom_id="throw_ball", row=0)
    async def throw_ball(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.uid:
            await interaction.response.send_message("❌ Não é a tua batalha!", ephemeral=True)
            return

        data = self._get_data()
        if not data.get("inBattle") or not data.get("wild"):
            await interaction.response.edit_message(content="❌ Sem batalha ativa.", embed=None, view=None)
            return

        wild = data["wild"]
        if data.get("balls", 0) <= 0:
            await interaction.response.send_message("❌ Sem Balls!", ephemeral=True)
            return

        data["balls"] -= 1
        chance = get_catch_chance(wild, data)

        if random.random() < chance:
            captured = capture_wild(wild, data)
            if wild["n"] not in data.get("caught", []):
                data.setdefault("caught", []).append(wild["n"])
            clear_wild_state(data)
            data["balls"] = min(99, data.get("balls", 0) + 2)

            self._cancel_tasks()
            self._save(data)
            embed = discord.Embed(
                title=f"✅ {wild.get('e','')} {wild['n']} Capturado!",
                description=f"Sucesso! ({int(chance*100)}%)\n{type_badge(wild.get('t','?'))} · {rare_badge(wild.get('rare','comum'))}\n\n*Esta mensagem desaparece em 30 segundos.*",
                color=RARE_COLOR.get(wild.get("rare","comum"), 0x888888)
            )
            await interaction.response.edit_message(embed=embed, view=None)
            # Apaga a mensagem após 30 segundos
            async def _delete_after():
                await asyncio.sleep(30)
                try:
                    msg = self.message or await interaction.original_response()
                    await msg.delete()
                except:
                    pass
            asyncio.create_task(_delete_after())
        else:
            self._save(data)
            self._update_buttons(data)
            await interaction.response.edit_message(
                embed=make_wild_embed(wild, data, "💥 A bola falhou! Chance: " + str(int(chance*100)) + "%"),
                view=self
            )

    @discord.ui.button(label="⭐ Master", style=discord.ButtonStyle.success, custom_id="throw_master", row=0)
    async def throw_master(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.uid:
            await interaction.response.send_message("❌ Não é a tua batalha!", ephemeral=True)
            return

        data = self._get_data()
        if not data.get("inBattle") or not data.get("wild"):
            await interaction.response.edit_message(content="❌ Sem batalha.", embed=None, view=None)
            return

        wild = data["wild"]
        if data.get("masterball", 0) <= 0:
            await interaction.response.send_message("❌ Sem Master Ball!", ephemeral=True)
            return

        data["masterball"] -= 1
        captured = capture_wild(wild, data)
        if wild["n"] not in data.get("caught", []):
            data.setdefault("caught", []).append(wild["n"])
        clear_wild_state(data)

        self._cancel_tasks()
        self._save(data)
        embed = discord.Embed(
            title=f"⭐ {wild.get('e','')} {wild['n']} Capturado!", 
            description="Captura garantida!\n\n*Esta mensagem desaparece em 30 segundos.*", 
            color=0xffd700
        )
        await interaction.response.edit_message(embed=embed, view=None)
        # Apaga a mensagem após 30 segundos
        async def _delete_after_master():
            await asyncio.sleep(30)
            try:
                msg = self.message or await interaction.original_response()
                await msg.delete()
            except:
                pass
        asyncio.create_task(_delete_after_master())

    @discord.ui.button(label="🏃 Fugir", style=discord.ButtonStyle.secondary, custom_id="flee", row=1)
    async def flee(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.uid:
            await interaction.response.send_message("❌ Não é a tua batalha!", ephemeral=True)
            return

        self._cancel_tasks()
        data = self._get_data()
        wild = data.get("wild")
        wild_ko = wild and wild.get("hp", 1) <= 0

        clear_wild_state(data)
        self._save(data)

        if wild_ko and wild:
            # Jogador derrotou o monstro mas não capturou — mostra mensagem de derrota e apaga após 30s
            embed = discord.Embed(
                title=f"💀 {wild.get('e','')} {wild['n']} Derrotado!",
                description=f"Derrotaste o **{wild['n']}** mas não o capturaste.\n\n*Esta mensagem desaparece em 30 segundos.*",
                color=0x888888
            )
            await interaction.response.edit_message(embed=embed, content=None, view=None)
            async def _delete_after_defeat():
                await asyncio.sleep(30)
                try:
                    msg = self.message or await interaction.original_response()
                    await msg.delete()
                except:
                    pass
            asyncio.create_task(_delete_after_defeat())
        else:
            await interaction.response.edit_message(content="🏃 Fugiste da batalha!", embed=None, view=None)

    async def on_timeout(self):
        self._cancel_tasks()
        try:
            data = self._get_data()
            clear_wild_state(data)
            self._save(data)
        except:
            pass
        try:
            if self.message:
                await self.message.delete()
        except:
            pass
# ══════════════════════════════════════════════
# VIEW DA LOJA
# ══════════════════════════════════════════════

class ShopView(discord.ui.View):
    def __init__(self,uid,page=0):
        super().__init__(timeout=60); self.uid=uid; self.page=page; self._upd()
    def _upd(self):
        self.clear_items(); pp=5; s=self.page*pp; shown=SHOP_ITEMS[s:s+pp]
        for it in shown:
            b=discord.ui.Button(label=f"{it['e']} {it['n']} ({it['price']}💰)",style=discord.ButtonStyle.secondary)
            b.callback=self._buy(it); self.add_item(b)
        if self.page>0:
            p=discord.ui.Button(label="◀ Anterior",style=discord.ButtonStyle.primary,row=4); p.callback=self._prev; self.add_item(p)
        if (self.page+1)*pp<len(SHOP_ITEMS):
            n=discord.ui.Button(label="▶ Próxima",style=discord.ButtonStyle.primary,row=4); n.callback=self._next; self.add_item(n)
    def _buy(self,it):
        async def cb(interaction:discord.Interaction):
            if interaction.user.id!=self.uid: await interaction.response.send_message("❌",ephemeral=True); return
            data=load_clean_save(self.uid)
            if data.get("gold",0)<it["price"]: await interaction.response.send_message(f"❌ Precisas de 💰**{it['price']}**. Tens **{data.get('gold',0)}**.",ephemeral=True); return
            data["gold"]-=it["price"]; iid=it["id"]
            if iid=="masterball": data["masterball"]=data.get("masterball",0)+1
            elif iid=="balls5": data["balls"]=min(99,data.get("balls",0)+5)
            elif iid=="charm": data["matBonus"]=min(3,data.get("matBonus",0)+1)
            elif iid=="incense": data["rareSpawnPassive"]=min(3,data.get("rareSpawnPassive",0)+1)
            elif iid=="rarepotion": data.setdefault("items",{})[iid]=data["items"].get(iid,0)+1
            else: data.setdefault("items",{})[iid]=data["items"].get(iid,0)+1
            write_save(self.uid,data); await interaction.response.send_message(f"✅ {it['e']} **{it['n']}** comprado! 💰 **{data['gold']}** restante.",ephemeral=True)
        return cb
    async def _prev(self,i): self.page=max(0,self.page-1); self._upd(); await i.response.edit_message(embed=self._emb(),view=self)
    async def _next(self,i): self.page=min((len(SHOP_ITEMS)-1)//5,self.page+1); self._upd(); await i.response.edit_message(embed=self._emb(),view=self)
    def _emb(self):
        pp=5; s=self.page*pp; shown=SHOP_ITEMS[s:s+pp]; tot=(len(SHOP_ITEMS)-1)//5+1
        embed=discord.Embed(title="🏪 Loja Monster Hunter",description=f"Página {self.page+1}/{tot}",color=0xffd700)
        for i in shown: embed.add_field(name=f"{i['e']} {i['n']} · 💰 {i['price']}",value=i['desc'],inline=False)
        return embed
        
class BossView(discord.ui.View):
    def __init__(self, uid, timeout=600):
        super().__init__(timeout=timeout)
        self.uid = uid

    # Por agora, para evitar o erro "batalha de boss", vamos fazer uma versão mínima
    @discord.ui.button(label="🏃 Retirar", style=discord.ButtonStyle.danger)
    async def retreat(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.uid:
            await interaction.response.send_message("❌ Não é a tua batalha!", ephemeral=True)
            return
        data = load_clean_save(self.uid)
        clear_boss_state(data)
        write_save(self.uid, data)
        await interaction.response.edit_message(content="🏃 Recuaste da batalha de boss.", embed=None, view=None)
# ══════════════════════════════════════════════
# VIEW DA POKÉDEX
# ══════════════════════════════════════════════

class PokedexView(discord.ui.View):
    def __init__(self,uid):
        super().__init__(timeout=120); self.uid=uid

    @discord.ui.button(label="🌌 Desafiar Boss Final",style=discord.ButtonStyle.danger,emoji="❓")
    async def challenge_final(self,interaction:discord.Interaction,button:discord.ui.Button):
        if interaction.user.id!=self.uid: await interaction.response.send_message("❌ Não é a tua Pokédex!",ephemeral=True); return
        data=load_clean_save(self.uid)
        if data.get("inBattle") or data.get("inBossBattle"): await interaction.response.send_message("⚔️ Já estás em batalha!",ephemeral=True); return
        if not is_pokedex_complete(data): await interaction.response.send_message(f"❌ Pokédex incompleta: **{pokedex_progress(data)}/{pokedex_total()}**",ephemeral=True); return
        if "???" in data.get("bossDefeated",[]) or "Leonking" in data.get("bossDefeated",[]): await interaction.response.send_message("👑 Já derrotaste Leonking!",ephemeral=True); return
        mon=get_active_mon(data)
        if not mon or not mon.get("alive",True): await interaction.response.send_message("❌ Precisas de um monstro vivo!",ephemeral=True); return
        final=next((b for b in BOSSES if b.get("special")=="final_boss"),None)
        if not final: await interaction.response.send_message("❌ Erro interno!",ephemeral=True); return
        start_boss_battle(data,final,mon); write_save(self.uid,data)
        embed=discord.Embed(title="🌌 O DEUS ABSOLUTO DESPERTOU!",
            description="# ❓ ???\n*O ser que transcende a realidade...*\n\n⚠️ **Batalha em DUAS FASES!**\n1️⃣ Derrota a forma `???`\n2️⃣ Enfrenta **Leonking** — O Rei dos Deuses",color=0xff00ff)
        await interaction.response.send_message(embed=embed,view=BossView(self.uid))

# ══════════════════════════════════════════════
# SLASH COMMANDS
# ══════════════════════════════════════════════

@tree.command(name="caçar",description="Encontra um monstro selvagem (10% chance de boss!)")
async def hunt(interaction:discord.Interaction):
    uid=interaction.user.id; data=load_clean_save(uid)
    if data.get("inBattle") and not data.get("wild"): clear_wild_state(data); write_save(uid,data)
    if data.get("inBossBattle") and (not data.get("boss") or data.get("bossHp",0)<=0): clear_boss_state(data); write_save(uid,data)
    if data.get("inBattle"): await interaction.response.send_message("⚔️ Já estás em batalha! Termina primeiro.",ephemeral=True); return
    if data.get("inBossBattle"): await interaction.response.send_message("👹 Já estás em batalha de boss!",ephemeral=True); return
    mon=get_active_mon(data); has_mon=bool(mon and mon.get("alive",True))
    # Boss pendente
    pending=data.get("pendingBoss")
    if pending and has_mon:
        boss=BOSS_INDEX.get(pending)
        if boss:
            data["pendingBoss"]=None; start_boss_battle(data,boss,mon); write_save(uid,data)
            embed=discord.Embed(title=f"⚠️ BOSS APARECEU! {boss['e']} {boss['n']}",
                description=f"*{boss.get('title','?')}*\n\n{type_badge(boss.get('t','?'))}\n❤️ HP: **{data['bossHp']:,}** · ⚔️ ATK: **{boss['atk']:,}**\n💰 **{boss.get('reward',0):,}** ouro",color=0x8a0020)
            await interaction.response.send_message(embed=embed,view=BossView(uid)); return
    # 10% boss aleatório (com repelente check)
    repel=data.get("bossRepelUntil",0)>time.time()
    if has_mon and not repel and data.get("battles",0)>0 and random.random()<0.10:
        boss=roll_random_boss(data)
        if boss:
            start_boss_battle(data,boss,mon); write_save(uid,data)
            embed=discord.Embed(title=f"⚠️ BOSS APARECEU! {boss['e']} {boss['n']}",
                description=f"*{boss.get('title','?')}*\n\n{type_badge(boss.get('t','?'))}\n❤️ HP: **{data['bossHp']:,}** · ⚔️ ATK: **{boss['atk']:,}**\n💰 **{boss.get('reward',0):,}** ouro",color=0x8a0020)
            await interaction.response.send_message(embed=embed,view=BossView(uid)); return
    # Monstro selvagem
    wild=generate_wild_mon(forced_rarity=data.get("forcedRarity"),forced_type=data.get("forcedType"),data=data)
    data["forcedRarity"]=None; data["forcedType"]=None
    data["wild"]=wild; data["inBattle"]=True; data["battleBonus"]=0
    data["attackCooldownUntil"]=0; data["battles"]=data.get("battles",0)+1
    write_save(uid,data)
    view=BattleView(uid)
    await interaction.response.send_message(embed=make_wild_embed(wild,data,f"Um **{wild['n']}** selvagem apareceu!"),view=view)
    view.message=await interaction.original_response()
    # Inicia ataque automático do inimigo desde o início (a cada 10s)
    view._enemy_task=asyncio.create_task(view._enemy_auto_attack())

@tree.command(name="equipa",description="Vê a tua equipa")
async def team_cmd(interaction:discord.Interaction):
    uid=interaction.user.id; data=load_clean_save(uid); team=data.get("team",[])
    if not team:
        await interaction.response.send_message(embed=discord.Embed(title="🐾 Equipa",description="Sem monstros! Usa `/caçar` e lança uma Ball.",color=0xffd166),ephemeral=True); return
    embed=discord.Embed(title="🐾 A Tua Equipa",color=0xffd700)
    embed.add_field(name="💰 Ouro",value=f"**{data.get('gold',0)}**",inline=True)
    embed.add_field(name="🔮 Balls",value=f"**{data.get('balls',0)}**",inline=True)
    embed.add_field(name="📖 Pokédex",value=f"**{len(data.get('caught',[]))}/{len(MONS)}**",inline=True)
    aid=data.get("activeMonId")
    for i,mon in enumerate(team,1):
        refresh_mon_stats(mon); sp=mon.get("species",mon.get("n","?")); is_act=mon.get("id")==aid
        pct=mon["hp"]/max(1,mon["maxHp"]); bar=hp_bar(pct,8); alive="💚" if mon.get("alive",True) else "💀 KO"
        embed.add_field(name=f"{'⭐ ' if is_act else f'{i}. '}{mon.get('e','❓')} {sp}",
            value=f"{type_badge(mon.get('t','?'))} · Tier **{mon.get('tier',1)}**\nLv.**{mon.get('level',1)}** · ⚔️ **{mon.get('atkStat','?')}** · {alive}\n{bar} {mon['hp']}/{mon['maxHp']}",inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="box",description="Vê a tua box")
async def box_cmd(interaction:discord.Interaction):
    uid=interaction.user.id; data=load_clean_save(uid); box=data.get("box",[])
    if not box: await interaction.response.send_message(embed=discord.Embed(title="📦 Box",description="Box vazia.",color=0x5090e0),ephemeral=True); return
    embed=discord.Embed(title=f"📦 Box ({len(box)} monstros)",color=0x5090e0)
    for mon in box[:15]:
        refresh_mon_stats(mon); sp=mon.get("species",mon.get("n","?")); pct=mon["hp"]/max(1,mon["maxHp"])
        embed.add_field(name=f"{mon.get('e','❓')} {sp}",
            value=f"{type_badge(mon.get('t','?'))} · Lv.**{mon.get('level',1)}** · Tier **{mon.get('tier',1)}**\n{hp_bar(pct,8)} {mon['hp']}/{mon['maxHp']}",inline=False)
    if len(box)>15: embed.set_footer(text=f"15/{len(box)}")
    await interaction.response.send_message(embed=embed)

@tree.command(name="ativar",description="Define o monstro ativo")
@app_commands.describe(posicao="Posição na equipa (1-6)")
async def set_active(interaction:discord.Interaction,posicao:int):
    uid=interaction.user.id; data=load_clean_save(uid); team=data.get("team",[])
    if not 1<=posicao<=len(team): await interaction.response.send_message(f"❌ Equipa tem **{len(team)}** monstro(s).",ephemeral=True); return
    mon=team[posicao-1]; data["activeMonId"]=mon["id"]; write_save(uid,data); refresh_mon_stats(mon)
    await interaction.response.send_message(f"⭐ {mon.get('e','')} **{mon.get('species',mon.get('n','?'))}** ativo!\nLv.**{mon.get('level',1)}** {tier_stars(mon.get('tier',1))} · ❤️ {mon['hp']}/{mon['maxHp']} · ⚔️ {mon['atkStat']}")

@tree.command(name="curar",description="Cura o monstro ativo")
@app_commands.describe(tipo="poção/superpoção/megapoção/hyperpoção/revive/maxrevive")
async def heal(interaction:discord.Interaction,tipo:str="poção"):
    uid=interaction.user.id; data=load_clean_save(uid); mon=get_active_mon(data)
    if not mon: await interaction.response.send_message("❌ Sem monstro ativo!",ephemeral=True); return
    mp={"poção":"potion","superpoção":"superpotion","megapoção":"megapotion","hyperpoção":"hyperpotion","hyper":"hyperpotion","revive":"revive","maxrevive":"maxrevive"}
    iid=mp.get(tipo.lower().strip(),"potion"); items=data.get("items",{})
    if items.get(iid,0)<=0: await interaction.response.send_message(f"❌ Sem **{tipo}**! Compra em `/loja`.",ephemeral=True); return
    refresh_mon_stats(mon); msg=""
    if iid=="potion":
        if not mon.get("alive",True): await interaction.response.send_message("❌ KO! Usa Revive.",ephemeral=True); return
        if mon["hp"]>=mon["maxHp"]: await interaction.response.send_message("❌ HP já cheio!",ephemeral=True); return
        if mon.get("species","")=="OXIGÉNIO":
            data["nicoPotions"]=data.get("nicoPotions",0)+1; items[iid]-=1; data["items"]=items; write_save(uid,data)
            if data["nicoPotions"]>=3: data["nicoPotions"]=0; data["pendingBoss"]="Nico"; write_save(uid,data); await interaction.response.send_message("✨ **O OXIGÉNIO brilha!**\n🐈 **NICO APARECEU!** Usa `/caçar`!"); return
            await interaction.response.send_message(f"✨ O Oxigénio absorve energia... (**{data['nicoPotions']}/3**)"); return
        mon["hp"]=min(mon["maxHp"],mon["hp"]+60); msg=f"🧪 +60 HP → {mon['hp']}/{mon['maxHp']}"
    elif iid=="hyperpotion":
        if not mon.get("alive",True): await interaction.response.send_message("❌ KO!",ephemeral=True); return
        mon["hp"]=mon["maxHp"]; msg=f"✨ HP totalmente restaurado! {mon['hp']}/{mon['maxHp']}"
    elif iid=="superpotion":
        if not mon.get("alive",True): await interaction.response.send_message("❌ KO!",ephemeral=True); return
        mon["hp"]=min(mon["maxHp"],mon["hp"]+150); msg=f"💚 +150 HP → {mon['hp']}/{mon['maxHp']}"
    elif iid=="megapotion":
        if not mon.get("alive",True): await interaction.response.send_message("❌ KO!",ephemeral=True); return
        h=int(mon["maxHp"]*0.5); mon["hp"]=min(mon["maxHp"],mon["hp"]+h); msg=f"💊 +{h} HP → {mon['hp']}/{mon['maxHp']}"
    elif iid=="revive":
        if mon.get("alive",True): await interaction.response.send_message("❌ Não está KO!",ephemeral=True); return
        mon["hp"]=max(1,int(mon["maxHp"]*0.75)); mon["alive"]=True; msg=f"❤️ {mon.get('species',mon.get('n','?'))} voltou! {mon['hp']}/{mon['maxHp']}"
    elif iid=="maxrevive":
        if mon.get("alive",True): await interaction.response.send_message("❌ Não está KO!",ephemeral=True); return
        mon["hp"]=mon["maxHp"]; mon["alive"]=True; msg=f"💖 HP total restaurado! {mon['hp']}/{mon['maxHp']}"
    items[iid]-=1; data["items"]=items; write_save(uid,data); await interaction.response.send_message(msg)

@tree.command(name="inventario",description="Vê o teu inventário")
async def inventory(interaction:discord.Interaction):
    uid=interaction.user.id; data=load_clean_save(uid)
    embed=discord.Embed(title="🎒 Inventário",color=0x5090e0)
    embed.add_field(name="💰 Ouro",value=f"**{data.get('gold',0)}**",inline=True)
    embed.add_field(name="🔮 Balls",value=f"**{data.get('balls',0)}**",inline=True)
    embed.add_field(name="⭐ Master",value=f"**{data.get('masterball',0)}**",inline=True)
    mon=get_active_mon(data)
    if mon:
        refresh_mon_stats(mon); pct=mon["hp"]/max(1,mon["maxHp"])
        embed.add_field(name=f"⭐ Ativo: {mon.get('e','')} {mon.get('species',mon.get('n','?'))}",
            value=f"Lv.**{mon.get('level',1)}** · {hp_bar(pct,10)} · ⚔️ {mon.get('atkStat','?')}",inline=False)
    im={i["id"]:i for i in SHOP_ITEMS}; items=data.get("items",{})
    il=[f"{im.get(k,{'e':'📦','n':k})['e']} **{im.get(k,{'e':'📦','n':k})['n']}** × {v}" for k,v in items.items() if v>0]
    embed.add_field(name="🧪 Itens",value="\n".join(il[:18]) if il else "*Nenhum*",inline=False)
    mats=data.get("materials",{})
    ml=[f"🪨 **{k}** × {v}" for k,v in list(mats.items())[:15] if v>0]
    embed.add_field(name="🪨 Materiais",value="\n".join(ml) if ml else "*Nenhum*",inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="loja",description="Abre a loja de itens")
async def shop(interaction:discord.Interaction):
    uid=interaction.user.id; data=load_clean_save(uid); view=ShopView(uid)
    embed=view._emb(); embed.set_footer(text=f"💰 Tens {data.get('gold',0)} ouro")
    await interaction.response.send_message(embed=embed,view=view)

@tree.command(name="usar",description="Usa um item do inventário")
@app_commands.describe(item="Nome do item")
async def use_item(interaction:discord.Interaction,item:str):
    uid=interaction.user.id; data=load_clean_save(uid); mon=get_active_mon(data)
    if not mon: await interaction.response.send_message("❌ Sem monstro ativo!",ephemeral=True); return
    mp={
        "proteína":"protein","protein":"protein","heartseed":"heartseed","tiercore":"tiercore",
        "xatk":"xatk","x-ataque":"xatk","raredecoy":"raredecoy","epicdecoy":"epicdecoy",
        "goldenball":"goldenball","golden ball":"goldenball","rarepotion":"rarepotion",
        "incense":"incense","incenso raro":"incense","repelente":"repelent","repelent":"repelent",
        "dragoball":"dragoball","drago ball":"dragoball","neoncage":"neoncage","gaiola néon":"neoncage",
        "soulcatcher":"soulcatcher","apanhador de almas":"soulcatcher","typelure":"typelure",
        "isca de tipo":"typelure","ritual":"ritual","ritual boss":"ritual",
        "megaincense":"megaincense","mega incenso":"megaincense","typedetect":"typedetect","detector de tipos":"typedetect",
        "isco raro":"raredecoy","isco épico":"epicdecoy",
    }
    iid=mp.get(item.lower().strip())
    if not iid: await interaction.response.send_message(f"❌ Item desconhecido: **{item}**",ephemeral=True); return
    items=data.get("items",{})
    if items.get(iid,0)<=0: await interaction.response.send_message(f"❌ Não tens **{item}**!",ephemeral=True); return
    refresh_mon_stats(mon); msg=""
    if iid=="protein": mon["atkBoost"]=mon.get("atkBoost",0)+10; refresh_mon_stats(mon); msg=f"💪 +10 ATK! Total: **{mon['atkStat']}**"
    elif iid=="heartseed": mon["hpBoost"]=mon.get("hpBoost",0)+10; refresh_mon_stats(mon); msg=f"🌱 +10 HP! Total: **{mon['maxHp']}**"
    elif iid=="tiercore":
        if mon.get("tier",1)>=5: await interaction.response.send_message("❌ Tier já no máximo!",ephemeral=True); return
        mon["tier"]=mon.get("tier",1)+1; refresh_mon_stats(mon); mon["hp"]=mon["maxHp"]; msg=f"🔺 Tier **{mon['tier']}** {tier_stars(mon['tier'])}! HP: **{mon['maxHp']}** · ATK: **{mon['atkStat']}**"
    elif iid=="xatk": data["xatkActive"]=True; msg="💢 **X-Ataque** ativo! Próximo ataque +60%."
    elif iid=="raredecoy": data["forcedRarity"]="raro"; msg="🧲 Próximo monstro será **Raro** ou superior!"
    elif iid=="epicdecoy": data["forcedRarity"]="épico"; msg="💎 Próximo monstro será **Épico** ou superior!"
    elif iid=="rarepotion": data["rareCatchBonus"]=data.get("rareCatchBonus",0)+0.30; msg="💜 **Poção Rara** pronta! +30% captura em raros+."
    elif iid=="incense": data["rareSpawnPassive"]=min(3,data.get("rareSpawnPassive",0)+1); msg=f"🎁 **Incenso Raro** ativo! Bónus: **{data['rareSpawnPassive']}**"
    elif iid=="repelent": data["bossRepelUntil"]=time.time()+5*60; msg="🕊️ **Repelente** ativo por 5 minutos!"
    elif iid=="dragoball": msg="🔴 **Drago Ball** pronta! +40% em Dragões/Fantasmas/Arcanos."
    elif iid=="neoncage": msg="🟩 **Gaiola Néon** pronta! +35% em Néon/Mecânico/Nuclear."
    elif iid=="soulcatcher": msg="👻 **Apanhador de Almas** pronto! +50% em Fantasmas/Espíritos."
    elif iid=="typelure":
        t=random.choice([td["t"] for td in TYPE_DEFS]); data["forcedType"]=t; msg=f"🎣 **Isca de Tipo**! Próximo encontro: **{t}**."
    elif iid=="ritual":
        boss=roll_random_boss(data)
        if not boss: await interaction.response.send_message("❌ Nenhum boss disponível.",ephemeral=True); return
        data["pendingBoss"]=boss["n"]; msg=f"🕯️ **{boss['n']}** aparecerá no próximo `/caçar`!"
    elif iid=="goldenball": msg="🌟 **Golden Ball** pronta! Usada no próximo Ball."
    elif iid=="megaincense": data["megaIncenseUntil"]=time.time()+30; msg="🌺 **Mega Incenso** ativo 30s! +300% raros!"
    elif iid=="typedetect": data["typeDetectActive"]=True; msg="📡 **Detector de Tipos** ativo!"
    items[iid]-=1; data["items"]=items; write_save(uid,data); await interaction.response.send_message(msg)

@tree.command(name="pokedex",description="Vê a tua Pokédex")
async def pokedex(interaction:discord.Interaction):
    uid=interaction.user.id; data=load_clean_save(uid)
    caught=data.get("caught",[]); bosses=data.get("bossDefeated",[])
    total=pokedex_total(); prog=pokedex_progress(data); pct=int(prog/total*100) if total>0 else 0
    complete=prog>=total; fd="???" in bosses or "Leonking" in bosses
    bd=len([b for b in bosses if b not in ("???","Leonking")]); bt=len([b for b in BOSSES if b.get("special")!="final_boss"])
    desc=f"Progresso: **{prog}/{total}** ({pct}%)\nMonstros: **{len(caught)}/{len(MONS)}** · Bosses: **{bd}/{bt}**"
    if complete and not fd: desc+="\n\n🌟 **POKÉDEX COMPLETA!** Usa o botão abaixo para o Boss Final!"
    if fd: desc+="\n👑 **Leonking já foi derrotado!**"
    embed=discord.Embed(title="📖 Pokédex",description=desc,color=0xffd700)
    if caught:
        dis=[f"{MON_INDEX.get(n,{}).get('e','❓')} {n[:10]}" for n in caught[:20]]
        rows=[" · ".join(dis[i:i+4]) for i in range(0,len(dis),4)]
        embed.add_field(name="🧩 Capturados",value="\n".join(rows[:5]),inline=False)
    if bosses: embed.add_field(name="👹 Bosses Derrotados",value=", ".join(bosses[:10])+("..." if len(bosses)>10 else ""),inline=False)
    embed.set_footer(text=f"Total: {len(MONS)} monstros + {len(BOSSES)} bosses")
    view=PokedexView(uid) if (complete and not fd) else None
    await interaction.response.send_message(embed=embed,view=view)

@tree.command(name="trocar",description="Troca monstros entre equipa e box")
@app_commands.describe(acao="'box' ou 'equipa'",nome="Nome do monstro")
async def swap(interaction:discord.Interaction,acao:str,nome:str):
    uid=interaction.user.id; data=load_clean_save(uid)
    if acao.lower()=="box":
        team=data.get("team",[]); 
        if len(team)<=1: await interaction.response.send_message("❌ Mínimo 1 na equipa!",ephemeral=True); return
        mon=next((m for m in team if nome.lower() in m.get("species",m.get("n","")).lower()),None)
        if not mon: await interaction.response.send_message(f"❌ **{nome}** não encontrado na equipa!",ephemeral=True); return
        data["team"].remove(mon); data.setdefault("box",[]).append(mon)
        if data.get("activeMonId")==mon.get("id"): data["activeMonId"]=data["team"][0]["id"] if data["team"] else None
        write_save(uid,data); await interaction.response.send_message(f"📦 {mon.get('e','')} **{mon.get('species',mon.get('n','?'))}** guardado na Box!")
    elif acao.lower() in ("equipa","team"):
        if len(data.get("team",[]))>=6: await interaction.response.send_message("❌ Equipa cheia (máx 6)!",ephemeral=True); return
        box=data.get("box",[]); mon=next((m for m in box if nome.lower() in m.get("species",m.get("n","")).lower()),None)
        if not mon: await interaction.response.send_message(f"❌ **{nome}** não encontrado na Box!",ephemeral=True); return
        data["box"].remove(mon); data.setdefault("team",[]).append(mon)
        if not data.get("activeMonId"): data["activeMonId"]=mon["id"]
        write_save(uid,data); await interaction.response.send_message(f"🐾 {mon.get('e','')} **{mon.get('species',mon.get('n','?'))}** na Equipa!")
    else: await interaction.response.send_message("❌ Usa `box` ou `equipa`.",ephemeral=True)

@tree.command(name="ranked",description="Vê o teu perfil ranked")
async def ranked_cmd(interaction:discord.Interaction):
    import base64; uid=interaction.user.id; data=load_clean_save(uid)
    elo=data.get("rankedElo",1200); rank=get_rank_info(elo)
    w=data.get("rankedWins",0); l=data.get("rankedLosses",0); name=data.get("playerName",f"Jogador_{uid}")
    t=w+l; wr=int(w/t*100) if t>0 else 0
    embed=discord.Embed(title=f"🏆 Ranked — {rank['icon']} {name}",description=f"Liga: **{rank['label']}**",color=rank["color"])
    embed.add_field(name="📊 ELO",value=f"**{elo}**",inline=True)
    embed.add_field(name="🏆 V/D",value=f"**{w}W/{l}L** ({wr}%)",inline=True)
    embed.add_field(name="💰 Ouro",value=f"**{data.get('gold',0)}**",inline=True)
    friends=data.get("friendScores",{})
    if friends:
        all_p=[{"name":name,"elo":elo}]+list(friends.values()); all_p.sort(key=lambda x:x["elo"],reverse=True)
        lb=[f"**#{i+1}** {get_rank_info(p['elo'])['icon']} {p['name']} — **{p['elo']}** ELO{' ← **Tu**' if p.get('name')==name and p.get('elo')==elo else ''}" for i,p in enumerate(all_p[:10])]
        embed.add_field(name="🏆 Leaderboard",value="\n".join(lb),inline=False)
    sd={"id":str(uid),"name":name,"elo":elo,"wins":w,"losses":l,"ts":int(time.time())}
    code="MHRPG:"+base64.b64encode(json.dumps(sd).encode()).decode()
    embed.add_field(name="📋 O teu Código",value=f"`{code[:60]}...`\nPartilha com amigos!",inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="ranked-import",description="Importa a pontuação de um amigo")
@app_commands.describe(codigo="Código MHRPG:")
async def ranked_import(interaction:discord.Interaction,codigo:str):
    import base64; uid=interaction.user.id; data=load_clean_save(uid)
    try:
        if not codigo.startswith("MHRPG:"): raise ValueError()
        fd=json.loads(base64.b64decode(codigo[6:]).decode())
        if not all(k in fd for k in ["id","name","elo"]): raise ValueError()
    except: await interaction.response.send_message("❌ Código inválido.",ephemeral=True); return
    if str(fd["id"])==str(uid): await interaction.response.send_message("😄 Esse código és tu!",ephemeral=True); return
    data.setdefault("friendScores",{})[fd["id"]]=fd; write_save(uid,data)
    rank=get_rank_info(fd["elo"]); await interaction.response.send_message(f"✅ **{fd['name']}** adicionado! {rank['icon']} ELO **{fd['elo']}**")

@tree.command(name="nomear",description="Define o teu nome")
@app_commands.describe(nome="Nome (2-24 caracteres)")
async def set_name(interaction:discord.Interaction,nome:str):
    if not 2<=len(nome)<=24: await interaction.response.send_message("❌ Nome: 2-24 caracteres.",ephemeral=True); return
    uid=interaction.user.id; data=load_clean_save(uid); data["playerName"]=nome; write_save(uid,data)
    await interaction.response.send_message(f"✅ Nome definido: **{nome}**!")

@tree.command(name="rebirth",description="Faz Rebirth (custa 10.000 💰)")
async def rebirth(interaction:discord.Interaction):
    uid=interaction.user.id; data=load_clean_save(uid)
    if data.get("gold",0)<10000: await interaction.response.send_message(f"❌ Precisas de 💰**10.000**. Tens **{data.get('gold',0)}**.",ephemeral=True); return
    data["gold"]-=10000; data["rebirthCount"]=data.get("rebirthCount",0)+1; rb=data["rebirthCount"]
    data["balls"]=10+rb*2; data["items"]={}; data["materials"]={}; data["level"]=1
    write_save(uid,data)
    await interaction.response.send_message(embed=discord.Embed(title=f"🌀 Rebirth #{rb}!",
        description=f"**Renasceste mais forte!**\n\n✨ Bónus **+{int(rb*50)}%** em HP/ATK e dano do Monster Lutar\n🔮 Balls: **{data['balls']}**\n💪 Monstros mantidos!",color=0x8e44ad))

@tree.command(name="perfil",description="Vê o teu perfil")
async def profile(interaction:discord.Interaction):
    uid=interaction.user.id; data=load_clean_save(uid)
    caught=data.get("caught",[]); bosses=data.get("bossDefeated",[])
    team=data.get("team",[]); elo=data.get("rankedElo",1200); rank=get_rank_info(elo); rb=data.get("rebirthCount",0)
    embed=discord.Embed(title=data.get("playerName",interaction.user.display_name),description=f"{rank['icon']} Perfil de Caçador",color=0xffd700)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.add_field(name="💰 Ouro",value=f"**{data.get('gold',0)}**",inline=True)
    embed.add_field(name="🔮 Balls",value=f"**{data.get('balls',0)}**",inline=True)
    embed.add_field(name="🌀 Rebirths",value=f"**{rb}**",inline=True)
    embed.add_field(name="📖 Pokédex",value=f"**{len(caught)}/{len(MONS)}**",inline=True)
    embed.add_field(name="👹 Bosses",value=f"**{len(bosses)}/{len(BOSSES)}**",inline=True)
    embed.add_field(name=f"{rank['icon']} Rank",value=f"**{rank['label']}** ({elo} ELO)",inline=True)
    mon=get_active_mon(data)
    if mon:
        refresh_mon_stats(mon); pct=mon["hp"]/max(1,mon["maxHp"])
        embed.add_field(name=f"⭐ {mon.get('e','')} {mon.get('species',mon.get('n','?'))}",
            value=f"Lv.**{mon.get('level',1)}** {tier_stars(mon.get('tier',1))} · {hp_bar(pct,10)}\n❤️ {mon['hp']}/{mon['maxHp']} · ⚔️ {mon.get('atkStat','?')}",inline=False)
    await interaction.response.send_message(embed=embed)

# ══════════════════════════════════════════════
# VIEW VENDER MATERIAIS
# ══════════════════════════════════════════════

class SellMatsView(discord.ui.View):
    """View interativa para vender materiais um a um ou todos de uma vez."""
    def __init__(self, uid, mats_snapshot):
        super().__init__(timeout=90)
        self.uid = uid
        self.mats = mats_snapshot  # lista de (nome, qty, valor_unit)

    def _make_embed(self, data):
        mats = data.get("materials", {})
        embed = discord.Embed(title="💰 Vender Materiais", color=0xf1c40f,
            description="Clica num material para vender **1 unidade**, ou usa **Vender Tudo** para liquidar tudo de uma vez.")
        embed.add_field(name="💰 Ouro atual", value=f"**{data.get('gold',0)}**", inline=True)
        total_val = sum(v * self._get_mat_value(k) for k,v in mats.items() if v > 0)
        embed.add_field(name="📦 Valor total", value=f"**{total_val}** 💰", inline=True)
        if mats:
            lines = []
            for name, qty in list(mats.items())[:15]:
                if qty > 0:
                    val = self._get_mat_value(name)
                    lines.append(f"🪨 **{name}** × {qty} — {val}💰/un. *(total: {qty*val}💰)*")
            embed.add_field(name="🎒 Materiais", value="\n".join(lines) if lines else "*Nenhum*", inline=False)
        else:
            embed.add_field(name="🎒 Materiais", value="*Sem materiais para vender.*", inline=False)
        return embed

    def _get_mat_value(self, name):
        """Obtém o valor de venda de um material (70% do valor base)."""
        # Procura nas mats dos monstros selvagens
        for mon in MONS:
            for mat in mon.get("mats", []):
                if mat["n"] == name:
                    return max(1, int(mat["v"] * 0.7))
        # Procura nas mats dos bosses
        for boss in BOSSES:
            for mat in boss.get("mats", []):
                if mat["n"] == name:
                    return max(1, int(mat["v"] * 0.7))
        return 5  # valor mínimo de fallback

    @discord.ui.button(label="🪨 Vender 1 Material", style=discord.ButtonStyle.primary, row=0)
    async def sell_one(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.uid:
            await interaction.response.send_message("❌ Não é o teu inventário!", ephemeral=True); return
        data = load_clean_save(self.uid)
        mats = data.get("materials", {})
        # Escolhe o primeiro material disponível com qty > 0
        mat_name = next((k for k,v in mats.items() if v > 0), None)
        if not mat_name:
            await interaction.response.edit_message(
                embed=discord.Embed(title="💰 Vender Materiais", description="❌ Sem materiais para vender!", color=0xe74c3c),
                view=None); return
        val = self._get_mat_value(mat_name)
        mats[mat_name] -= 1
        if mats[mat_name] <= 0: del mats[mat_name]
        data["materials"] = mats
        data["gold"] = data.get("gold", 0) + val
        write_save(self.uid, data)
        await interaction.response.edit_message(
            content=f"✅ Vendeste **1x {mat_name}** por **{val}💰**!",
            embed=self._make_embed(data), view=self)

    @discord.ui.button(label="💰 Vender Tudo", style=discord.ButtonStyle.danger, row=0)
    async def sell_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.uid:
            await interaction.response.send_message("❌ Não é o teu inventário!", ephemeral=True); return
        data = load_clean_save(self.uid)
        mats = data.get("materials", {})
        if not mats:
            await interaction.response.send_message("❌ Sem materiais!", ephemeral=True); return
        total = sum(v * self._get_mat_value(k) for k,v in mats.items() if v > 0)
        data["materials"] = {}
        data["gold"] = data.get("gold", 0) + total
        write_save(self.uid, data)
        embed = discord.Embed(
            title="💰 Vendido!",
            description=f"Vendeste **todos os materiais** por **{total}💰**!\n\n💰 Ouro total: **{data['gold']}**",
            color=0xf1c40f)
        await interaction.response.edit_message(content=None, embed=embed, view=None)

    @discord.ui.button(label="❌ Fechar", style=discord.ButtonStyle.secondary, row=0)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.uid:
            await interaction.response.send_message("❌", ephemeral=True); return
        await interaction.response.edit_message(content="*Loja de materiais fechada.*", embed=None, view=None)

@tree.command(name="vender",description="Vende os teus materiais por ouro")
async def sell_mats(interaction: discord.Interaction):
    uid = interaction.user.id
    data = load_clean_save(uid)
    mats = data.get("materials", {})
    view = SellMatsView(uid, list(mats.items()))
    embed = view._make_embed(data)
    await interaction.response.send_message(embed=embed, view=view)

# ══════════════════════════════════════════════
# COMANDO /imagem — GERA IMAGEM DO MONSTER
# ══════════════════════════════════════════════

# Mapeamento emoji → descrição visual para o Claude usar no prompt
EMOJI_VISUAL = {
    "🔥":"feito de chamas vivas, corpo incandescente cor de brasa",
    "🦊":"raposa ágil com pelagem cor de fogo",
    "🐅":"tigre flamejante com listras de lava",
    "🐲":"dragão com escamas flamejantes",
    "💧":"corpo translúcido de água, gotículas flutuantes",
    "🐟":"peixe gigante com escamas brilhantes azuis",
    "🌊":"criatura feita de ondas do oceano",
    "🌿":"criatura vegetal com folhas e vinhas pelo corpo",
    "🍀":"corpo coberto de trevo e musgo",
    "🌱":"pequena planta animada com raízes como pernas",
    "🪨":"corpo rochoso e maciço, pele de pedra",
    "🐗":"javali colossal de pedra e terra",
    "⛰️":"criatura montanhosa, enorme e rochosa",
    "🪶":"ave etérea com penas que flutuam no vento",
    "☁️":"ser feito de nuvens e vento com forma vaga",
    "🌬️":"criatura de ar invisível com redemoinhos visíveis",
    "❄️":"ser cristalino de gelo com arestas afiadas",
    "⛄":"golem de neve com olhos brilhantes",
    "🧊":"cubo de gelo vivo com núcleo azul pulsante",
    "⚡":"criatura elétrica faíscas constantes no corpo",
    "🔋":"robô-animal com células de energia no peito",
    "🌑":"ser de trevas absolutas, forma indefinida e sombria",
    "🦇":"morcego sombrio gigante com asas negras",
    "💎":"criatura de cristal facetado translúcido",
    "☠️":"ser venenoso esverdeado com gases tóxicos ao redor",
    "🐍":"serpente venenosa com escamas roxas e presas longas",
    "🎵":"ser musical feito de notas e ondas sonoras",
    "⌛":"criatura do tempo com corpo de ampulheta e engrenagens",
    "☀️":"ser luminoso com corpo solar e raios de luz",
    "🌌":"entidade cósmica com galáxias no corpo",
    "🪐":"ser com anéis planetários ao redor do corpo",
    "⚙️":"golem metálico coberto de engrenagens e aço",
    "⛓️":"criatura de correntes e metal fundido",
    "👻":"fantasma translúcido com forma etérea e brilhante",
    "🫥":"ser quase invisível com contorno brilhante",
    "🐉":"dragão majestoso com asas enormes e fogo nas fauces",
    "🦕":"dinossauro dracônico com escamas e chifres",
    "🧚":"fada luminosa com asas delicadas e pó mágico",
    "🌸":"ser de pétalas cor-de-rosa e magia floral",
    "🔮":"ser psíquico com olho no centro e aura violeta",
    "🧠":"criatura com cérebro exposto e ondas mentais visíveis",
    "👊":"lutador musculoso com punhos de aço e aura de combate",
    "🥊":"boxeador-monstro com corpo definido e luvas mágicas",
    "🐛":"larva gigante com mandíbulas e corpo segmentado",
    "🦋":"borboleta-monstro com asas de padrão hipnótico",
    "🟢":"criatura néon verde com circuitos brilhantes na pele",
    "💻":"ser digital pixelado com dados flutuando",
    "☢️":"mutante radioativo brilhante e deformado",
    "🙏":"ser espiritual com aura dourada e forma humanoide serena",
    "🤖":"robô-monstro imponente com armor pesado",
    "🌪️":"tornado vivo com olho da tempestade brilhante",
    "🌋":"criatura de magma e rocha derretida",
    "🪄":"ser mágico arcano com runas flutuando ao redor",
    "👹":"demônio com chifres, dentes afiados e corpo vermelho",
    "🐋":"baleia colossal com tentáculos de água",
    "🎻":"ser musical sombrio com instrumentos no corpo",
    "🕰️":"golem de relógio com tempo congelado ao redor",
    "👼":"anjo guerreiro com asas douradas e armadura celestial",
    "🕳️":"singularidade viva, buraco negro com forma de criatura",
    "🐝":"abelha-rainha gigante com ferrão de energia",
    "👑":"rei-monstro com coroa de cristal e manto sombrio",
    "🐈":"gato misterioso com olhos cósmicos e sorriso eterno",
    "👨‍🦽":"figura humanoide perturbadora em cadeira de rodas sombria",
    "❓":"entidade desconhecida sem forma definida, iridescente",
    "🐐":"cabra divina colossal com chifres dourados e aura de deus",
}

async def _gerar_descricao_visual_claude(mon_name, mon_type, mon_rare, mon_emoji, is_boss, title_lore, atk, hp):
    """Chama a API do Claude para gerar uma descrição visual detalhada e fiel ao monster."""
    import aiohttp

    emoji_hint = EMOJI_VISUAL.get(mon_emoji, "")

    rarity_power = {
        "comum": "pequeno e inofensivo, aparência simples",
        "incomum": "de tamanho médio, aspecto interessante e colorido",
        "raro": "grande e ameaçador, detalhes marcantes",
        "épico": "imponente e majestoso, corpo impressionante",
        "lendário": "enorme e lendário, emana poder visível",
        "mítico": "transcendente, corpo brilhante e sobrenatural",
        "divino": "divino, radiante de luz e energia celestial",
        "boss": "colossal e aterrorizante, presença avassaladora",
    }.get(mon_rare, "misterioso")

    system_prompt = (
        "You are a creature concept artist for a Portuguese monster-catching RPG game. "
        "Your job is to write ultra-precise English image generation prompts for AI art tools. "
        "The prompt must make the creature look EXACTLY like its name, type, emoji and lore suggest. "
        "Be very specific about: body shape, colors, textures, elemental effects, size, pose. "
        "Output ONLY the image prompt, nothing else. No explanations. Max 120 words."
    )

    user_msg = (
        f"Create an image generation prompt for this monster:\n"
        f"- Name: {mon_name} (Portuguese name, use its meaning as visual inspiration)\n"
        f"- Element/Type: {mon_type}\n"
        f"- Emoji representation: {mon_emoji} — visual hint: {emoji_hint}\n"
        f"- Rarity/Power: {mon_rare} — {rarity_power}\n"
        f"- ATK: {atk} / HP: {hp}\n"
        + (f"- Boss title: '{title_lore}' — make it look like a terrifying final boss\n" if is_boss else "")
        + f"\nThe prompt must describe: creature body, colors tied to '{mon_type}' element, "
        f"size matching rarity, dynamic pose, elemental aura/effects, RPG fantasy art style. "
        f"Background should reflect the '{mon_type}' environment. No text in image."
    )

    # OpenRouter — compatível com OpenAI API, suporta vários modelos gratuitos
    payload = {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "max_tokens": 300,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ]
    }

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/leonking3543-cmyk/Monster-hunter",
        "X-Title": "Monster Hunter RPG Bot",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise Exception(f"OpenRouter HTTP {resp.status}: {body[:200]}")
            data = await resp.json()
            return data["choices"][0]["message"]["content"].strip()

# ══════════════════════════════════════════════
# GERAÇÃO DE IMAGEM (Melhorada e Gratuita)
# ══════════════════════════════════════════════

async def gerar_prompt_imagem(mon):
    """Prompt único e específico para cada monstro — remete ao nome, tipo e emoji."""

    nome = mon.get("n", "Monstro")
    tipo = mon.get("t", "").lower()
    emoji = mon.get("e", "❓")
    rare = mon.get("rare", "comum").lower()
    is_boss = mon.get("hp", 0) > 800 or bool(mon.get("title")) or rare in ["boss", "mítico", "lendário", "divino", "Divino"]

    # Palavras-chave visuais específicas por nome (quando existir, tem prioridade total)
    name_overrides = {
        # FOGO
        "Flaminho":     "tiny baby fire fox with flickering orange tail, cute beginner flame spirit, warm glow",
        "Labaréu":      "scorched wolf leaving burning pawprints, amber fur with fire veins, charred ground trail",
        "Brasalto":     "rock tiger with lava-filled cracks in fur, spitting embers at opponents",
        "Fornalix":     "walking forge furnace creature, stone belly glowing molten orange, chimney exhaust on back",
        "Tochino":      "lantern pig with nose that glows like a torch, warm amber light, small and round",
        "Faíscor":      "electric-fire hybrid lizard scraping claws on rock, creating long spark shower",
        "Fogaréu":      "bonfire-shaped beast, logs and ash forming body, crackling pop sounds visualized",
        "Pirólito":     "lava-stone golem hurling incandescent boulders, volcanic rock armor glowing red",
        "Chamego":      "friendly fire cat that wants to hug you, flame mane, soft orange glow",
        "Cinzal":       "ash phoenix rising from embers, grey and orange feathers, fertile ash trail",
        "Braseon":      "fire lion with mane made of living white-hot flames, royal ember crown",
        "Magmário":     "translucent body with visible magma veins, pressure building cracks on skin",
        "Ardencor":     "heat-distortion aura knight, armor radiates 1000-degree thermal waves",
        "Vulkar":       "volcanic dragon head erupting lava from maw, mountain spine back ridges",
        "Solferno":     "ancient fire deity wrapped in solar corona, molten gold form, crater guardian",
        # ÁGUA
        "Marulhinho":   "tiny blue puddle sprite with round eyes, happy splashing in a small pool",
        "Bolhudo":      "chubby water creature with giant bubble backpack, bubble trails when walking",
        "Aqualume":     "bioluminescent deep-sea fish with glowing blue lantern, flowing translucent fins",
        "Mariscoz":     "crab shell that filters and purifies water, crystal clear water jets from claws",
        "Pingorim":     "raindrop that gained awareness, teardrop body with tiny limbs, blue shimmer",
        "Riachito":     "stream-wolf that flows around obstacles, liquid silver fur, rushing current body",
        "Mareco":       "duck-platypus swimming upside down in whirlpool, mischievous grin",
        "Ondal":        "wave elemental with surfboard fins, blue-green crest, mood-reactive wave height",
        "Nautelo":      "nautilus spirit with spiral shell storing ocean secrets, glowing amber chambers",
        "Aqualux":      "deep sea jellyfish with bioluminescent tentacles guiding sailors, cerulean glow",
        "Tsuniko":      "small creature with disproportionately massive tail wave, calm eyes, huge power",
        "Abissor":      "abyssal anglerfish golem, no visible eyes, bioluminescent lure, crushing dark pressure",
        "Maréon":       "tide-controlling deity, moon-shaped crown, ocean swirls in eye sockets",
        "Leviagota":    "sea serpent made of condensed ocean water, continents visible as shadows beneath",
        "Tidalux":      "tsunami god in humanoid form, every step floods the ground, trident of deep currents",
        # PLANTA
        "Brotinho":     "tiny green sprout with big curious eyes, single leaf hat, fresh morning dew",
        "Ramalho":      "branch-body creature whose limbs predict weather by bending, bark skin",
        "Trepiko":      "vine gecko climbing walls, sucker pads on feet, leaves growing from spine",
        "Verdelim":     "medicine-flower deer with petals along spine, healing nectar dripping from antlers",
        "Mossito":      "moss-covered rock that gained legs, soft velvet texture, tiny flowers blooming on back",
        "Clorofim":     "solar-powered plant golem with leaf-wings angled at sun, pure green energy beam",
        "Galhudo":      "carnivorous plant bear, jaw-trap paws, pitcher plant stomach, fly-catching tongue",
        "Vinhedo":      "grape vine serpent feeling environment with tendrils, purple-green clusters as armor",
        "Botanix":      "plant librarian being, scrolls made of dried leaves, flower reading glasses",
        "Silvério":     "forest guardian with tree-trunk torso, canopy crown, owl perched on shoulder",
        "Selvar":       "jungle roar titan, seeds exploding from body on impact, rainforest aura",
        "Espinhaflor":  "beautiful rose armor knight, gorgeous blooms alongside razor thorns, contradictory beauty",
        "Clorossauro":  "plant dinosaur covered in chlorophyll scales, photosynthesis steam rising from back",
        "Floracel":     "pollinator queen bee made of flower petals, commanding bee swarm crown",
        "Matrizal":     "ancient root network entity, veins visible as glowing root map, world-tree scale",
        # TERRA
        "Cascalho":     "gravel ball with tiny pebble limbs, rattles loudly when rolling downhill",
        "Barrolho":     "mud creature slowly sinking and re-emerging elsewhere, footprints of wet clay",
        "Territo":      "seismograph lizard, seismic sensor whiskers, footsteps create visible shockwaves",
        "Tremorim":     "trembling ground-dweller, every step causes micro-quake ripples in soil",
        "Areíto":       "desert sandstorm fox that dissolves into dust cloud, re-forming body mid-run",
        "Pedrino":      "rock-camouflage armadillo, indistinguishable from boulder until it blinks",
        "Lamosso":      "swamp toad in hardening mud armor, ooze dripping from body, sticky trap aura",
        "Sedento":      "parched clay golem absorbing groundwater, cracked skin regrowing after drink",
        "Gravito":      "gravity anomaly creature floating rocks orbit it, local gravity distortion visible",
        "Monterro":     "plateau-back beast, its dorsal surface is a flat mountain with tiny trees",
        "Basalto":      "basalt column formation that walks, hexagonal pillar joints, volcanic black",
        "Colossalmo":   "mountain that learned locomotion, snow peaks on shoulders, valley between legs",
        "Terragor":     "magnitude-7 stomper with cracked earth trail, tectonic energy veins in skin",
        "Pedrax":       "granite-armored rhino, no blade has ever left a scratch, ancient mineral patterns",
        "Titanterra":   "geological titan with continental shelf spine, carries the weight of the world literally",
        # AR
        "Assobinho":    "wind-whistle bird that calms storms, gentle breeze aura, feathers dancing",
        "Névolo":       "cloud-bunny feeding on moisture, cumulus fluff body, silver lining fur",
        "Brisito":      "refreshing wind sprite creating cool breeze on hot days, transparent form with ripples",
        "Volitro":      "sonic-speed harrier leaving afterimage trail, compressed air cone at tip",
        "Nublim":       "mischievous cloud hidden in fog, giggling face inside mist bank",
        "Aeral":        "air current sculptor, reshaping wind flows with wing-angle precision",
        "Celsito":      "stratospheric ice-crystal bird, altitude vapor trails, blue-white crystalline feathers",
        "Ventor":       "spinning top creature generating personal tornado, debris orbit rings",
        "Ciclar":       "contained cyclone entity, calm eye at center, organized chaos spiraling around",
        "Nebulon":      "fog-giant dispersing then condensing, 500m body that thinks slowly but powerfully",
        "Furavento":    "drill-nose mole punching through air barriers, sonic boom shockwave visible",
        "Aerólux":      "bioluminescent sky manta ray leaving glowing contrail across night sky",
        "Tempespin":    "storm-summoner crane, one wing flap creates regional tempest system",
        "Estratelo":    "thermosphere swimmer, space-edge feathers glowing with atmospheric entry heat",
        "Skythar":      "sky sovereign, wings spanning horizon to horizon, cloud throne, wind obeys",
        # GELO
        "Gelito":       "frost puppy leaving icy pawprints, breath visible, happy in snowdrift",
        "Nevisco":      "snowflake artist, each snowflake it drops has a different unique geometry",
        "Frigelo":      "ice-breath salamander, freezes rain mid-fall, hail from exhaled air",
        "Branquim":     "arctic white fox perfectly camouflaged in blizzard, only eyes visible",
        "Geadinho":     "morning frost sprite kissing plants with protective icy film",
        "Cristagel":    "living ice crystal formation, shatters and reforms, prismatic inner glow",
        "Polarim":      "polar bear navigator on iceberg raft, aurora borealis crown, ice compass paws",
        "Nevon":        "snowstorm wolf with blizzard coat, howl creates local whiteout condition",
        "Brisagel":     "cold-wind specter, freezing breath cone, crystallizing the air it passes through",
        "Granizo":      "hailstone artillery creature, precision-targeted hail projectiles",
        "Gelágio":      "iceberg-scale sea creature controlling polar currents, ancient and slow",
        "Glacialto":    "absolute zero entity, frost radiates 20 meters instantly, winter in its wake",
        "Cryonix":      "time-freeze raven, brief local temporal crystallization around it",
        "Nevastro":     "eternal mountain guardian frozen in ice, blizzard halo, peak eternal",
        "Zeroar":       "zero-kelvin void entity, quantum frost field, absolute cold emanation",
        # TROVÃO
        "Raiolho":      "electric hamster climbing power poles, cheeks sparking like capacitors",
        "Choquito":     "clumsy electric puppy accidentally shocking friends with excitement, apologetic face",
        "Faíscudo":     "spark-trail gecko, continuous spark shower from dragging tail, neon glow path",
        "Pulsarim":     "heart-pulse energy creature, electricity beating in rhythm, EKG pattern on skin",
        "Estaleco":     "thunder-step centipede, each leg impact creates audible electric pop",
        "Voltino":      "high-voltage eel coiled into ball, city-powering discharge when fully charged",
        "Troval":       "storm-born wolf appearing only mid-lightning, fur is frozen lightning bolt",
        "Neonchoque":   "neon glow pre-discharge creature, full body illumination before attack",
        "Descargor":    "walking powerplant releasing city-scale electric burst, grid operator of nature",
        "Eletrux":      "electric current entity flowing through power lines at light speed",
        "Tempestral":   "storm conductor raising baton to summon lightning orchestra, maestro of thunder",
        "Raiotron":     "guided-lightning sniper, precision-targeted bolt from storm eye, scope eyeball",
        "Fulminax":     "fulgurite-forming titan, each strike vitrifies sand into glass columns",
        "Arcozapp":     "arc-jump predator leaping between cloud nodes, living arc flash",
        "Stormvolt":    "perfect storm entity, ultimate fusion of thunder lightning and wind, apex predator sky",
        # SOMBRA
        "Breuzinho":    "shadow kitten hiding in tiny dark corners, disappears when light touches it",
        "Sombralho":    "creature whose shadow moves independently with different intentions",
        "Ocultim":      "darkness field walker, extinguishes every light source in radius as it approaches",
        "Vultito":      "nightmare whisperer appearing at dream threshold, feeding on sleeping fears",
        "Umbralim":     "shadow-portal traveler, stepping through one shadow emerging from another",
        "Nocturo":      "midnight-only visible demon, body made of lunar eclipse darkness",
        "Escurix":      "light-devourer predator, swallowing torches and stars to grow stronger",
        "Véunegra":     "black veil manifestation, enveloping enemies in impenetrable darkness cocoon",
        "Tenebris":     "darkness incarnate, no conventional light affects it, anti-light field",
        "Mistumbrio":   "fog-shadow hybrid illusionist, shadow faces forming in the mist",
        "Abysmino":     "abyss-portal creature, staring into it reveals the void between worlds",
        "Sombrakar":    "solar eclipse predator, converting sunlight into solid shadow weapons",
        "Vaziurno":     "interstitial void being, exists in the space between light and shadow",
        "Crepux":       "twilight elemental born at dusk, growing in power as night advances",
        "Noxthar":      "eternal night sovereign, dark crown absorbing all light, ruler of shadows",
        # CRISTAL
        "Facetim":      "gem-cut insect with faceted compound eyes refracting rainbow light",
        "Brilhux":      "crystal shaker creature, rattling gem body creating light shows when disturbed",
        "Vidrilho":     "glass-transparent lizard, organs visible through body, near-invisible in sunlight",
        "Lúmino":       "light battery crystal creature, charging all day then blazing at night",
        "Gemarim":      "gem-scale dragon, each scale a different gemstone with unique property",
        "Prismal":      "prism creature, splitting any energy beam into spectrum, rainbow defense",
        "Reflexor":     "mirror-surface sentinel, reflecting all incoming energy attacks back at source",
        "Cintilux":     "hypnotic crystal jellyfish, pulsing sparkle pattern entrances predators",
        "Quartzel":     "resonant quartz golem vibrating at frequencies that shatter other crystals",
        "Luzcrist":     "light-focusing crystal archer, concentrating beams into cutting energy arrows",
        "Diamar":       "absolute hardness entity, nothing has ever scratched its surface, perfect clarity",
        "Shinério":     "danger-sensing gem that brightens as threat increases, perfect warning system",
        "Prismon":      "living prism manipulating all electromagnetic light, master of spectrum",
        "Glamyte":      "hypnotic crystal face with infinite reflections, entrancing gaze",
        "Luxórion":     "crystallized light deity, body is solidified photons, light in physical form",
        # VENENO
        "Toxito":       "cute poisonous frog with warning colors, gentle-looking but toxic to touch",
        "Peçonhudo":    "fang-filled serpent with hollow venom delivery teeth, venom drop visible",
        "Bafumeio":     "swamp gas creature exhaling visible toxic clouds, trees wilting nearby",
        "Ácidim":       "acid-drool wolf, teeth dissolving metal, corrosive trail burning ground",
        "Nocivo":       "passive poison aura being, no active attack needed, environment poisoning",
        "Vaporoz":      "toxic mist generator, low cloud of poison vapor covering the ground",
        "Miasmelo":     "plague cloud entity, persistent toxic fog zone, pestilential presence",
        "Corrosix":     "rust-and-acid golem corroding anything organic or metal it contacts",
        "Venomix":      "venom laboratory creature, multiple glands producing custom toxin blends",
        "Biletor":      "bile-cannon beast, pressurized corrosive fluid projectile from abdomen",
        "Toxibras":     "paradox creature, poisoning enemies while vaccinating allies simultaneously",
        "Podrino":      "rot accelerator, decomposing matter around it for nutrient harvesting",
        "Morbax":       "pathogen form, infectious touch, single contact begins systemic breakdown",
        "Peçonrex":     "apex venom predator, most potent toxin in known biology, slow and confident",
        "Nexovina":     "water-contaminating entity, single presence taints entire watershed systems",
        # SOM
        "Notinha":      "musical note that became a dancing creature, treble clef body, bouncing to music",
        "Apito":        "ultrasonic whistle being, glass-shattering frequency, invisible sound waves visible",
        "Vibrax":       "resonance lizard, body vibrating at disorienting frequencies, blur effect",
        "Ecoante":      "echo chamber bat, perfectly reproducing any heard sound with delay",
        "Resson":       "harmonic resonator creature, singing in tune with environment",
        "Sônico":       "sonic speed runner leaving sound wave wake, breaking sound barrier visually",
        "Ressonância":  "sympathetic vibration giant, making nearby objects shake in unison",
        "Batida":       "drum-beat creature, rhythmic body pulses creating trance-inducing bass",
        "Melódico":     "healing melody bird, musical notes floating from beak as visible colored light",
        "Grito":        "banshee-scream entity, sound visualized as destructive pressure wave",
        "Harmon":       "harmony conductor, multiple sound entities orbiting in musical formation",
        "Bumbo":        "bass-drum stomper, shockwave foot impacts felt before heard",
        "Agudo":        "ultra-high frequency pin creature, glass-shattering sustained note",
        "Sinfon":       "orchestra director entity, commanding symphonic sound attacks simultaneously",
        "Ópera":        "operatic soprano titan, voice physically moving air as weapon and shield",
        # TEMPO
        "Tique":        "clockwork tick-tock creature, mechanical heartbeat, pendulum tail",
        "Toque":        "bell-chime being marking exact hours, resonant toll vibrating reality",
        "Ampulim":      "living hourglass, sand flowing through transparent body, time-sensitive",
        "Relogito":     "clock face creature with backward-spinning hands when angered",
        "Sécullus":     "century-marked elder, each scale representing an era of history",
        "Erax":         "memory-eraser touching temples with ethereal hands, leaving blank expression",
        "Momentum":     "time-accelerator sprinter, leaving slow-motion afterimage behind",
        "Pendor":       "hypnotic pendulum swinger, every swing is one second of someone's life",
        "Eterno":       "ageless entity untouched by entropy, pristine while everything around decays",
        "Cronix":       "time-fork manipulator, splitting timeline paths visible as branching light",
        "Antigo":       "primordial memory keeper, carrying artifacts of extinct civilizations",
        "Futuro":       "five-seconds-ahead prophet, always reacting to attacks before they're made",
        "Paradoxo":     "simultaneous dual-timeline entity, existing visibly in two moments at once",
        "Zênite":       "peak-moment crystallization, frozen at the highest point of any arc",
        "Infinito":     "time itself in form, loop symbol body, beginning and end meeting at center",
        # LUZ
        "Faisquinha":   "tiny spark fairy bouncing through the air, leaving glitter light trail",
        "Raioluz":      "solar energy surfer riding light beam from sun to earth",
        "Lume":         "soft warm glow orb creature, dungeon illuminator, gentle pulse",
        "Solaris":      "photovoltaic reptile, solar panel scales perfectly angled, full charge aura",
        "Claro":        "shadow-dissolving nova, 100-meter radius pure light, darkness retreating visibly",
        "Aura":         "golden protective field generator, radiant halo over allied heads",
        "Relampo":      "flash-step light being, visible teleportation between positions as lightbeams",
        "Radiante":     "healing light emitter, warm rays causing wounds to close and allies to recover",
        "Glorioso":     "sunrise avatar, born with first morning ray, dawn in creature form",
        "Cintilo":      "morse-code flasher, binary light communication with allies",
        "Ilumin":       "truth-revealer lantern being, hidden things made visible in its glow",
        "Candela":      "inextinguishable flame holder, burning through rain wind and vacuum",
        "Facho":        "wall-penetrating searchlight creature, revealing what's hidden anywhere",
        "Prisma":       "white-light decomposer, breaking any energy into spectrum components",
        "Divino":       "pure light deity, no defined form, blazing solar presence, divine radiance",
        # COSMOS
        "Nebulino":     "nebula-dust kitten with star-forming regions in fluffy cosmic fur",
        "Cometa":       "comet creature with icy nucleus body and glowing plasma tail",
        "Orbital":      "self-orbiting entity, body rotating around its own gravitational center",
        "Galaxico":     "miniature spiral galaxy inside transparent shell, star formation visible",
        "Quasar":       "twin-jet energy being, massive energy blasting from both poles",
        "Pulzar":       "pulsar heartbeat creature, precise timed gamma-ray pulse from chest",
        "Sideral":      "stellar navigator, star charts tattooed on wings, compass rose eyes",
        "Vácuo":        "vacuum field entity, absorbing nearby matter and energy into null space",
        "Astro":        "guide star being, brighter when showing direction, constant in dark sky",
        "Luneto":       "moon phase follower, body waxing and waning with lunar cycle",
        "Solfar":       "solar corona swimmer, living in extreme heat of star atmosphere",
        "Planeta":      "personal gravity being, small rocks and debris orbiting it constantly",
        "Constela":     "dot-pattern entity, connecting light-points forming constellation map",
        "Zenit":        "apex celestial form, directly overhead, peak of any arc",
        "Universo":     "cosmos made manifest, infinite stars visible inside, universe contained in form",
        # METAL
        "Prequinho":    "tiny self-tightening bolt creature, OCD about loose fasteners, wrench arms",
        "Latão":        "polished brass serpent perfectly reflecting surroundings, warm golden metal",
        "Blindado":     "steel-plate tortoise, every surface is thick armor, impervious shell",
        "Chapa":        "flat razor-disc creature, cutting edge all around perimeter, spinning attack",
        "Mecano":       "multi-source salvage robot assembled from mismatched machine parts",
        "Tanque":       "unstoppable advancing bulldozer beast, leaving crushed earth trail",
        "Escudo":       "shield spirit, mirror-polished face deflecting projectiles, defensive stance",
        "Lâmina":       "sword-edge entity, mono-molecular blade edge always maintained, cuts air",
        "Broca":        "rotating drill-tip borer, continuous spin for solid material penetration",
        "Titânio":      "aerospace-grade alloy golem, lightest strongest material, titanium sheen",
        "Robusto":      "maximum-density metal block that compressed itself to ultimate resistance",
        "Cromo":        "chrome-mirror surface that reflects lasers with perfect angle calculation",
        "Bigorna":      "anvil-body forging hammer creature, sparks raining from impact point",
        "Colosso":      "walking fortress with crenellated battlements on back, drawbridge mouth",
        "Muralha":      "infinite wall extension creature, impenetrable barrier wherever it stands",
        # FANTASMA
        "Fantasminha":  "playful bedsheet ghost, tiny form with big hollow eyes, pranking everything",
        "Vaporzinho":   "steam-cloud sprite flowing through keyholes and under doors",
        "Espectrim":    "cold-spot haunter, dropping temperature 10 degrees as it passes through",
        "Sombraluz":    "liminal edge dweller, simultaneously casting shadow and emitting glow",
        "Aparião":      "pop-in pop-out specter, no warning appearance and vanishing",
        "Poltergeist":  "invisible furniture-thrower, household objects levitating and crashing",
        "Etéreo":       "solid-phase walker, appearing to walk through walls with ease",
        "Wraitho":      "fear-feeding wraith, growing larger as prey terror increases",
        "Spectrax":     "face-copying specter, wearing familiar faces to disarm victims",
        "Bansheiro":    "death-keening wail entity, acoustic premonition of mortality",
        "Hauntelo":     "centuries-bound location ghost, territorial about its haunting spot",
        "Phantomix":    "ghost merger, combining with other spirits to amplify collective power",
        "Espírito":     "stubborn soul refusing rest, transparent form with persistent purpose",
        "Revenant":     "revenge-driven undead, burning purpose keeping it in the physical plane",
        "Necrovolt":    "electro-spectral hybrid, ghost powered by static electricity, blue arc ghost",
        # DRAGÃO
        "Drakoninho":   "baby fire drake sneezing unexpected flame bursts, learning to fly",
        "Wyvernito":    "juvenile wyvern practicing wing beats, crashing landings, determined expression",
        "Serpelux":     "sky serpent coiling through clouds, iridescent scale underbelly, hypnotic movement",
        "Ryudrak":      "eastern storm dragon dancing in lightning, pearl orb, whisker tendrils",
        "Winguim":      "hurricane-wing dragon, each flap creating visible pressure wave",
        "Dracozar":     "draconic czar with jeweled crown, smaller dragons attending court around him",
        "Fyrrex":       "rune-scale dragon, magical glyphs appearing on scales during spellcast",
        "Drakonis":     "mirror-scale dragon deflecting magic, metallic natural armor, ancient bearing",
        "Ignithorn":    "igniting-horn dragon, horns erupting in flame channeling magical energy",
        "Scalethar":    "battle-scarred veteran dragon, every scar has a story, proud and ancient",
        "Clawmere":     "dimensional-tear claws, reality splitting at the tips of curved talons",
        "Draklord":     "dragon nobility with ancestral chain, patriarch of draconic dynasty",
        "Vyraxion":     "half-dragon half-storm entity, lightning spine, tempest wings",
        "Nidragor":     "first-born ancient drake, pre-history scale color, timeless primal form",
        "Dragonyx":     "perfect dragon archetype, embodiment of the ideal, apex draconic form",
        # FADA
        "Fadinhas":     "tiny pink fairy dusting magic everywhere, mushroom ring habitat, giggling",
        "Encantura":    "enchantment weaver spinning magic threads into flower blooms out of season",
        "Pixelim":      "pixel fairy, 8-bit visible sprite movement, digital magic sparkles",
        "Glitterix":    "golden glitter trail fairy, persistent sparkle path marking passage",
        "Sparkelo":     "joy-sparkling being, happiness projectiles making sad things smile",
        "Lumiríx":      "pathway lighter, marking safe trails through darkness with gentle light",
        "Feerinha":     "lost-children guardian, appearing to guide the confused back to safety",
        "Dazzlim":      "dazzle-wing attacker, blinding flash from wing-spread opening",
        "Wisping":      "wish-whisperer, desires sometimes becoming reality in fog around it",
        "Shimmerix":    "mood-color-shift fairy, emotional spectrum visible in wing iridescence",
        "Blossomix":    "flower-step fairy, blossoms growing instantly in each footprint",
        "Glowette":     "excitement-brightness fairy, intensity of glow matches emotional state",
        "Twinkling":    "star-linked fairy, winking in sync with specific star far away",
        "Sprinklex":    "power-dust distributor, selective magical enhancement to chosen targets",
        "Celestira":    "fairy queen in aurora robes, reality-rewriting court magic, crown of wishes",
        # PSÍQUICO
        "Psiquim":      "surface-thought reader with visible thought bubbles appearing around targets",
        "Mentalis":     "direct mind projection, enemy sees their own fears from inside",
        "Telepatix":    "long-distance mind bridge, psychic link lines visible between communicants",
        "Alucinex":     "hallucination architect, constructing bespoke sensory illusions for each target",
        "Premonix":     "attack-preview entity, reacting before actions happen with perfect foresight",
        "Clairix":      "psychometric touch-reader, object history playing like film when grasped",
        "Psivolt":      "mental energy converter, thought translated directly into electric combat attack",
        "Mindmere":     "universal mind ocean merging, individual consciousness temporarily dissolved",
        "Intuidor":     "intention-sensor being, detecting hidden motivations before expression",
        "Kinesis":      "telekinetic architect, assembling and dismantling objects with focused thought",
        "Espatix":      "body-sleeping astral traveler, consciousness departing visible as light form",
        "Telekin":      "levitation master, suspending own body while manipulating environment",
        "Cognithor":    "battle-computer mind, processing optimal strategies at machine speed",
        "Visionix":     "parallel-reality viewer, multiple timeline paths visible simultaneously",
        "Omegamind":    "collective consciousness node, connected to all thought ever thinking",
        # LUTA
        "Soqinho":      "tiny but precise knockout puncher, perfect form from small body",
        "Pontapelux":   "spinning roundhouse kicker, momentum-building rotational attack",
        "Upperim":      "classic upward-launch puncher, perfect uppercut geometry, chin-seeker",
        "Jabhero":      "rapid-fire combination jabber, 20 punches per second without stopping",
        "Kombatik":     "style-mixer martial artist, seamlessly blending multiple arts mid-fight",
        "Rushador":     "shoulder-rush charger, low center of gravity burst-speed approach",
        "Strikelux":    "luminous impact striker, each blow leaving glowing energy trace",
        "Grapplino":    "throw-master wrestler, efficient judo-style leverage and projection",
        "Punchix":      "jackhammer-force puncher, impact comparable to industrial machinery",
        "Kicker":       "rapid-fire kicking machine, impossibly fast simultaneous strike illusion",
        "Kickzilla":    "wall-demolishing mega kick, concrete shattering single-leg impact",
        "Sluggerax":    "full-body rotation punch, total mass behind each strike delivery",
        "Brutegor":     "pure mass forward mover, no technique needed at this force level",
        "Ironknuckle":  "forge-hardened fist fighter, knuckle-bone density of metal ore",
        "Ultimapunch":  "fight-ending final strike, the one punch that closes every conflict",
        # INSETO
        "Lagartixa":    "color-shift bug, pattern changing to match surroundings in real-time",
        "Besourelo":    "impact-resistant beetle, combat-proof carapace repelling all damage",
        "Borbolim":     "hypnotic wing-pattern butterfly, opponents mesmerized by wing display",
        "Formigor":     "super-strength carrier ant, lifting 50x own body weight routinely",
        "Escaravim":    "sacred scarab rolling energy spheres, sun-worship behavior pattern",
        "Gafanhotix":   "proportionally impossible jumper, landing creates shockwave crater",
        "Larviço":      "pre-evolution mystery larva, power type unknown, intense potential aura",
        "Cocônix":      "active chrysalis, visible transformative activity inside shifting shape",
        "Chrysalis":    "metamorphosis moment crystallized, form between two states of being",
        "Antleon":      "ambush trap insect, pitfall funnel beneath sand waiting for prey",
        "Scarabeux":    "fortune-luck carrier bug, golden scarab amulet design made real",
        "Beetlord":     "colony commander beetle, smaller beetles following in formation",
        "Mothwing":     "paralytic dust moth, wing scale cloud immobilizing targets",
        "Mantidor":     "prayer-pose ambush predator, strike speed invisible to eye",
        "Hexapod":      "six-limb perfect-coordination fighter, each limb with different weapon",
        # NÉON
        "Néonix":       "neon-green pixel creature blinking in 8-bit patterns, RGB accent lines",
        "Glitchim":     "reality-glitch entity, visual artifacts and corrupted textures around body",
        "Ciberlink":    "network-interface creature, data stream portals opening from fingertips",
        "Pixelglow":    "high-resolution animated sprite, crisp pixel perfect glowing body",
        "Synthrix":     "synthesizer wave rider, sound-wave visualization affecting brain frequencies",
        "Databit":      "conscious data unit, binary stream body, 0s and 1s visibly composing form",
        "Wireframe":    "polygon-outline being, visible mesh structure of pure light geometry",
        "Glowbyte":     "data-rich glowing processor, visual display of combat analytics on skin",
        "Circuitex":    "self-optimizing living circuit, improving efficiency each iteration",
        "Lagzero":      "zero-latency being, moves completed before animation frame updates",
        "Flashnet":     "internet-speed traveler, fiber-optic body traversing network paths",
        "Hyperglow":    "sensor-saturating brightness entity, overpowering detection systems",
        "Matrixter":    "digital reality controller, manipulating local simulation parameters",
        "Virtuelux":    "VR-to-reality crossover being, materialized from virtual simulation",
        "Cybercore":    "digital singularity entity, all connected systems answering to it",
        # NUCLEAR
        "Radiino":      "soft-glow radiation emitter, constant low-level Geiger clicks audible",
        "Atomillo":     "conscious stable atom, electron cloud orbiting visible around body",
        "Nucléix":      "unstable nucleus creature searching for stable configuration, energy leaking",
        "Fusionix":     "hydrogen fusion reactor in chest, miniature star burning inside",
        "Fissurex":     "atom-splitter scream, nucleus division chain reaction from sound alone",
        "Radiotor":     "multi-spectrum radiation broadcaster, alpha beta gamma all emitting",
        "Halflifo":     "half-life decay tracker, power measurably diminishing in predictable pattern",
        "Decayix":      "entropy accelerator, structures near it aging centuries per second",
        "Isótopo":      "isotope-switching entity, oscillating between stable and unstable states",
        "Falloutix":    "persistent contamination trail, radioactive footprints glowing for days",
        "Gammaray":     "gamma-burst emitter, penetrating radiation visible as blue Cherenkov glow",
        "Reatorix":     "contained nuclear reactor form, coolant rods visible through transparent shell",
        "Critimass":    "critical mass threshold creature, approaching detonation point constantly",
        "Meltorex":     "core-meltdown entity, melting any material including metal on contact",
        "Nucleagor":    "mega-fusion amalgam, multiple nuclear processes occurring simultaneously",
        # ESPÍRITO
        "Alminha":      "gentle home-guardian soul, warm light protecting family space",
        "Kamirix":      "nature deity kamigami form, river and mountain spirits visible in aura",
        "Shintorix":    "shrine spirit blessing honest visitors, torii gate materialized around it",
        "Ancestrix":    "ancestor chain carrier, ethereal lineage visible stretching behind it",
        "Espirix":      "free-roaming soul without territory, pure spiritual freedom",
        "Soulix":       "incarnation-refusing spirit, choosing freedom over physical form",
        "Totemix":      "clan-spirit totem, tribal markings representing entire people",
        "Orixim":       "African deity form, sacred power orixá embodied in combat",
        "Blessor":      "pre-battle blessing distributor, consecrating allies before each fight",
        "Holyrim":      "holy presence purifying corrupted environments, sacred light emanation",
        "Sacredix":     "sacred object made sentient, religious significance imbued with will",
        "Mantra":       "chanting power amplifier, sacred syllables as visible energy waves",
        "Divinix":      "descended deity in limited mortal form, divine constrained by flesh",
        "Transcend":    "physical-form shedder, essence remaining after body dissolution",
        "Enlighten":    "perfect peace warrior, absolute serenity and absolute power unified",
        # MECÂNICO
        "Robotinho":    "rust-covered janitor bot with big sad eyes, still trying its best",
        "Automec":      "maintenance automaton turned adventurer, tools for weapons",
        "Dronix":       "surveillance combat drone, multiple camera eyes, hover mode default",
        "Cogwheelx":    "master-gear of all machine systems, everything turning around it",
        "Steamrix":     "Victorian steam-punk engine creature, pressure valve safety releases",
        "Pistonix":     "hydraulic piston puncher, mechanical arm compression-burst strikes",
        "Valvulor":     "flow-control valve body, regulating energy through allied machine systems",
        "Turbinix":     "wind-generating turbine spinner, rotational cutting attack on overload",
        "Transmitor":   "tactical data relay, broadcasting battle commands to mechanical allies",
        "Gearborg":     "half-gear half-warrior, mechanical heart visible through chest plate",
        "Motorax":      "high-performance racing engine made physical, never overheating",
        "Clockwork":    "Swiss-precision mechanical perfection, every gear timed exactly right",
        "Steamborg":    "industrial revolution survivor cyborg, brass and steam aesthetics",
        "Technogor":    "bio-mechanical fusion warrior, organic tissue and circuit board merged",
        "Mekavolt":     "electric-core mechanical apex, perfect synthesis of machine and energy",
        # VENTOS
        "Brisim":       "gentle breeze entity concealing internal tempest, deceptively calm",
        "Tufarix":      "miniature typhoon that grows when challenged, spiral arm winds",
        "Zonalix":      "low-pressure center being, drawing in all surrounding air systems",
        "Cyclonix":     "perfect cyclone form, eye wall visible, organized destruction spiral",
        "Galerix":      "sudden gale materializer, appearing without forecast warning",
        "Tempestix":    "oceanic storm system alive, warm-core hurricane driving forward",
        "Twistix":      "perpetual-rotation tornado legs, drilling through obstacles",
        "Squallo":      "sudden squall line ambusher, catching sailors completely unprepared",
        "Zephyrion":    "western wind deity personified, gentle but persistent ancient force",
        "Anemix":       "wind speed controller, setting and measuring airflow with precision",
        "Typhonex":     "category-5 typhoon conscious, coastal devastation scale entity",
        "Sirocco":      "Saharan hot wind traveler, desiccating everything touched with dry heat",
        "Mistral":      "cold north wind razor, Mediterranean speed-master cold front",
        "Boreamix":     "north wind god Boreas in creature form, winter herald, frost caller",
        "Zondragor":    "ultimate wind force, beyond categorization, topographic-scale destruction",
        # MAGMA
        "Lavinha":      "small lava puddle that learned to roll, warm gentle glow, harmless looking",
        "Magmarim":     "magma creature with cooling outer crust hiding molten interior",
        "Ignerix":      "spontaneous combustion salamander, 800-degree internal temperature",
        "Pyroclax":     "pyroclastic flow condensed into running form, hot ash cloud body",
        "Emberlux":     "eternal ember that never fully extinguishes, glowing orange-red core",
        "Calderon":     "volcanic cauldron entity, bubbling molten rock contents visible inside",
        "Scorcherix":   "superheating atmosphere around body, air visibly boiling and distorting",
        "Infernix":     "hell-temperature concentrated being, infernal heat beyond measurement",
        "Lavabeast":    "full lava beast emerging from volcanic vent, basalt cooling on surface",
        "Moltenix":     "fully liquefied high-temperature form, every material melts on contact",
        "Cinder":       "ember and ash form, reigniting from any remaining warmth source",
        "Eruption":     "volcanic eruption given legs, walking lava fountain constantly erupting",
        "Volcanus":     "ambulatory volcano, complete with magma chamber, vent, and pressure system",
        "Firestorm":    "lava and fire tornado fusion, spinning column of volcanic destruction",
        "Magmarex":     "apex magma predator, absolute ruler of volcanic domain, lava king",
        # ARCANO
        "Arcalix":      "rune-study apprentice, floating glyphs being actively researched",
        "Rúnico":       "self-activating rune stone, magic text reading itself into existence",
        "Spellrix":     "instinctive spellcaster, no grimoire needed, pure arcane intuition",
        "Glamorix":     "glamour-weaver changing perceived reality for all observers",
        "Hexamix":      "personalized curse crafter, custom-fitted hexes for each target",
        "Grimora":      "living spell-book, pages opening to reveal active enchantments",
        "Occultix":     "veil-thin reality practitioner, operating at boundary between worlds",
        "Witchix":      "brew-master sorcerer, potion effects and hex effects combined",
        "Conjuror":     "entity-summoner, doorways to other planes opening behind it",
        "Runeborn":     "rune-origin being, emerged directly from a primordial power inscription",
        "Eldritch":     "incomprehensible cosmic magic entity, geometry wrong, perception bending",
        "Sorceron":     "arcane sovereign with millennia of accumulated spell mastery",
        "Arcanix":      "spell-master archive, every incantation ever cast catalogued and available",
        "Mystara":      "magical knowledge embodiment, complete arcane library made conscious",
        "Sorceling":    "pure sorcery given form, the platonic ideal of magical power",
        # ESPECIAIS
        "OXIGÉNIO":     "transparent wind creature made of pure oxygen molecules, breathing creates visible energy, O2 formula on body",
        "Ciclone-Rei":  "chaos vortex king with crown of spinning debris, purple-black chaos energy swirling",
        "DEUS-DRAGÃO":  "absolute supreme dragon beyond elements, golden aura, primordial energy from pre-creation",
        # BOSSES
        "Rei das Chamas":        "colossal fire king on obsidian throne, crown of living flames, rivers of lava bowing before him",
        "Titã dos Mares":        "massive whale leviathan with ancient barnacle armor, ocean trenches visible beneath it",
        "Lorde das Sombras":     "soul-devouring shadow lord, thousands of captured souls visible screaming inside dark form",
        "Maestro do Caos":       "chaos orchestra conductor with violin bow made of silence, destroying reality with each stroke",
        "Guardião das Eras":     "frozen-time clockwork titan, gears stopped mid-turn, eternal moment captured",
        "Arcanjo Solar":         "blinding solar archangel, noon-sun brightness, wings made of concentrated light energy",
        "Vazio Estelar":         "sentient black hole devouring galaxies, stars visibly falling into its event horizon",
        "Leviatã de Ferro":      "iron leviathan fortress-sized, with cannon towers and battlements grown from its metal body",
        "Dragão do Apocalipse":  "apocalypse dragon blocking the sky entirely, each wing-beat destroying civilization below",
        "DEUS DO CAOS":          "reality-breaking chaos god, existence flickering in and out, wrong geometry everywhere",
        "Entidade Verdejante":   "forest heart entity, entire ecosystem living on and within its body, ancient beyond measure",
        "Colosso da Montanha":   "mountain-scale stone colossus, actual mountain summits as shoulders, valleys between legs",
        "Senhor dos Vendavais":  "sky-filling wind lord, atmosphere itself a weapon, clouds forming war formation",
        "Tirano Glacial":        "eternal ice tyrant freezing time itself, glacial advance unstoppable, absolute zero aura",
        "Deus da Tempestade":    "thunder god speaking in lightning bolts, storm crown, hurricane body",
        "Mente Suprema":         "all-knowing supreme mind, every thought ever had visible around it, cosmic oracle form",
        "Campeão Indomável":     "undefeated champion with aura of victory, iron fists never unclenched, eternal fight stance",
        "Imperador dos Enxames": "living hive emperor, body composed of billions of individual insects working as one",
        "Soberano de Néon":      "digital grid sovereign, entire internet made physical, neon data streams forming body",
        "Entidade Radioativa":   "radioactive entity at critical mass, unstable core visible, continent-scale energy",
        "Ancestral Sagrado":     "voice-of-all-ancestors entity, every dead elder speaking through it simultaneously",
        "Engenheiro do Caos":    "perfect destruction machine, engineered specifically to unmake everything that exists",
        "Senhor do Magma":       "magma lord from earth's core, planet's inner heat personified, tectonic power",
        "Mestre Arcano":         "secret-keeper arcane master, forbidden spells orbiting like satellites, hidden power",
        "Espectro do Vazio":     "inter-dimensional lost soul, glimpsing multiple planes simultaneously, seeking vessel",
        "Dragão Primordial":     "first dragon before all others, primordial scales, father of every draconic lineage",
        "Rainha das Fadas":      "fairy queen with enchanted realm visible inside wings, ancient magic of first forest",
        "Void King":             "void king beyond comprehension, existence-negating aura, crystalline crown of nothingness",
        "Nico":                  "deceptively cute cosmic cat purring while planets crumble, soft paws hiding universe-ending power",
        "murilo":                "mysterious chaotic figure that should not exist, reality distorting around him, unspeakable form",
        "???":                   "entity beyond all classification, impossible geometry, looking at it breaks perception",
    }

    # Estilos base por tipo (fallback se não houver override de nome)
    type_base = {
        "fogo":     "fire elemental creature with molten core, lava veins visible under skin, ember particles floating",
        "água":     "aquatic elemental with transparent water body, flowing currents inside form, bubble trails",
        "planta":   "plant creature covered in living vines and flowers, bioluminescent spores, organic beauty",
        "terra":    "stone and earth golem with geological layers visible, rugged mineral textures",
        "ar":       "wind elemental with semi-transparent form, feathers and currents flowing freely",
        "gelo":     "ice crystal creature with sharp frost geometry, cool blue-white aura, snowflake aura",
        "trovão":   "electric creature crackling with lightning, yellow-blue plasma arcs between extremities",
        "sombra":   "shadow entity with dark smoke body, glowing purple eyes in darkness",
        "cristal":  "crystal-formed being with faceted refractive surface, prismatic light scatter",
        "veneno":   "toxic creature dripping corrosive liquid, sickly green-purple color, mutated form",
        "som":      "sound wave creature with vibrating body, musical note particles orbiting",
        "tempo":    "time entity with hourglass and clock elements, temporal distortion aura",
        "luz":      "radiant light being with golden aura, solar energy corona, pure luminescence",
        "cosmos":   "celestial entity with galaxies and nebulae inside transparent body",
        "metal":    "metallic armored creature with machine components, industrial shine",
        "fantasma": "translucent ghost form with ethereal glow, floating without touching ground",
        "dragão":   "powerful dragon with scales, wings, horns, ancient and fierce",
        "fada":     "delicate fairy with gossamer wings, magical sparkles, enchanted beauty",
        "psíquico": "psychic creature with glowing third eye, purple energy aura, mind waves",
        "luta":     "muscular fighter in battle stance, combat energy emanating, power pose",
        "inseto":   "giant insect with detailed exoskeleton, multiple limbs, compound eyes",
        "néon":     "cyberpunk neon creature with digital circuit patterns, glowing LED colors",
        "nuclear":  "radioactive glowing entity with unstable energy core, Cherenkov glow",
        "espírito": "spiritual being with divine aura, sacred light, serene powerful presence",
        "mecânico": "steam-punk mechanical robot with gears and pistons, industrial design",
        "ventos":   "wind tornado creature with swirling air currents, storm formations",
        "magma":    "molten magma beast with glowing lava body, volcanic rock armor",
        "arcano":   "arcane sorcerer creature surrounded by glowing runes, magical energy",
        "caos":     "chaotic swirling entity with unpredictable energy, reality warping",
        "absoluto": "absolute power beyond elements, golden divine energy, primordial",
        "fofa":     "adorably dangerous creature with cosmic power hidden in cute form",
        "molestador": "disturbing chaotic entity, reality bending around its presence",
    }

    # Raridade afeta a escala e intensidade visual
    rarity_mod = {
        "comum":    "small, simple design, soft colors, approachable",
        "incomum":  "medium size, more details, vivid colors",
        "raro":     "impressive creature, intricate details, strong colors",
        "épico":    "epic scale, highly detailed, dramatic lighting, intense colors",
        "lendário": "legendary being, godlike presence, radiant aura, breathtaking detail",
        "mítico":   "mythical entity glowing with divine energy, otherworldly beauty",
        "boss":     "colossal boss monster, massive scale, terrifying presence, battlefield-filling",
        "divino":   "divine entity beyond normal classification, transcendent power visible",
        "Divino":   "divine entity beyond normal classification, transcendent power visible",
    }.get(rare, "")

    # Build prompt
    name_visual = name_overrides.get(nome, "")

    if name_visual:
        # Specific override: use it as the primary visual description
        emoji_hint = f"visual motif inspired by {emoji}, " if emoji and emoji != "❓" else ""
        prompt = (
            f"creature called '{nome}': {name_visual}, "
            f"{emoji_hint}"
            f"{rarity_mod}, "
            f"fantasy RPG monster concept art, signature distinctive design, "
            f"highly detailed digital painting, character sheet style, "
            f"cinematic lighting, sharp focus, vibrant saturated colors, "
            f"professional creature design, ArtStation trending, best quality, 8k"
        )
    else:
        # Fallback: combine emoji + nome + tipo para algo único e não-genérico
        tipo_desc = type_base.get(tipo, f"{tipo} elemental fantasy creature")
        emoji_hint = f"visually inspired by the emoji {emoji}, " if emoji and emoji != "❓" else ""
        prompt = (
            f"unique original creature named '{nome}', "
            f"{emoji_hint}"
            f"{tipo_desc}, "
            f"design elements and silhouette echoing the name '{nome}' and its phonetics, "
            f"{rarity_mod}, "
            f"fantasy RPG monster concept art, signature distinctive features, "
            f"highly detailed digital painting, character sheet style, "
            f"cinematic lighting, sharp focus, vibrant saturated colors, "
            f"professional creature design, ArtStation trending, best quality, 8k"
        )

    if is_boss:
        prompt += ", epic boss battle atmosphere, dramatic scale, menacing presence, awe-inspiring"

    prompt += ", no text, no watermark, clean composition"

    return prompt


OWNER_ID = 1322369063132860476

class RefazerImagemView(discord.ui.View):
    """Botão 🔄 Refazer que apaga o cache e gera uma nova imagem (só o dono do bot)."""
    def __init__(self, entry: dict):
        super().__init__(timeout=120)
        self.entry = entry

    @discord.ui.button(label="🔄 Refazer imagem", style=discord.ButtonStyle.secondary)
    async def refazer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ Só o dono do bot pode refazer imagens.", ephemeral=True)
            return
        mon_name = self.entry["n"]
        button.disabled = True
        button.label = "⏳ A gerar..."
        await interaction.response.edit_message(view=self)
        try:
            delete_cached_image_url(mon_name)
            prompt = await gerar_prompt_imagem(self.entry)
            print(f"[IMG] {mon_name} → REFAZER por {interaction.user}")
            img_bytes = None
            last_err = None
            for attempt in range(5):
                try:
                    img_bytes = await generate_image_with_queue(prompt)
                    break
                except Exception as e:
                    last_err = str(e)
                    if "429" in last_err and attempt < 4:
                        await asyncio.sleep(min(2 ** attempt + random.uniform(0.5, 2.0), 30.0))
                        continue
                    raise
            if img_bytes is None:
                raise Exception(f"Pollinations AI indisponível ({last_err})")
            safe_filename = f"{_img_cache_key(mon_name)}_{int(time.time())}.png"
            discord_url = await upload_image_to_discord_cache(bot, img_bytes, safe_filename)
            desc_line = self.entry.get("desc", f"{self.entry.get('t','').capitalize()} • {self.entry.get('rare','')}")
            embed = discord.Embed(
                title=f"{self.entry.get('e','❓')} {mon_name}",
                description=desc_line,
                color=RARE_COLOR.get(self.entry.get("rare"), 0x888888)
            )
            new_view = RefazerImagemView(self.entry)
            if discord_url:
                store_cached_image_url(mon_name, discord_url)
                embed.set_image(url=discord_url)
                embed.set_footer(text="🎨 Gerado com Pollinations AI (flux) • guardado no cache")
                await interaction.edit_original_response(embed=embed, view=new_view)
            else:
                file = discord.File(io.BytesIO(img_bytes), filename="monster.png")
                embed.set_image(url="attachment://monster.png")
                embed.set_footer(text="🎨 Gerado com Pollinations AI (flux)")
                await interaction.edit_original_response(embed=embed, attachments=[file], view=new_view)
        except Exception as e:
            button.disabled = False
            button.label = "🔄 Refazer imagem"
            await interaction.edit_original_response(
                content=f"❌ Erro ao refazer: `{str(e)[:150]}`", view=self
            )


async def _gerar_e_enviar_imagem(interaction: discord.Interaction, entry: dict, followup: bool = True):
    """Lógica partilhada de gerar imagem e enviar embed com botão Refazer."""
    mon_name = entry["n"]

    cached_url = get_cached_image_url(mon_name)
    if cached_url:
        print(f"[IMG] {mon_name} → cache HIT")
        desc_line = entry.get("desc", f"{entry.get('t','').capitalize()} • {entry.get('rare','')}")
        embed = discord.Embed(
            title=f"{entry.get('e','❓')} {mon_name}",
            description=desc_line,
            color=RARE_COLOR.get(entry.get("rare"), 0x888888)
        )
        embed.set_image(url=cached_url)
        embed.set_footer(text="🎨 Imagem guardada (cache Discord)")
        await interaction.followup.send(embed=embed, view=RefazerImagemView(entry))
        return

    prompt = await gerar_prompt_imagem(entry)
    print(f"[IMG] {mon_name} → cache MISS | a gerar...")

    img_bytes = None
    last_err = None
    MAX_ATTEMPTS = 5
    for attempt in range(MAX_ATTEMPTS):
        try:
            img_bytes = await generate_image_with_queue(prompt)
            break
        except Exception as e:
            last_err = str(e)
            if "429" in last_err and attempt < MAX_ATTEMPTS - 1:
                wait = min(2 ** attempt + random.uniform(0.5, 2.0), 30.0)
                print(f"[IMG] 429, retry {attempt+1}/{MAX_ATTEMPTS} em {wait:.1f}s")
                await asyncio.sleep(wait)
                continue
            raise

    if img_bytes is None:
        raise Exception(f"Pollinations AI indisponível após {MAX_ATTEMPTS} tentativas ({last_err})")

    safe_filename = f"{_img_cache_key(mon_name)}.png"
    discord_url = await upload_image_to_discord_cache(bot, img_bytes, safe_filename)

    desc_line = entry.get("desc", f"{entry.get('t','').capitalize()} • {entry.get('rare','')}")
    embed = discord.Embed(
        title=f"{entry.get('e','❓')} {mon_name}",
        description=desc_line,
        color=RARE_COLOR.get(entry.get("rare"), 0x888888)
    )
    view = RefazerImagemView(entry)
    if discord_url:
        store_cached_image_url(mon_name, discord_url)
        embed.set_image(url=discord_url)
        embed.set_footer(text="🎨 Gerado com Pollinations AI (flux) • guardado no cache")
        await interaction.followup.send(embed=embed, view=view)
    else:
        file = discord.File(io.BytesIO(img_bytes), filename="monster.png")
        embed.set_image(url="attachment://monster.png")
        embed.set_footer(text="🎨 Gerado com Pollinations AI (flux) — configura IMAGE_CACHE_CHANNEL para cache permanente")
        await interaction.followup.send(embed=embed, file=file, view=view)


@tree.command(name="imagem", description="Gera uma imagem artística de um monster")
@app_commands.describe(nome="Nome do monster")
async def monster_image(interaction: discord.Interaction, nome: str):
    await interaction.response.defer(thinking=True)

    nome_lower = nome.lower()
    entry = (
        MON_INDEX.get(nome) or
        MON_INDEX.get(nome.title()) or
        next((m for m in MONS if m["n"].lower() == nome_lower), None) or
        next((m for m in MONS if m["n"].lower().startswith(nome_lower)), None) or
        BOSS_INDEX.get(nome) or
        next((b for b in BOSSES if b["n"].lower() == nome_lower), None) or
        next((b for b in BOSSES if b["n"].lower().startswith(nome_lower)), None)
    )
    if not entry:
        await interaction.followup.send(f"❌ Monster **{nome}** não encontrado!", ephemeral=True)
        return
    try:
        await _gerar_e_enviar_imagem(interaction, entry)
    except Exception as e:
        print(f"[ERRO IMAGEM] {entry.get('n', nome)} → {type(e).__name__}: {str(e)}")
        await interaction.followup.send(
            f"❌ Erro ao gerar imagem de **{entry.get('n', nome)}**.\n\nErro: `{str(e)[:150]}`",
            ephemeral=True
        )

@tree.command(name="ajuda",description="Mostra todos os comandos")
async def help_cmd(interaction:discord.Interaction):
    embed=discord.Embed(title="⚔️ Monster Hunter RPG — Ajuda",description="Captura monstros, enfrenta bosses e sobe no ranking!",color=0xffd700)
    cmds=[
        ("🏹 `/caçar`","Encontra monstro selvagem **(10% chance de boss aparecer!)** — Bosses são todos aleatórios!"),
        ("🐾 `/equipa`","Vê a tua equipa"),("📦 `/box`","Vê a box"),("⭐ `/ativar [pos]`","Define monstro ativo"),
        ("💊 `/curar [tipo]`","Cura (poção/superpoção/megapoção/hyperpoção/revive/maxrevive)"),
        ("🎒 `/inventario`","Vê itens e materiais"),("🛒 `/loja`","Abre a loja"),("🧪 `/usar [item]`","Usa item"),
        ("📖 `/pokedex`","Pokédex + botão Boss Final quando completa"),("🔄 `/trocar [ação] [nome]`","Troca equipa/box"),
        ("🏆 `/ranked`","Rank e leaderboard"),("📥 `/ranked-import [código]`","Adiciona amigo"),
        ("✏️ `/nomear [nome]`","Define nome"),("🌀 `/rebirth`","Rebirth (10.000💰)"),("👤 `/perfil`","Perfil completo"),
        ("💰 `/vender`","Vende materiais por ouro (70% do valor base)"),
        ("🎨 `/imagem [nome]`","Gera uma imagem artística do monster escolhido"),
    ]
    for n,d in cmds: embed.add_field(name=n,value=d,inline=False)
    embed.add_field(name="⚔️ Batalha Selvagem",
        value="⚔️ **Lutar** — Ataca (cooldown 5s, inimigo contra-ataca simultaneamente!)\n🔮 **Ball** — Tenta capturar\n⭐ **Master Ball** — Captura garantida\n🏃 **Fugir**",inline=False)
    embed.add_field(name="👹 Batalha de Boss",
        value="⚔️ Atacar · 🛡️ Defender (-60% dano) · 🔮 Ball (cd 3 turnos) · 💊 Poção · 🏃 Retirar\n⚠️ A cada 3 turnos o boss carrega **Ataque Especial** (x1.8)!\n⚠️ Confirmação extra ao atacar boss <20% HP!",inline=False)
    await interaction.response.send_message(embed=embed)

# ══════════════════════════════════════════════
# EVENTOS
# ══════════════════════════════════════════════

@bot.event
async def on_ready():
    print(f"Bot conectado: {bot.user} (ID: {bot.user.id})")
    try:
        # Sync global — aparece para TODOS os utilizadores em todos os servidores
        # (pode demorar até 1h do Discord propagar, mas funciona)
        synced = await tree.sync()
        print(f"Sync global: {len(synced)} comandos")
        for cmd in synced: print(f"  /{cmd.name}")

        # Sync imediato em cada guild onde o bot está (para testes instantâneos)
        for guild in bot.guilds:
            try:
                tree.copy_global_to(guild=guild)
                gs = await tree.sync(guild=guild)
                print(f"  Guild {guild.name}: {len(gs)} cmds sincronizados")
            except Exception as ge:
                print(f"  Guild {guild.name} erro: {ge}")

    except Exception as e:
        print(f"Erro sync: {e}"); import traceback; traceback.print_exc()
    await bot.change_presence(activity=discord.Game(name="/ajuda | Monster Hunter RPG"))

    # Pré-geração de imagens em background (silenciosa, não bloqueia o bot)
    asyncio.create_task(_pregenerate_monster_images())

async def _pregenerate_monster_images():
    """Gera em background as imagens de todos os monsters/bosses que ainda
    não estão em cache. Lento mas silencioso. Após terminar (algumas horas),
    todas as chamadas a /imagem serão instantâneas (cache HIT)."""
    await asyncio.sleep(15)  # dá tempo ao bot de assentar antes de começar
    try:
        all_entries = []
        seen = set()
        for src in (MONS, BOSSES):
            for m in src:
                key = _img_cache_key(m.get("n", ""))
                if key in seen:
                    continue
                seen.add(key)
                all_entries.append(m)

        pending = [m for m in all_entries if not get_cached_image_url(m["n"])]
        total = len(pending)
        if total == 0:
            print("[img-pregen] todas as imagens já estão em cache ✅")
            return

        if not IMAGE_CACHE_CHANNEL_ID:
            print("[img-pregen] IMAGE_CACHE_CHANNEL não configurado — pré-geração desativada")
            print("[img-pregen] Define a variável de ambiente IMAGE_CACHE_CHANNEL com o ID do canal")
            return

        print(f"[img-pregen] iniciando pré-geração de {total} imagens em background…")
        done = 0
        fail = 0
        for m in pending:
            try:
                if get_cached_image_url(m["n"]):
                    continue  # já gerado entretanto
                    
                    prompt = await gerar_prompt_imagem(m)
                img_data = await generate_image_with_queue(prompt, max_attempts=4)
                
                # Retry com backoff para lidar com 429 da Pollinations AI
                img_data = None
                for pregen_attempt in range(4):
                    try:
                        img_data = await _fetch_monster_image_bytes(m)
                        break
                    except Exception as e:
                        err_str = str(e)
                        if "429" in err_str and pregen_attempt < 3:
                            wait = min(10 * (2 ** pregen_attempt) + random.uniform(0, 5), 120)
                            print(f"[img-pregen] 429 em {m.get('n','?')}, aguardar {wait:.0f}s…")
                            await asyncio.sleep(wait)
                            continue
                        raise
                if img_data:
                    safe_fn = f"{_img_cache_key(m['n'])}.png"
                    url = await upload_image_to_discord_cache(bot, img_data, safe_fn)
                    if url:
                        store_cached_image_url(m["n"], url)
                        done += 1
                    else:
                        print(f"[img-pregen] upload falhou para {m.get('n','?')}")
                        fail += 1
                if done % 10 == 0 and done > 0:
                    print(f"[img-pregen] progresso: {done}/{total} (falhas: {fail})")
            except Exception as e:
                fail += 1
                print(f"[img-pregen] falha em {m.get('n','?')}: {e}")
            # Pausa entre imagens para respeitar rate-limit
            await asyncio.sleep(5)
        print(f"[img-pregen] concluído ✅ geradas={done} falhas={fail} total={total}")
    except Exception as e:
                fail += 1
                print(f"[img-pregen] falha em {m.get('n','?')}: {e}")

@tree.error
async def on_error(interaction:discord.Interaction,error:app_commands.AppCommandError):
    print(f"Erro: {error}"); import traceback; traceback.print_exc()
    try:
        msg="⚠️ Erro interno. Tenta novamente."
        if interaction.response.is_done(): await interaction.followup.send(msg,ephemeral=True)
        else: await interaction.response.send_message(msg,ephemeral=True)
    except: pass

if __name__=="__main__":
    TOKEN=os.environ.get("DISCORD_TOKEN","")
    if not TOKEN: print("ERRO: Define DISCORD_TOKEN.\n  Windows: set DISCORD_TOKEN=o_teu_token\n  Linux: export DISCORD_TOKEN=o_teu_token"); exit(1)
    print("A iniciar o bot..."); bot.run(TOKEN)

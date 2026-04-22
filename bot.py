"""
Monster Hunter RPG — Discord Bot
=================================
Port completo do jogo HTML (monster_hunter_V117) para Discord.

Mecânicas implementadas:
- Sistema de tipos com vantagens/desvantagens
- Captura com chance dinâmica (HP, raridade, balls)
- Equipa (6 slots) + Box ilimitada
- Leveling, tiers (1-5) e Rebirth
- Loja com itens permanentes e consumíveis
- Batalha contra selvagens (View interativa)
- Batalha contra bosses com HUD completa:
  * Aviso de ataque especial a cada 3 turnos (x1.8 dano)
  * Cooldown de Ball (3 turnos)
  * Escudo + Defender (dano x0.4)
  * Penalidade de raridade (comum x2, incomum x1.5)
  * Aviso automático de 20% HP do boss
  * Escala baseada na força média da equipa
- Boss Final em 2 FASES: ??? → Leonking (requer Pokédex completa)
- Boss SECRETO: Nico (3 poções seguidas no monstro OXIGÉNIO)
- Boss oculto: murilo / Void King (só capturável com Master Ball)

Ficheiro único, save por utilizador em JSON (pasta `saves/`).
"""

from __future__ import annotations

import json
import os
import random
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

# dotenv é opcional em ambientes tipo Vercel/Railway onde as envs já vêm do host
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ══════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ══════════════════════════════════════════════════════════════

TOKEN = os.environ.get("DISCORD_TOKEN", "").strip()
SAVES_DIR = "saves"
os.makedirs(SAVES_DIR, exist_ok=True)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
tree = bot.tree


# ══════════════════════════════════════════════════════════════
# DADOS: RARIDADES, TIPOS, MONSTROS
# ══════════════════════════════════════════════════════════════

RARITY_PLAN = [
    {"rare": "comum",    "catch": 0.66, "hp": 24,  "atk": 5,  "mat": 8},
    {"rare": "comum",    "catch": 0.64, "hp": 27,  "atk": 5,  "mat": 9},
    {"rare": "comum",    "catch": 0.62, "hp": 30,  "atk": 6,  "mat": 10},
    {"rare": "incomum",  "catch": 0.56, "hp": 34,  "atk": 7,  "mat": 13},
    {"rare": "incomum",  "catch": 0.53, "hp": 37,  "atk": 8,  "mat": 15},
    {"rare": "incomum",  "catch": 0.50, "hp": 40,  "atk": 9,  "mat": 17},
    {"rare": "raro",     "catch": 0.41, "hp": 46,  "atk": 11, "mat": 24},
    {"rare": "raro",     "catch": 0.38, "hp": 50,  "atk": 12, "mat": 27},
    {"rare": "raro",     "catch": 0.35, "hp": 54,  "atk": 13, "mat": 30},
    {"rare": "épico",    "catch": 0.26, "hp": 62,  "atk": 15, "mat": 40},
    {"rare": "épico",    "catch": 0.23, "hp": 68,  "atk": 17, "mat": 46},
    {"rare": "lendário", "catch": 0.17, "hp": 82,  "atk": 19, "mat": 60},
    {"rare": "lendário", "catch": 0.14, "hp": 90,  "atk": 21, "mat": 70},
    {"rare": "mítico",   "catch": 0.10, "hp": 108, "atk": 24, "mat": 90},
    {"rare": "mítico",   "catch": 0.08, "hp": 118, "atk": 27, "mat": 105},
]

RARITY_COLOR = {
    "comum": 0x888888, "incomum": 0x50c050, "raro": 0x5090e0,
    "épico": 0xa050e0, "lendário": 0xe0a020, "mítico": 0xff4080,
    "divino": 0xffd700,
}

# Cada tipo define um conjunto de 15 monstros (um por linha da RARITY_PLAN)
TYPE_DEFS = [
    {"t": "fogo",   "c": 0xe2583d, "mat": "Brasa",   "hpMod": 0,  "atkMod": 0,
     "names": ["Flaminho","Labaréu","Brasalto","Fornalix","Tochino","Faíscor","Fogaréu","Pirólito","Chamego","Cinzal","Braseon","Magmário","Ardencor","Vulkar","Solferno"],
     "emojis": ["🔥","🦊","🕯️","🐅","🏮","🧨","🐲","🍂","☄️","🦁","🎇","🌋","❤️‍🔥","🐦‍🔥","☀️"]},
    {"t": "água",   "c": 0x3a92d9, "mat": "Gota",    "hpMod": -1, "atkMod": 0,
     "names": ["Marulhinho","Bolhudo","Aqualume","Mariscoz","Pingorim","Riachito","Mareco","Ondal","Nautelo","Aqualux","Tsuniko","Abissor","Maréon","Leviagota","Tidalux"],
     "emojis": ["💧","🐟","🌊","🐠","🫧","🐸","🦦","💦","🦭","🐬","🦈","🐋","🌧️","🪸","🔱"]},
    {"t": "planta", "c": 0x4ea85f, "mat": "Folha",   "hpMod": 3,  "atkMod": -1,
     "names": ["Brotinho","Ramalho","Trepiko","Verdelim","Mossito","Clorofim","Galhudo","Vinhedo","Botanix","Silvério","Selvar","Espinhaflor","Clorossauro","Floracel","Matrizal"],
     "emojis": ["🌿","🍀","🪴","🌱","🍃","🌵","🌾","🌻","🌳","🍄","🌺","🪻","🌴","🌸","🌲"]},
    {"t": "terra",  "c": 0x9b7b54, "mat": "Pedra",   "hpMod": 8,  "atkMod": -2,
     "names": ["Cascalho","Barrolho","Territo","Tremorim","Areíto","Pedrino","Lamosso","Sedento","Gravito","Monterro","Basalto","Colossalmo","Terragor","Pedrax","Titanterra"],
     "emojis": ["🪨","🦔","🐗","🪵","🏜️","⛰️","🐢","🦬","🐘","🦏","🧱","🏔️","🗿","⚒️","🌍"]},
    {"t": "ar",     "c": 0x80cde0, "mat": "Pluma",   "hpMod": -3, "atkMod": 1,
     "names": ["Assobinho","Névolo","Brisito","Volitro","Nublim","Aeral","Celsito","Ventor","Ciclar","Nebulon","Furavento","Aerólux","Tempespin","Estratelo","Skythar"],
     "emojis": ["🪶","☁️","🕊️","🌬️","🪽","🪁","🎈","🦅","🌪️","🦉","🦤","🐦","🪂","🌫️","🦜"]},
    {"t": "gelo",   "c": 0x77c9df, "mat": "Cristal", "hpMod": 4,  "atkMod": 1,
     "names": ["Gelito","Nevisco","Frigelo","Branquim","Geadinho","Cristagel","Polarim","Nevon","Brisagel","Granizo","Gelágio","Glacialto","Cryonix","Nevastro","Zeroar"],
     "emojis": ["❄️","⛄","🧊","🐧","🛷","🥶","🐻‍❄️","🏔️","🦣","🧤","🎿","⛸️","🍧","🐺","☃️"]},
    {"t": "trovão", "c": 0xe4c243, "mat": "Faísca",  "hpMod": -2, "atkMod": 2,
     "names": ["Raiolho","Choquito","Faíscudo","Pulsarim","Estaleco","Voltino","Troval","Neonchoque","Descargor","Eletrux","Tempestral","Raiotron","Fulminax","Arcozapp","Stormvolt"],
     "emojis": ["⚡","🔋","🐹","💡","📻","💾","🦘","🌩️","📀","🔌","🚨","🪫","📱","🗜️","🥁"]},
    {"t": "sombra", "c": 0x5960b8, "mat": "Essência","hpMod": -1, "atkMod": 3,
     "names": ["Breuzinho","Sombralho","Ocultim","Vultito","Umbralim","Nocturo","Escurix","Véunegra","Tenebris","Mistumbrio","Abysmino","Sombrakar","Vaziurno","Crepux","Noxthar"],
     "emojis": ["🌑","🦇","🐈‍⬛","🕳️","🕸️","🎩","♠️","🌘","🕷️","🖤","🌒","🥷","🌌","👁️","🪦"]},
    {"t": "cristal","c": 0x73cfe0, "mat": "Gema",    "hpMod": 1,  "atkMod": 2,
     "names": ["Facetim","Brilhux","Vidrilho","Lúmino","Gemarim","Prismal","Reflexor","Cintilux","Quartzel","Luzcrist","Diamar","Shinério","Prismon","Glamyte","Luxórion"],
     "emojis": ["💎","🪩","🔷","💠","🔮","💍","👑","🪞","🧂","🔹","🧿","🪙","🪬","❇️","✴️"]},
    {"t": "veneno", "c": 0x8e4ac2, "mat": "Toxina",  "hpMod": 2,  "atkMod": 1,
     "names": ["Toxito","Peçonhudo","Bafumeio","Ácidim","Nocivo","Vaporoz","Miasmelo","Corrosix","Venomix","Biletor","Toxibras","Podrino","Morbax","Peçonrex","Nexovina"],
     "emojis": ["☠️","🧪","🐍","🦂","🪱","🦠","🐌","🦨","🦎","🧫","☣️","🦟","🗑️","🧟","🪰"]},
    {"t": "som",    "c": 0xff9ff3, "mat": "Vibração","hpMod": -3, "atkMod": 4,
     "names": ["Notinha","Apito","Vibrax","Ecoante","Resson","Sônico","Ressonix","Batida","Melódico","Grito","Harmon","Bumbo","Agudo","Sinfon","Ópera"],
     "emojis": ["🎵","🔔","📣","🎼","🎷","🎸","🎹","🎺","🎻","🎙️","📻","🔉","🔈","🔊","📯"]},
    {"t": "tempo",  "c": 0x54a0ff, "mat": "Engrenagem","hpMod": 5,"atkMod": 2,
     "names": ["Tique","Toque","Ampulim","Relogito","Sécullus","Erax","Momentum","Pendor","Eterno","Cronix","Antigo","Futuro","Paradoxo","Zênite","Infinito"],
     "emojis": ["⌛","⏳","⌚","⏰","🕰️","📅","📆","🗓️","🌀","⚙️","🔙","🔜","♾️","🗝️","🏛️"]},
    {"t": "luz",    "c": 0xfeca57, "mat": "Fóton",   "hpMod": 2,  "atkMod": 1,
     "names": ["Faisquinha","Raio","Lume","Solaris","Claro","Aura","Relampo","Radiante","Glorioso","Cintilo","Ilumin","Candela","Facho","Prisma","Divino"],
     "emojis": ["☀️","⭐","🌟","✨","🔦","💡","🕯️","🌕","🌅","🌤️","🎥","📸","🎐","🔆","👼"]},
    {"t": "cosmos", "c": 0x2e86de, "mat": "Poeira Estelar","hpMod": 0,"atkMod": 6,
     "names": ["Nebulino","Cometa","Orbital","Galaxico","Quasar","Pulzar","Sideral","Vácuo","Astro","Luneto","Solfar","Planeta","Constela","Zenit","Universo"],
     "emojis": ["🌌","🪐","☄️","🛰️","🛸","🌑","🌘","🔭","🪷","🌠","🚀","👽","⚫","🟣","🟠"]},
    {"t": "metal",  "c": 0x95a5a6, "mat": "Lingote", "hpMod": 10, "atkMod": 0,
     "names": ["Prequinho","Latão","Blindado","Chapa","Mecano","Tanque","Escudo","Lâmina","Broca","Titânio","Robusto","Cromo","Bigorna","Colosso","Muralha"],
     "emojis": ["🔩","⚙️","⛓️","🗡️","🛡️","⚓","⚔️","⚒️","🛠️","⛏️","🚜","🏗️","🏢","🚄","🦾"]},
    {"t": "fantasma","c":0x9b59b6,"mat":"Ectoplasma","hpMod":-2,"atkMod":3,
     "names":["Fantasminha","Vaporzinho","Espectrim","Sombraluz","Aparião","Poltergeist","Etéreo","Wraitho","Spectrax","Bansheiro","Hauntelo","Phantomix","Espírito","Revenant","Necrovolt"],
     "emojis":["👻","🫥","💨","🌫️","👁️","🪦","🪬","🕸️","🌒","🦴","💀","🪄","🌑","⚰️","🔮"]},
    {"t":"dragão", "c":0xc0392b, "mat":"Escama",  "hpMod":6, "atkMod":4,
     "names":["Drakoninho","Wyvernito","Serpelux","Ryudrak","Winguim","Dracozar","Fyrrex","Drakonis","Ignithorn","Scalethar","Clawmere","Draklord","Vyraxion","Nidragor","Dragonyx"],
     "emojis":["🐉","🦕","🦖","🐲","🔥","🌋","⚔️","🛡️","🌪️","🌊","⚡","❄️","☄️","💫","👑"]},
    {"t":"fada",   "c":0xff6eb4, "mat":"Pó de Fada","hpMod":0, "atkMod":2,
     "names":["Fadinhas","Encantura","Pixelim","Glitterix","Sparkelo","Lumiríx","Feerinha","Dazzlim","Wisping","Shimmerix","Blossomix","Glowette","Twinkling","Sprinklex","Celestira"],
     "emojis":["🧚","🌸","✨","🦋","🌺","🎀","💗","🌈","🪷","🌠","💖","🫧","🪻","🎆","🔮"]},
    {"t":"psíquico","c":0x8e44ad,"mat":"Fragmento Psíquico","hpMod":-1,"atkMod":4,
     "names":["Psiquim","Mentalis","Telepatix","Alucinex","Premonix","Clairix","Psivolt","Mindmere","Intuidor","Kinesis","Espatix","Telekin","Cognithor","Visionix","Omegamind"],
     "emojis":["🔮","🧠","👁️","🌀","💜","🪬","⭐","🌊","🎭","💭","🫀","🔵","🧿","💫","🌌"]},
    {"t":"luta",   "c":0xe74c3c, "mat":"Fita de Treino","hpMod":2,"atkMod":5,
     "names":["Soqinho","Pontapelux","Upperim","Jabhero","Kombatik","Rushador","Strikelux","Grapplino","Punchix","Kicker","Kickzilla","Sluggerax","Brutegor","Ironknuckle","Ultimapunch"],
     "emojis":["👊","🥊","🥋","🤼","💪","🦵","🦶","⚡","🔥","🏋️","🤺","🥷","🏆","⚔️","💢"]},
    {"t":"inseto", "c":0x27ae60, "mat":"Casulo", "hpMod":1, "atkMod":2,
     "names":["Lagartixa","Besourelo","Borbolim","Formigor","Escaravim","Gafanhotix","Larviço","Cocônix","Chrysalis","Antleon","Scarabeux","Beetlord","Mothwing","Mantidor","Hexapod"],
     "emojis":["🐛","🦋","🐝","🐜","🦗","🕷️","🐞","🪲","🪳","🦟","🦠","🌿","🍃","🌱","🪸"]},
    {"t":"néon",   "c":0x00ffcc, "mat":"Plasma Néon","hpMod":-3,"atkMod":5,
     "names":["Néonix","Glitchim","Ciberlink","Pixelglow","Synthrix","Databit","Wireframe","Glowbyte","Circuitex","Lagzero","Flashnet","Hyperglow","Matrixter","Virtuelux","Cybercore"],
     "emojis":["🟢","💚","🔋","📡","💻","🖥️","📺","🎮","🕹️","🔌","📱","💾","🛜","🔆","⚡"]},
    {"t":"nuclear","c":0xf39c12, "mat":"Urânio","hpMod":0, "atkMod":6,
     "names":["Radiino","Atomillo","Nucléix","Fusionix","Fissurex","Radiotor","Halflifo","Decayix","Isótopo","Falloutix","Gammaray","Reatorix","Critimass","Meltorex","Nucleagor"],
     "emojis":["☢️","⚗️","💥","🔬","🧬","⚡","🌡️","🧪","💣","🔥","🌋","☄️","💫","🌀","🔶"]},
    {"t":"espírito","c":0x1abc9c,"mat":"Essência Espiritual","hpMod":3,"atkMod":2,
     "names":["Alminha","Kamirix","Shintorix","Ancestrix","Espirix","Soulix","Totemix","Orixim","Blessor","Holyrim","Sacredix","Mantra","Divinix","Transcend","Enlighten"],
     "emojis":["🙏","⛩️","🎋","🪬","🔯","☯️","🕉️","✡️","🔱","⚜️","🪷","🌸","🌟","💫","👼"]},
    {"t":"mecânico","c":0x7f8c8d,"mat":"Peça Mecânica","hpMod":8,"atkMod":1,
     "names":["Robotinho","Automec","Dronix","Cogwheelx","Steamrix","Pistonix","Valvulor","Turbinix","Transmitor","Gearborg","Motorax","Clockwork","Steamborg","Technogor","Mekavolt"],
     "emojis":["🤖","⚙️","🔧","🔩","🛠️","🚜","🏗️","🚂","✈️","🚀","🛸","🦾","🦿","🧲","💡"]},
    {"t":"ventos", "c":0x3498db, "mat":"Redemoinho","hpMod":-2,"atkMod":3,
     "names":["Brisim","Tufarix","Zonalix","Cyclonix","Galerix","Tempestix","Twistix","Squallo","Zephyrion","Anemix","Typhonex","Sirocco","Mistral","Boreamix","Zondragor"],
     "emojis":["🌪️","🌀","💨","🌬️","🌊","⛵","🪁","🎑","🎐","☁️","🌩️","⛈️","🌧️","🌦️","🪂"]},
    {"t":"magma",  "c":0xe67e22, "mat":"Lava Solidificada","hpMod":5,"atkMod":3,
     "names":["Lavinha","Magmarim","Ignerix","Pyroclax","Emberlux","Calderon","Scorcherix","Infernix","Lavabeast","Moltenix","Cinder","Eruption","Volcanus","Firestorm","Magmarex"],
     "emojis":["🌋","🔥","💥","🧱","🏔️","☄️","🫧","🌡️","⚗️","🔶","🟠","🟤","🫁","🪨","⛏️"]},
    {"t":"arcano", "c":0x9b30ff, "mat":"Cristal Arcano","hpMod":1,"atkMod":5,
     "names":["Arcalix","Rúnico","Spellrix","Glamorix","Hexamix","Grimora","Occultix","Witchix","Conjuror","Runeborn","Eldritch","Sorceron","Arcanix","Mystara","Sorceling"],
     "emojis":["🪄","✨","🔮","📖","🌙","⭐","💜","🎩","🃏","🪬","📜","🔯","🌀","💫","🧿"]},
]

# Chart de tipos — vantagens dão x1.5, desvantagens x0.67, neutro x1.0
TYPE_CHART = {
    "fogo":     {"adv": ["gelo","planta","inseto","metal"],  "dis": ["terra","água","magma"]},
    "água":     {"adv": ["fogo","gelo","magma"],             "dis": ["planta","trovão"]},
    "planta":   {"adv": ["água","terra"],                    "dis": ["fogo","veneno","gelo"]},
    "terra":    {"adv": ["trovão","fogo","veneno"],          "dis": ["planta","cristal"]},
    "ar":       {"adv": ["veneno","sombra","inseto"],        "dis": ["cosmos","metal"]},
    "gelo":     {"adv": ["luz","veneno","planta"],           "dis": ["fogo","água"]},
    "trovão":   {"adv": ["água","som","mecânico"],           "dis": ["terra","sombra"]},
    "sombra":   {"adv": ["cosmos","trovão","psíquico"],      "dis": ["luz","ar","fada"]},
    "cristal":  {"adv": ["terra","tempo"],                   "dis": ["som"]},
    "veneno":   {"adv": ["planta","metal"],                  "dis": ["ar","gelo"]},
    "som":      {"adv": ["cristal","metal"],                 "dis": ["cosmos","trovão"]},
    "luz":      {"adv": ["tempo","sombra","fantasma"],       "dis": ["metal","gelo"]},
    "tempo":    {"adv": ["cosmos","trovão"],                 "dis": ["luz","cristal"]},
    "metal":    {"adv": ["luz","ar","fada"],                 "dis": ["som","veneno","fogo"]},
    "cosmos":   {"adv": ["ar","som"],                        "dis": ["tempo","sombra"]},
    "fantasma": {"adv": ["psíquico","luta"],                 "dis": ["arcano","metal"]},
    "dragão":   {"adv": ["metal","arcano"],                  "dis": ["gelo","fada"]},
    "fada":     {"adv": ["dragão","luta","sombra"],          "dis": ["veneno","metal"]},
    "psíquico": {"adv": ["luta","fantasma","veneno"],        "dis": ["sombra","inseto"]},
    "luta":     {"adv": ["metal","gelo","sombra"],           "dis": ["fada","psíquico"]},
    "inseto":   {"adv": ["psíquico","planta"],               "dis": ["fogo","ar"]},
    "néon":     {"adv": ["mecânico","sombra"],               "dis": ["nuclear","arcano"]},
    "nuclear":  {"adv": ["néon","inseto"],                   "dis": ["espírito","terra"]},
    "espírito": {"adv": ["nuclear","sombra"],                "dis": ["dragão","metal"]},
    "mecânico": {"adv": ["ar","gelo"],                       "dis": ["néon","nuclear"]},
    "ventos":   {"adv": ["inseto","fogo"],                   "dis": ["metal","terra"]},
    "magma":    {"adv": ["gelo","terra","metal"],            "dis": ["água","ventos"]},
    "arcano":   {"adv": ["fantasma","cosmos"],               "dis": ["dragão","sombra"]},
    # Tipos especiais de bosses e divinos
    "molestador":{"adv": ["fofa"],                           "dis": ["fofa"]},
    "fofa":      {"adv": ["molestador"],                     "dis": ["molestador"]},
    "oxigénio":  {"adv": ["caos"],                           "dis": ["absoluto"]},
    "caos":      {"adv": ["absoluto"],                       "dis": ["oxigénio"]},
    "absoluto":  {"adv": ["oxigénio"],                       "dis": ["caos"]},
    "deus":      {"adv": [],                                 "dis": []},
    "???":       {"adv": [],                                 "dis": []},
}


def build_mons() -> list[dict]:
    """Gera a lista completa de monstros a partir de TYPE_DEFS + RARITY_PLAN."""
    mons = []
    for td in TYPE_DEFS:
        for i, plan in enumerate(RARITY_PLAN):
            if i >= len(td["names"]):
                break
            mons.append({
                "n":    td["names"][i],
                "e":    td["emojis"][i],
                "t":    td["t"],
                "c":    td["c"],
                "catch": plan["catch"],
                "hp":   plan["hp"] + td["hpMod"],
                "atk":  plan["atk"] + td["atkMod"],
                "mat":  {"n": f"{td['mat']} {td['t']}", "v": plan["mat"]},
                "rare": plan["rare"],
            })
    # Monstros DIVINOS (usados em eventos, ex.: Nico é triggered pelo OXIGÉNIO)
    mons.extend([
        {"n": "OXIGÉNIO",    "e": "💨", "t": "oxigénio", "c": 0xaae0ff, "catch": 0.05,
         "hp": 95, "atk": 88, "mat": {"n": "O₂", "v": 130}, "rare": "divino"},
        {"n": "Ciclone-Rei", "e": "🌀", "t": "caos",     "c": 0x6b44d9, "catch": 0.06,
         "hp": 122, "atk": 28, "mat": {"n": "Olho do Caos", "v": 120}, "rare": "divino"},
        {"n": "DEUS-DRAGÃO", "e": "🐲", "t": "absoluto", "c": 0xffd700, "catch": 0.06,
         "hp": 165, "atk": 33, "mat": {"n": "Alma do Dragão", "v": 160}, "rare": "divino"},
    ])
    return mons


MONS = build_mons()
MON_INDEX = {m["n"]: m for m in MONS}


# ══════════════════════════════════════════════════════════════
# BOSSES
# ══════════════════════════════════════════════════════════════

FINAL_BOSS_PHASE2_IMAGE = "https://imgur.com/AdvDrEa.png"

BOSSES = [
    {"n": "Rei das Chamas",      "t": "fogo",    "e": "👹", "hp": 1000, "atk": 35, "reward": 500,
     "title": "Senhor do Inferno",      "mats": [{"n": "Coroa de Fogo", "v": 200}]},
    {"n": "Titã dos Mares",      "t": "água",    "e": "🐋", "hp": 1400, "atk": 30, "reward": 600,
     "title": "Leviatã Ancestral",      "mats": [{"n": "Escudo Abissal", "v": 200}]},
    {"n": "Lorde das Sombras",   "t": "sombra",  "e": "🌑", "hp": 1200, "atk": 40, "reward": 700,
     "title": "Devorador de Almas",     "mats": [{"n": "Cristal Negro", "v": 200}]},
    {"n": "Maestro do Caos",     "t": "som",     "e": "🎻", "hp": 1900, "atk": 55, "reward": 1600,
     "title": "O Regente do Silêncio",  "mats": [{"n": "Vibração", "v": 400}]},
    {"n": "Guardião das Eras",   "t": "tempo",   "e": "🕰️", "hp": 2400, "atk": 40, "reward": 1900,
     "title": "Aquele que Parou o Tempo","mats": [{"n": "Engrenagem", "v": 450}]},
    {"n": "Arcanjo Solar",       "t": "luz",     "e": "👼", "hp": 2100, "atk": 50, "reward": 2500,
     "title": "O Esplendor do Meio-Dia","mats": [{"n": "Fóton", "v": 500}]},
    {"n": "Vazio Estelar",       "t": "cosmos",  "e": "🕳️", "hp": 2600, "atk": 65, "reward": 3000,
     "title": "O Devorador de Galáxias","mats": [{"n": "Poeira Estelar", "v": 550}]},
    {"n": "Leviatã de Ferro",    "t": "metal",   "e": "⛓️", "hp": 3800, "atk": 35, "reward": 2200,
     "title": "A Fortaleza Móvel",      "mats": [{"n": "Lingote", "v": 600}]},
    {"n": "Entidade Verdejante", "t": "planta",  "e": "🌳", "hp": 2200, "atk": 38, "reward": 1400,
     "title": "O Coração da Floresta",  "mats": [{"n": "Folha Ancestral", "v": 350}]},
    {"n": "Colosso da Montanha", "t": "terra",   "e": "🗿", "hp": 3500, "atk": 42, "reward": 1600,
     "title": "O Guardião da Rocha Eterna","mats":[{"n": "Pedra Titânica", "v": 400}]},
    {"n": "Senhor dos Vendavais","t": "ar",      "e": "🌪️", "hp": 1900, "atk": 48, "reward": 1500,
     "title": "A Fúria do Céu",         "mats": [{"n": "Pluma da Tempestade", "v": 380}]},
    {"n": "Tirano Glacial",      "t": "gelo",    "e": "❄️", "hp": 2800, "atk": 36, "reward": 1700,
     "title": "O Inverno Eterno",       "mats": [{"n": "Cristal Gélido", "v": 420}]},
    {"n": "Deus da Tempestade",  "t": "trovão",  "e": "⚡", "hp": 2100, "atk": 52, "reward": 1800,
     "title": "O Arauto dos Céus",      "mats": [{"n": "Faísca Divina", "v": 450}]},
    {"n": "Arquiteto Cristalino","t": "cristal", "e": "💎", "hp": 2600, "atk": 45, "reward": 1900,
     "title": "O Mestre das Gemas",     "mats": [{"n": "Gema Pura", "v": 480}]},
    {"n": "Mente Suprema",       "t": "psíquico","e": "🧠", "hp": 1800, "atk": 55, "reward": 2000,
     "title": "O Oráculo Cósmico",      "mats": [{"n": "Fragmento Psíquico", "v": 500}]},
    {"n": "Campeão Indomável",   "t": "luta",    "e": "👊", "hp": 3000, "atk": 50, "reward": 1600,
     "title": "O Punho Inquebrável",    "mats": [{"n": "Fita de Treino Lendária", "v": 400}]},
    {"n": "Imperador dos Enxames","t": "inseto", "e": "🐝", "hp": 1700, "atk": 40, "reward": 1400,
     "title": "A Colmeia Viva",         "mats": [{"n": "Casulo Real", "v": 350}]},
    {"n": "Soberano de Néon",    "t": "néon",    "e": "🟢", "hp": 2000, "atk": 54, "reward": 2000,
     "title": "A Grade Digital",        "mats": [{"n": "Plasma Néon", "v": 500}]},
    {"n": "Entidade Radioativa", "t": "nuclear", "e": "☢️", "hp": 3200, "atk": 60, "reward": 2200,
     "title": "O Núcleo Instável",      "mats": [{"n": "Urânio Puro", "v": 550}]},
    {"n": "Ancestral Sagrado",   "t": "espírito","e": "🙏", "hp": 2300, "atk": 44, "reward": 1800,
     "title": "A Voz dos Antigos",      "mats": [{"n": "Essência Espiritual", "v": 450}]},
    {"n": "Engenheiro do Caos",  "t": "mecânico","e": "🤖", "hp": 4000, "atk": 46, "reward": 2100,
     "title": "A Máquina Perfeita",     "mats": [{"n": "Peça Mecânica Lendária", "v": 520}]},
    {"n": "Senhor do Magma",     "t": "magma",   "e": "🌋", "hp": 3600, "atk": 48, "reward": 2000,
     "title": "O Coração da Terra",     "mats": [{"n": "Lava Solidificada", "v": 500}]},
    {"n": "Mestre Arcano",       "t": "arcano",  "e": "🔮", "hp": 2500, "atk": 56, "reward": 2300,
     "title": "O Guardião dos Segredos","mats": [{"n": "Cristal Arcano", "v": 600}]},
    {"n": "Espectro do Vazio",   "t": "fantasma","e": "👻", "hp": 1500, "atk": 58, "reward": 1900,
     "title": "A Alma Perdida",         "mats": [{"n": "Ectoplasma", "v": 480}]},
    {"n": "Dragão Primordial",   "t": "dragão",  "e": "🐉", "hp": 5000, "atk": 70, "reward": 3000,
     "title": "O Primeiro dos Dragões", "mats": [{"n": "Escama Ancestral", "v": 800}]},
    {"n": "Rainha das Fadas",    "t": "fada",    "e": "🧚", "hp": 1600, "atk": 42, "reward": 1700,
     "title": "A Protetora dos Reinos", "mats": [{"n": "Pó de Fada", "v": 420}]},
    {"n": "Dragão do Apocalipse","t": "ar",      "e": "🐲", "hp": 4000, "atk": 45, "reward": 900,
     "title": "Fim dos Tempos",         "mats": [{"n": "Dente do Apocalipse", "v": 200}]},
    {"n": "DEUS DO CAOS",        "t": "veneno",  "e": "💀", "hp": 6666, "atk": 666,"reward": 1500,
     "title": "O Inominável",           "mats": [{"n": "Fragmento Divino", "v": 200}]},
    # Bosses especiais
    {"n": "Void King",           "t": "cristal", "e": "👑", "hp": 5800, "atk": 1000,"reward": 1200,
     "title": "Rei do Vazio",           "mats": [{"n": "Coroa do Vazio", "v": 2000}],
     "special": "master_only"},
    {"n": "murilo",              "t": "molestador","e":"👨‍🦽","hp":3000,"atk":150,"reward":5000,
     "title": "O Inominável do Caos",   "mats": [{"n": "esperma", "v": 999}],
     "special": "murilo"},
    {"n": "Nico",                "t": "fofa",   "e": "🐈", "hp": 1500, "atk": 150, "reward": 5000,
     "title": "A Destruidora de Mundos","mats": [{"n": "Pelo Cósmico", "v": 999}],
     "special": "nico"},
    # BOSS FINAL — só se desbloqueia quando a Pokédex está completa
    {"n": "???",                 "t": "???",    "e": "❓", "hp": 999999, "atk": 12000, "reward": 10000,
     "title": "???",                    "mats": [{"n": "Essência Divina", "v": 1000}],
     "special": "final_boss"},
]

BOSS_INDEX = {b["n"]: b for b in BOSSES}


# ══════════════════════════════════════════════════════════════
# LOJA
# ══════════════════════════════════════════════════════════════

SHOP_ITEMS = [
    {"id": "superball",  "n": "Super Ball",   "e": "🔵", "price": 40,  "desc": "+15% captura (próximo lançamento)"},
    {"id": "ultraball",  "n": "Ultra Ball",   "e": "🟣", "price": 90,  "desc": "+25% captura (próximo lançamento)"},
    {"id": "masterball", "n": "Master Ball",  "e": "⭐", "price": 220, "desc": "Captura garantida (máx 1)"},
    {"id": "potion",     "n": "Poção",        "e": "🧪", "price": 25,  "desc": "Cura 60 HP"},
    {"id": "superpotion","n": "Super Poção",  "e": "💚", "price": 70,  "desc": "Cura 150 HP"},
    {"id": "megapotion", "n": "Mega Poção",   "e": "💊", "price": 120, "desc": "Cura 50% do HP máximo"},
    {"id": "hyperpotion","n": "Hyper Poção",  "e": "✨", "price": 220, "desc": "Cura 100% do HP máximo"},
    {"id": "revive",     "n": "Revive",       "e": "❤️","price": 120, "desc": "Reanima com 75% HP"},
    {"id": "maxrevive",  "n": "Max Revive",   "e": "💖", "price": 280, "desc": "Reanima com HP total"},
    {"id": "protein",    "n": "Proteína",     "e": "💪", "price": 95,  "desc": "+10 ATK permanente"},
    {"id": "heartseed",  "n": "Semente Vital","e": "🌱", "price": 95,  "desc": "+10 HP permanente"},
    {"id": "tiercore",   "n": "Tier Core",    "e": "🔺", "price": 500, "desc": "+1 Tier no monstro ativo"},
    {"id": "balls5",     "n": "Pack Balls",   "e": "🔮", "price": 35,  "desc": "+5 Monster Balls"},
    {"id": "shield",     "n": "Escudo Mágico","e": "🛡️","price": 80,  "desc": "Absorve 40% do próximo dano (boss)"},
    {"id": "xatk",       "n": "X-Ataque",     "e": "💢", "price": 20,  "desc": "+60% dano no próximo ataque"},
    {"id": "neoncage",   "n": "Gaiola Néon",  "e": "🟩", "price": 160, "desc": "+35% captura em Néon/Mecânico/Nuclear"},
]

SHOP_INDEX = {s["id"]: s for s in SHOP_ITEMS}


# ══════════════════════════════════════════════════════════════
# PERSISTÊNCIA (save/load por utilizador)
# ══════════════════════════════════════════════════════════════

def save_path(uid: int) -> str:
    return os.path.join(SAVES_DIR, f"{uid}.json")


def default_save() -> dict:
    return {
        # Recursos
        "gold": 50, "balls": 5, "masterball": 0,
        "items": {}, "materials": {},
        # Colecção
        "caught": [], "bossDefeated": [],
        "team": [], "box": [], "nextMonId": 1, "activeMonId": None,
        # Estado de batalha (selvagem)
        "inBattle": False, "wild": None, "wildHp": 0, "wildMaxHp": 0,
        # Estado de batalha (boss)
        "inBossBattle": False, "boss": None,
        "bossHp": 0, "bossMaxHp": 0,
        "playerHp": 0, "playerMaxHp": 0, "playerMon": None,
        "defending": False, "bossShield": 0,
        "bossTurn": 0, "bossCharging": False, "bossBallCD": 0,
        "lowHpWarned": False,
        # Boss pendente (ex.: Nico após evento)
        "pendingBoss": None,
        # Boss final (0=inativo, 1=??? 2=Leonking)
        "finalBossPhase": 0,
        # Evento secreto: Nico (3 poções no OXIGÉNIO)
        "nicoPotions": 0,
        # Buffs temporários
        "xatkActive": False,
        # Progresso
        "rebirthCount": 0, "battles": 0,
    }


def load_save(uid: int) -> dict:
    path = save_path(uid)
    if not os.path.exists(path):
        return default_save()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Merge com defaults para garantir novas chaves após updates
        base = default_save()
        for k, v in base.items():
            if k not in data:
                data[k] = v
        return data
    except Exception:
        return default_save()


def write_save(uid: int, data: dict) -> None:
    path = save_path(uid)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[bot] Erro ao guardar {uid}: {e}")


# ══════════════════════════════════════════════════════════════
# HELPERS DE APRESENTAÇÃO (HUD)
# ══════════════════════════════════════════════════════════════

def fmt_num(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def tier_stars(tier: int) -> str:
    return "⭐" * max(1, min(5, int(tier))) + "☆" * max(0, 5 - int(tier))


def hp_bar(ratio: float, length: int = 14) -> str:
    """Barra de HP em blocos unicode."""
    ratio = max(0.0, min(1.0, ratio))
    filled = int(round(ratio * length))
    if ratio > 0.5:
        block = "█"
    elif ratio > 0.25:
        block = "▓"
    else:
        block = "▒"
    return block * filled + "░" * (length - filled)


def rarity_color(r: str) -> int:
    return RARITY_COLOR.get(r, 0x888888)


def type_badge(t: str) -> str:
    icons = {
        "fogo": "🔥", "água": "💧", "planta": "🌿", "terra": "🪨", "ar": "🌬️",
        "gelo": "❄️", "trovão": "⚡", "sombra": "🌑", "cristal": "💎", "veneno": "☠️",
        "som": "🎵", "tempo": "⏳", "luz": "☀️", "cosmos": "🌌", "metal": "⚙️",
        "fantasma": "👻", "dragão": "🐉", "fada": "🧚", "psíquico": "🔮", "luta": "👊",
        "inseto": "🐛", "néon": "🟢", "nuclear": "☢️", "espírito": "🙏",
        "mecânico": "🤖", "ventos": "🌪️", "magma": "🌋", "arcano": "🪄",
        "molestador": "👨‍🦽", "fofa": "🐈", "oxigénio": "💨", "caos": "🌀",
        "absoluto": "🐲", "deus": "👑", "???": "❓",
    }
    return f"{icons.get(t, '❔')} **{t}**"


# ══════════════════════════════════════════════════════════════
# LÓGICA DE MONSTROS (stats, XP, tipo)
# ══════════════════════════════════════════════════════════════

def get_type_mult(atk_type: str, def_type: str) -> float:
    chart = TYPE_CHART.get(atk_type, {})
    if def_type in chart.get("adv", []):
        return 1.5
    if def_type in chart.get("dis", []):
        return 0.67
    return 1.0


def refresh_mon_stats(mon: dict) -> None:
    """Recalcula maxHp/atkStat com base em level, tier e boosts."""
    sp = MON_INDEX.get(mon.get("species", ""), {})
    base_hp = mon.get("baseHp", sp.get("hp", 20))
    base_atk = mon.get("baseAtk", sp.get("atk", 5))
    level = mon.get("level", 1)
    tier = mon.get("tier", 1)
    hp_boost = mon.get("hpBoost", 0)
    atk_boost = mon.get("atkBoost", 0)

    tier_mult_hp = 1.0 + 0.15 * (tier - 1)
    tier_mult_atk = 1.0 + 0.10 * (tier - 1)

    new_max = int(round((base_hp + hp_boost) * (1 + 0.08 * (level - 1)) * tier_mult_hp))
    new_atk = int(round((base_atk + atk_boost) * (1 + 0.06 * (level - 1)) * tier_mult_atk))
    mon["maxHp"] = max(1, new_max)
    mon["atkStat"] = max(1, new_atk)
    mon["hp"] = min(mon.get("hp", mon["maxHp"]), mon["maxHp"])


def gain_xp(mon: dict, amount: int) -> int:
    """Adiciona XP e processa level-ups. Devolve nr de levels ganhos."""
    mon.setdefault("xp", 0)
    mon.setdefault("level", 1)
    mon["xp"] += amount
    levels = 0
    while mon["xp"] >= mon["level"] * 20:
        mon["xp"] -= mon["level"] * 20
        mon["level"] += 1
        levels += 1
        # Tier-up a cada 10 níveis, máx 5
        if mon["level"] % 10 == 0 and mon.get("tier", 1) < 5:
            mon["tier"] += 1
    refresh_mon_stats(mon)
    return levels


def create_mon_from_species(sp: dict, next_id: int) -> dict:
    """Cria instância nova de monstro a partir da espécie."""
    mon = {
        "id": next_id,
        "species": sp["n"], "n": sp["n"], "e": sp["e"],
        "t": sp["t"], "c": sp.get("c", 0x888888),
        "level": 1, "tier": 1, "xp": 0,
        "baseHp": sp["hp"], "baseAtk": sp["atk"],
        "hpBoost": 0, "atkBoost": 0,
        "alive": True, "isBoss": False,
    }
    refresh_mon_stats(mon)
    mon["hp"] = mon["maxHp"]
    return mon


def get_active_mon(data: dict) -> Optional[dict]:
    aid = data.get("activeMonId")
    team = data.get("team", [])
    if aid:
        for m in team:
            if m.get("id") == aid:
                return m
    return team[0] if team else None


# ══════════════════════════════════════════════════════════════
# CAPTURA / CHANCE
# ══════════════════════════════════════════════════════════════

def get_catch_chance(wild: dict, data: dict, ball: str = "normal") -> float:
    base = wild.get("catch", 0.5)
    # HP baixo dá bónus (até +20%)
    wild_hp = data.get("wildHp", wild.get("hp", 1))
    wild_max = data.get("wildMaxHp", wild.get("hp", 1))
    hp_ratio = wild_hp / max(1, wild_max)
    hp_bonus = (1 - hp_ratio) * 0.2
    # Balls diferentes
    ball_bonus = {"normal": 0.0, "super": 0.15, "ultra": 0.25}[ball]
    # Gaiola néon para tipos tech
    cage_bonus = 0.0
    if data.get("items", {}).get("neoncage", 0) > 0 and wild.get("t") in ("néon", "mecânico", "nuclear"):
        cage_bonus = 0.35
    return max(0.02, min(0.98, base + hp_bonus + ball_bonus + cage_bonus))


def spawn_wild(data: dict) -> dict:
    """Escolhe um monstro selvagem aleatório (não inclui divinos a 100%)."""
    # Divinos só 1% chance
    if random.random() < 0.01:
        divinos = [m for m in MONS if m["rare"] == "divino"]
        if divinos:
            return random.choice(divinos)
    # Raridade ponderada
    weights = {
        "comum": 50, "incomum": 25, "raro": 15, "épico": 6,
        "lendário": 3, "mítico": 1, "divino": 0,
    }
    pool = [(m, weights.get(m["rare"], 1)) for m in MONS if m["rare"] != "divino"]
    mons, ws = zip(*pool)
    return random.choices(mons, weights=ws, k=1)[0]


# ══════════════════════════════════════════════════════════════
# BOSS: ESCALA, POKÉDEX, EVENTO NICO
# ══════════════════════════════════════════════════════════════

def compute_boss_scale(data: dict) -> float:
    """Escala o boss baseada na força média da equipa (idêntico ao HTML)."""
    team = data.get("team", [])
    if not team:
        return 1.0
    for m in team:
        refresh_mon_stats(m)
    avg_tier = sum(m.get("tier", 1) for m in team) / len(team)
    avg_hp = sum(m.get("maxHp", 20) for m in team) / len(team)
    avg_atk = sum(m.get("atkStat", 5) for m in team) / len(team)
    tier_bonus = (avg_tier - 1) * 0.08
    hp_bonus = min(0.6, avg_hp / 250.0)
    atk_bonus = min(0.6, avg_atk / 50.0)
    return 1.0 + tier_bonus + hp_bonus + atk_bonus


def pokedex_total() -> int:
    return len(MONS) + len([b for b in BOSSES if b.get("special") != "final_boss"])


def pokedex_progress(data: dict) -> int:
    caught = set(data.get("caught", []))
    bosses = [b for b in data.get("bossDefeated", []) if b not in ("???", "Leonking")]
    return len(caught) + len(bosses)


def is_pokedex_complete(data: dict) -> bool:
    return pokedex_progress(data) >= pokedex_total()


def start_final_boss_phase2(data: dict) -> None:
    """Transição ??? → Leonking."""
    b = data.get("boss") or {}
    data["finalBossPhase"] = 2
    new_atk = int(round(b.get("atk", 12000) * 1.45))
    new_reward = int(round(b.get("reward", 10000) * 1.5))
    new_max = max(6500000, int(round(data.get("bossMaxHp", b.get("hp", 999999)) * 0.72)))
    data["boss"] = {
        "n": "Leonking", "e": "🐐", "t": "deus",
        "title": "O Rei dos Deuses",
        "hp": new_max, "atk": new_atk, "reward": new_reward,
        "mats": b.get("mats", [{"n": "Essência Divina", "v": 1000}]),
        "special": "final_boss", "phase": 2,
        "image": FINAL_BOSS_PHASE2_IMAGE,
    }
    data["bossMaxHp"] = new_max
    data["bossHp"] = new_max
    # Cura 30% do HP ao jogador
    data["playerHp"] = min(
        data.get("playerMaxHp", 100),
        data.get("playerHp", 0) + int(round(data.get("playerMaxHp", 100) * 0.3))
    )
    data["defending"] = False
    data["bossShield"] = 0
    data["bossCharging"] = False
    data["bossTurn"] = 0
    data["bossBallCD"] = 0
    data["lowHpWarned"] = False


# ══════════════════════════════════════════════════════════════
# EMBEDS (HUD)
# ══════════════════════════════════════════════════════════════

def embed_profile(user: discord.abc.User, data: dict) -> discord.Embed:
    team = data.get("team", [])
    box = data.get("box", [])
    caught = data.get("caught", [])
    bosses = data.get("bossDefeated", [])
    progress = pokedex_progress(data)
    total = pokedex_total()
    pct = int(progress / total * 100) if total else 0

    embed = discord.Embed(
        title=f"👤 Perfil de {user.display_name}",
        description=f"**Monster Hunter RPG** — Rebirth #{data.get('rebirthCount', 0)}",
        color=0xffd700,
    )
    embed.set_thumbnail(url=user.display_avatar.url)

    embed.add_field(name="💰 Ouro", value=fmt_num(data.get("gold", 0)), inline=True)
    embed.add_field(name="🔮 Balls", value=str(data.get("balls", 0)), inline=True)
    embed.add_field(name="⭐ Master", value=str(data.get("masterball", 0)), inline=True)

    embed.add_field(name="🐾 Equipa", value=f"{len(team)}/6", inline=True)
    embed.add_field(name="📦 Box", value=str(len(box)), inline=True)
    embed.add_field(name="⚔️ Batalhas", value=fmt_num(data.get("battles", 0)), inline=True)

    embed.add_field(
        name=f"📖 Pokédex — {progress}/{total} ({pct}%)",
        value=f"```\n{hp_bar(progress / max(1, total), 18)}\n```"
              f"👹 Bosses: **{len([b for b in bosses if b not in ('???','Leonking')])}/"
              f"{len([x for x in BOSSES if x.get('special') != 'final_boss'])}**",
        inline=False,
    )

    if is_pokedex_complete(data) and "Leonking" not in bosses and "???" not in bosses:
        embed.add_field(
            name="🌌 POKÉDEX COMPLETA!",
            value="Usa `/desafiar_final` para enfrentar o **DEUS ABSOLUTO**!",
            inline=False,
        )
    if "Leonking" in bosses or "???" in bosses:
        embed.add_field(name="👑 Campeão", value="Derrotaste o DEUS ABSOLUTO LEONKING!", inline=False)

    active = get_active_mon(data)
    if active:
        refresh_mon_stats(active)
        embed.add_field(
            name="🎯 Monstro Ativo",
            value=f"{active['e']} **{active.get('species', '?')}** Lv.{active.get('level', 1)} "
                  f"{tier_stars(active.get('tier', 1))}\n"
                  f"❤️ {active['hp']}/{active['maxHp']}  ⚔️ {active['atkStat']}",
            inline=False,
        )
    return embed


def embed_team(user: discord.abc.User, data: dict) -> discord.Embed:
    team = data.get("team", [])
    aid = data.get("activeMonId")
    embed = discord.Embed(title=f"🐾 Equipa de {user.display_name}", color=0x5090e0)
    if not team:
        embed.description = "A tua equipa está vazia. Usa `/cacar` para capturar monstros!"
        return embed
    for i, m in enumerate(team, 1):
        refresh_mon_stats(m)
        marker = "🎯 " if m.get("id") == aid else ""
        status = "" if m.get("alive", True) else " 💀"
        embed.add_field(
            name=f"{marker}{i}. {m['e']} {m.get('species', '?')}{status}",
            value=f"Lv.**{m.get('level', 1)}** {tier_stars(m.get('tier', 1))}\n"
                  f"{type_badge(m.get('t', '?'))}\n"
                  f"❤️ {m['hp']}/{m['maxHp']}  ⚔️ {m['atkStat']}",
            inline=True,
        )
    embed.set_footer(text="Usa /ativar [posição] para trocar o monstro ativo.")
    return embed


def embed_box(user: discord.abc.User, data: dict, page: int = 0) -> discord.Embed:
    box = data.get("box", [])
    per_page = 12
    total_pages = max(1, (len(box) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    chunk = box[start:start + per_page]

    embed = discord.Embed(
        title=f"📦 Box de {user.display_name}",
        description=f"**{len(box)}** monstros guardados  ·  Página **{page + 1}/{total_pages}**",
        color=0x8e44ad,
    )
    if not chunk:
        embed.description += "\n\nA tua box está vazia."
        return embed
    for m in chunk:
        refresh_mon_stats(m)
        embed.add_field(
            name=f"{m['e']} {m.get('species', '?')}",
            value=f"Lv.{m.get('level', 1)} {tier_stars(m.get('tier', 1))}\n"
                  f"❤️{m['hp']}/{m['maxHp']} ⚔️{m['atkStat']}",
            inline=True,
        )
    embed.set_footer(text="Usa /trocar para mover entre equipa e box.")
    return embed


def embed_pokedex(user: discord.abc.User, data: dict) -> discord.Embed:
    caught = set(data.get("caught", []))
    bosses = data.get("bossDefeated", [])
    progress = pokedex_progress(data)
    total = pokedex_total()
    pct = int(progress / total * 100) if total else 0

    by_rarity = {"comum": 0, "incomum": 0, "raro": 0, "épico": 0,
                 "lendário": 0, "mítico": 0, "divino": 0}
    rare_totals = {r: 0 for r in by_rarity}
    for m in MONS:
        rare_totals[m["rare"]] = rare_totals.get(m["rare"], 0) + 1
        if m["n"] in caught:
            by_rarity[m["rare"]] += 1

    embed = discord.Embed(
        title=f"📖 Pokédex — {progress}/{total} ({pct}%)",
        description=f"```\n{hp_bar(progress / max(1, total), 22)}\n```",
        color=0xffd700 if progress >= total else 0x5090e0,
    )

    lines = []
    for r in ["comum", "incomum", "raro", "épico", "lendário", "mítico", "divino"]:
        lines.append(f"• **{r}**: {by_rarity[r]}/{rare_totals[r]}")
    embed.add_field(name="📊 Por raridade", value="\n".join(lines), inline=True)

    bosses_regular = [b for b in BOSSES if b.get("special") not in ("final_boss",)]
    defeated_regular = [b for b in bosses if b not in ("???", "Leonking")]
    embed.add_field(
        name="👹 Bosses",
        value=f"Derrotados: **{len(defeated_regular)}/{len(bosses_regular)}**\n"
              + ("🌌 FINAL: Leonking ✅" if "Leonking" in bosses else "🌌 FINAL: por derrotar"),
        inline=True,
    )

    if is_pokedex_complete(data) and "Leonking" not in bosses:
        embed.add_field(
            name="🌟 POKÉDEX COMPLETA",
            value="Usa `/desafiar_final` para o **DEUS ABSOLUTO**!",
            inline=False,
        )
    return embed


def embed_inventory(user: discord.abc.User, data: dict) -> discord.Embed:
    items = data.get("items", {})
    mats = data.get("materials", {})
    embed = discord.Embed(title=f"🎒 Inventário de {user.display_name}", color=0x27ae60)
    embed.add_field(name="💰 Ouro", value=fmt_num(data.get("gold", 0)), inline=True)
    embed.add_field(name="🔮 Balls", value=str(data.get("balls", 0)), inline=True)
    embed.add_field(name="⭐ Master Balls", value=str(data.get("masterball", 0)), inline=True)

    if items:
        lines = []
        for iid, q in items.items():
            if q <= 0:
                continue
            s = SHOP_INDEX.get(iid, {})
            lines.append(f"{s.get('e', '📦')} **{s.get('n', iid)}** × {q}")
        if lines:
            embed.add_field(name="🧪 Itens", value="\n".join(lines), inline=False)
    if mats:
        lines = [f"🪨 **{n}** × {q}" for n, q in mats.items() if q > 0]
        if lines:
            embed.add_field(name="🪨 Materiais", value="\n".join(lines[:15]), inline=False)
    return embed


def embed_shop() -> discord.Embed:
    embed = discord.Embed(
        title="🛒 Loja",
        description="Usa `/comprar [id]` para adquirir itens.",
        color=0xe4c243,
    )
    for s in SHOP_ITEMS:
        embed.add_field(
            name=f"{s['e']} {s['n']} — 💰 {s['price']}",
            value=f"`{s['id']}` · {s['desc']}",
            inline=False,
        )
    return embed


def embed_bosses_list(data: dict) -> discord.Embed:
    defeated = data.get("bossDefeated", [])
    complete = is_pokedex_complete(data)
    embed = discord.Embed(
        title="👹 Bosses",
        description=f"Derrotados: **{len(defeated)}/{len(BOSSES)}**",
        color=0x8a0020,
    )
    for b in BOSSES:
        status = "✅" if b["n"] in defeated else "🔒"
        tag = ""
        if b.get("special") == "master_only":
            tag = " 👑 *Master Ball only*"
        elif b.get("special") == "nico":
            tag = " 🐈 *Secreto — 3 poções no OXIGÉNIO*"
        elif b.get("special") == "murilo":
            tag = " 👨‍🦽 *Secreto*"
        elif b.get("special") == "final_boss":
            if complete and b["n"] not in defeated:
                tag = " 🌌 **BOSS FINAL — DESBLOQUEADO**"
            else:
                tag = f" 🌌 *Requer Pokédex completa ({pokedex_progress(data)}/{pokedex_total()})*"

        if b.get("special") == "final_boss" and not complete:
            body = "*???*\n❤️ ??? · ⚔️ ??? · 💰 ???"
        else:
            body = (f"*{b.get('title', '?')}*\n"
                    f"{type_badge(b['t'])} · ❤️{fmt_num(b['hp'])} · "
                    f"⚔️{fmt_num(b['atk'])} · 💰{fmt_num(b['reward'])}")
        embed.add_field(name=f"{status} {b['e']} {b['n']}{tag}", value=body, inline=False)
    return embed


def embed_battle(data: dict, msg: str = "") -> discord.Embed:
    """HUD de batalha contra selvagem."""
    wild = data.get("wild", {})
    active = data.get("playerMon") or get_active_mon(data)
    wild_ratio = data.get("wildHp", 0) / max(1, data.get("wildMaxHp", 1))

    color = rarity_color(wild.get("rare", "comum"))
    embed = discord.Embed(
        title=f"🏹 Encontro Selvagem!",
        description=f"# {wild.get('e', '?')} **{wild.get('n', '?')}**\n"
                    f"{type_badge(wild.get('t', '?'))} · *{wild.get('rare', '?')}*",
        color=color,
    )
    embed.add_field(
        name=f"🔴 HP Selvagem — {data.get('wildHp', 0)}/{data.get('wildMaxHp', 0)}",
        value=f"```\n{hp_bar(wild_ratio, 14)}\n```",
        inline=False,
    )
    if active:
        refresh_mon_stats(active)
        pr = active["hp"] / max(1, active["maxHp"])
        embed.add_field(
            name=f"❤️ {active['e']} {active.get('species', '?')} — {active['hp']}/{active['maxHp']}",
            value=f"Lv.{active.get('level', 1)} {tier_stars(active.get('tier', 1))}\n"
                  f"```\n{hp_bar(pr, 12)}\n```",
            inline=False,
        )
    chance = get_catch_chance(wild, data)
    embed.add_field(name="🎯 Chance de captura", value=f"**{int(chance * 100)}%**", inline=True)
    embed.add_field(name="🔮 Balls", value=str(data.get("balls", 0)), inline=True)
    if msg:
        embed.add_field(name="📋 Ação", value=msg, inline=False)
    return embed


def embed_boss(data: dict, msg: str = "") -> discord.Embed:
    """HUD de batalha contra boss — inclui avisos, fases e todos os indicadores."""
    boss = data.get("boss", {})
    active = data.get("playerMon") or get_active_mon(data)
    ratio_boss = data.get("bossHp", 0) / max(1, data.get("bossMaxHp", 1))
    ratio_player = data.get("playerHp", 0) / max(1, data.get("playerMaxHp", 1))

    is_final = boss.get("special") == "final_boss"
    phase = data.get("finalBossPhase", 0)

    if is_final and phase == 2:
        color, prefix = 0xffd700, "🐐 BOSS FINAL — FASE 2"
    elif is_final:
        color, prefix = 0xff00ff, "🌌 BOSS FINAL — FASE 1"
    elif boss.get("special") == "nico":
        color, prefix = 0xff00aa, "🐈 BOSS SECRETO"
    elif boss.get("special") == "master_only":
        color, prefix = 0x6a30ff, "👑 MASTER-ONLY"
    elif boss.get("special") == "murilo":
        color, prefix = 0x1b1111, "👨‍🦽 BOSS SECRETO"
    elif ratio_boss > 0.5:
        color, prefix = 0x8a0020, "💀 BOSS"
    else:
        color, prefix = 0xff0000, "💀 BOSS"

    embed = discord.Embed(
        title=f"{prefix}: {boss.get('e', '')} {boss.get('n', '?')}",
        description=f"*{boss.get('title', 'Chefe Lendário')}*",
        color=color,
    )

    # Imagem da fase 2 do boss final
    if is_final and phase == 2 and boss.get("image"):
        embed.set_image(url=boss["image"])

    # Aviso de ataque especial a carregar
    if data.get("bossCharging"):
        embed.add_field(
            name="⚠️ ATAQUE ESPECIAL A CARREGAR!",
            value="Prepara-te! O próximo ataque do Boss fará **x1.8 dano**. Usa 🛡️ **Defender** para reduzir!",
            inline=False,
        )

    # Aviso automático de 20% HP
    if (ratio_boss <= 0.2 and ratio_boss > 0
            and not (is_final and phase == 1) and boss.get("special") != "master_only"):
        embed.add_field(
            name="🌀 Boss em HP crítico!",
            value="Considera **tentar capturar** antes de matares — matá-lo deita a chance fora!",
            inline=False,
        )

    embed.add_field(
        name=f"🔴 HP Boss — {fmt_num(data.get('bossHp', 0))}/{fmt_num(data.get('bossMaxHp', 0))}  ({int(ratio_boss*100)}%)",
        value=f"```\n{hp_bar(ratio_boss, 16)}\n```",
        inline=False,
    )

    embed.add_field(name="Tipo", value=type_badge(boss.get("t", "?")), inline=True)
    embed.add_field(name="⚔️ ATK", value=f"**{fmt_num(boss.get('atk', 0))}**", inline=True)
    cd = data.get("bossBallCD", 0)
    embed.add_field(name="🔮 Ball", value="Disponível" if cd <= 0 else f"⏳ {cd} turno(s)", inline=True)

    if active:
        shield = ""
        if data.get("bossShield", 0) > 0:
            shield += "  🛡️ Escudo"
        if data.get("defending"):
            shield += "  🛡️ A defender"
        embed.add_field(
            name=f"❤️ {active['e']} {active.get('species', '?')} — {data.get('playerHp', 0)}/{data.get('playerMaxHp', 0)}{shield}",
            value=f"Lv.{active.get('level', 1)} {tier_stars(active.get('tier', 1))}\n"
                  f"```\n{hp_bar(ratio_player, 14)}\n```",
            inline=False,
        )

    if msg:
        embed.add_field(name="📋 Combate", value=msg, inline=False)

    phase_txt = ""
    if is_final and phase == 1:
        phase_txt = "  ·  🌌 Fase 1/2 (não podes capturar)"
    elif is_final and phase == 2:
        phase_txt = "  ·  👑 Fase Final"
    reward = boss.get("reward", 0)
    mats = ", ".join(m["n"] for m in boss.get("mats", []))
    embed.set_footer(text=f"💰 {fmt_num(reward)} ouro  ·  🪨 {mats}{phase_txt}")
    return embed


# ══════════════════════════════════════════════════════════════
# VIEW: CAÇA (batalha contra selvagem)
# ══════════════════════════════════════════════════════════════

class HuntView(discord.ui.View):
    def __init__(self, uid: int):
        super().__init__(timeout=300)
        self.uid = uid

    async def _guard(self, interaction: discord.Interaction) -> Optional[dict]:
        if interaction.user.id != self.uid:
            await interaction.response.send_message("❌ Não é a tua caça!", ephemeral=True)
            return None
        data = load_save(self.uid)
        if not data.get("inBattle"):
            await interaction.response.edit_message(content="❌ Sem caça ativa.", embed=None, view=None)
            return None
        return data

    @discord.ui.button(label="Atacar", emoji="⚔️", style=discord.ButtonStyle.danger)
    async def attack(self, interaction: discord.Interaction, _: discord.ui.Button):
        data = await self._guard(interaction)
        if not data:
            return
        active = get_active_mon(data)
        if not active or not active.get("alive"):
            await interaction.response.send_message("❌ Sem monstro ativo vivo!", ephemeral=True)
            return

        refresh_mon_stats(active)
        wild = data["wild"]
        mult = get_type_mult(active.get("t", ""), wild.get("t", ""))
        atk = active["atkStat"]
        if data.get("xatkActive"):
            atk = int(atk * 1.6)
            data["xatkActive"] = False

        dmg = max(1, int(atk * mult * random.uniform(0.85, 1.15)))
        data["wildHp"] = max(0, data["wildHp"] - dmg)
        hint = " ⚡ Super eficaz!" if mult > 1 else (" 💧 Não muito eficaz..." if mult < 1 else "")
        lines = [f"⚔️ {active['e']} atacou! **-{dmg}**{hint}"]

        if data["wildHp"] <= 0:
            data["inBattle"] = False
            levels = gain_xp(active, 15 + wild.get("atk", 5))
            gold = 5 + wild.get("atk", 5) * 2
            data["gold"] = data.get("gold", 0) + gold
            data["battles"] = data.get("battles", 0) + 1
            nm = wild.get("mat", {}).get("n", "")
            if nm:
                data["materials"][nm] = data["materials"].get(nm, 0) + 1
            lines.append(f"\n🏆 Derrotaste **{wild['n']}**!")
            lines.append(f"💰 +{gold} ouro · ⭐ +XP" + (f" (**+{levels} níveis!**)" if levels else ""))
            write_save(self.uid, data)
            await interaction.response.edit_message(embed=embed_battle(data, "\n".join(lines)), view=None)
            return

        # Contra-ataque do selvagem
        raw = wild.get("atk", 5) * random.uniform(0.7, 1.1)
        raw *= get_type_mult(wild.get("t", ""), active.get("t", ""))
        counter = max(1, int(raw))
        active["hp"] = max(0, active["hp"] - counter)
        lines.append(f"💥 {wild['e']} contra-atacou! **-{counter} HP**")
        if active["hp"] <= 0:
            active["alive"] = False
            data["inBattle"] = False
            lines.append(f"\n💀 {active.get('species', '?')} foi derrotado!")
            write_save(self.uid, data)
            await interaction.response.edit_message(embed=embed_battle(data, "\n".join(lines)), view=None)
            return

        write_save(self.uid, data)
        await interaction.response.edit_message(embed=embed_battle(data, "\n".join(lines)), view=self)

    @discord.ui.button(label="Capturar", emoji="🔮", style=discord.ButtonStyle.primary)
    async def catch(self, interaction: discord.Interaction, _: discord.ui.Button):
        data = await self._guard(interaction)
        if not data:
            return
        if data.get("balls", 0) <= 0:
            await interaction.response.send_message("❌ Sem Balls! Compra em `/loja`.", ephemeral=True)
            return
        data["balls"] -= 1
        wild = data["wild"]
        chance = get_catch_chance(wild, data)
        if random.random() < chance:
            data["inBattle"] = False
            if wild["n"] not in data["caught"]:
                data["caught"].append(wild["n"])
            new_mon = create_mon_from_species(wild, data["nextMonId"])
            data["nextMonId"] += 1
            if len(data.get("team", [])) < 6:
                data["team"].append(new_mon)
                if not data.get("activeMonId"):
                    data["activeMonId"] = new_mon["id"]
            else:
                data["box"].append(new_mon)
            data["gold"] = data.get("gold", 0) + 10
            write_save(self.uid, data)
            em = discord.Embed(
                title=f"✨ Capturaste {wild['e']} {wild['n']}!",
                description=f"*{wild.get('rare', '?')}* · {type_badge(wild.get('t', '?'))}\n"
                            f"Adicionado à {'equipa' if len(data['team']) <= 6 else 'box'}!",
                color=rarity_color(wild.get("rare", "comum")),
            )
            await interaction.response.edit_message(embed=em, view=None)
            return

        lines = [f"🌀 Captura falhou! (**{int(chance*100)}%**) · 🔮 {data['balls']} balls restantes"]
        # Selvagem pode contra-atacar
        active = get_active_mon(data)
        if active and active.get("alive"):
            counter = max(1, int(wild.get("atk", 5) * random.uniform(0.5, 0.9)))
            active["hp"] = max(0, active["hp"] - counter)
            lines.append(f"💥 {wild['e']} ficou irritado! **-{counter} HP**")
            if active["hp"] <= 0:
                active["alive"] = False
                data["inBattle"] = False
                lines.append(f"\n💀 {active.get('species', '?')} foi derrotado!")
                write_save(self.uid, data)
                await interaction.response.edit_message(embed=embed_battle(data, "\n".join(lines)), view=None)
                return
        write_save(self.uid, data)
        await interaction.response.edit_message(embed=embed_battle(data, "\n".join(lines)), view=self)

    @discord.ui.button(label="X-Ataque", emoji="💢", style=discord.ButtonStyle.secondary, row=1)
    async def xatk(self, interaction: discord.Interaction, _: discord.ui.Button):
        data = await self._guard(interaction)
        if not data:
            return
        items = data.get("items", {})
        if items.get("xatk", 0) <= 0:
            await interaction.response.send_message("❌ Sem X-Ataque! Compra em `/loja`.", ephemeral=True)
            return
        items["xatk"] -= 1
        data["items"] = items
        data["xatkActive"] = True
        write_save(self.uid, data)
        await interaction.response.edit_message(
            embed=embed_battle(data, "💢 **X-Ataque ativado!** O próximo ataque dá +60% dano."), view=self
        )

    @discord.ui.button(label="Fugir", emoji="🏃", style=discord.ButtonStyle.danger, row=1)
    async def run(self, interaction: discord.Interaction, _: discord.ui.Button):
        data = await self._guard(interaction)
        if not data:
            return
        data["inBattle"] = False
        data["wild"] = None
        write_save(self.uid, data)
        await interaction.response.edit_message(content="🏃 Fugiste do encontro!", embed=None, view=None)


# ══════════════════════════════════════════════════════════════
# VIEW: BOSS (com todas as mecânicas do HTML)
# ══════════════════════════════════════════════════════════════

def boss_counterattack(data: dict, lines: list[str]) -> None:
    """Processa o contra-ataque do boss: especial a cada 3 turnos, raridade, escudo, defender."""
    boss = data["boss"]
    data["bossTurn"] = data.get("bossTurn", 0) + 1

    raw = boss["atk"] * random.uniform(0.8, 1.2)
    active = data.get("playerMon") or get_active_mon(data)

    # Type effectiveness: boss vs monstro do jogador
    if active:
        raw *= get_type_mult(boss.get("t", ""), active.get("t", ""))
        sp = MON_INDEX.get(active.get("species", ""), {})
        if sp.get("rare") == "comum":
            raw *= 2.0
        elif sp.get("rare") == "incomum":
            raw *= 1.5

    is_special = False
    if data.get("bossCharging"):
        raw *= 1.8
        data["bossCharging"] = False
        is_special = True

    if data.get("bossShield", 0) > 0:
        absorbed = int(raw * 0.4)
        raw -= absorbed
        data["bossShield"] -= 1
        lines.append(f"🛡️ Escudo absorveu **{fmt_num(absorbed)}** dano!")

    if data.get("defending"):
        raw *= 0.4

    dmg = max(1, int(raw))
    data["playerHp"] = max(0, data.get("playerHp", 0) - dmg)
    data["defending"] = False
    if active:
        active["hp"] = data["playerHp"]
        active["alive"] = active["hp"] > 0

    prefix = "💥 **ATAQUE ESPECIAL!** " if is_special else ""
    lines.append(f"{prefix}👹 {boss['e']} atacou! **-{fmt_num(dmg)} HP**")

    # Anuncia próximo especial
    if data["bossTurn"] % 3 == 0 and not data.get("bossCharging"):
        data["bossCharging"] = True
        lines.append("⚠️ O Boss está a **carregar** um ataque especial! Defende no próximo turno!")

    if data.get("bossBallCD", 0) > 0:
        data["bossBallCD"] -= 1


class BossView(discord.ui.View):
    def __init__(self, uid: int):
        super().__init__(timeout=900)
        self.uid = uid

    async def _guard(self, interaction: discord.Interaction) -> Optional[dict]:
        if interaction.user.id != self.uid:
            await interaction.response.send_message("❌ Não é a tua batalha!", ephemeral=True)
            return None
        data = load_save(self.uid)
        if not data.get("inBossBattle") or not data.get("boss"):
            await interaction.response.edit_message(content="❌ Sem batalha de boss ativa.", embed=None, view=None)
            return None
        return data

    async def _end_victory(self, interaction, data, boss, active, lines):
        # Fase 1 → Fase 2 do boss final
        if boss.get("special") == "final_boss" and data.get("finalBossPhase") == 1:
            lines.append("\n💥 **A primeira forma caiu... mas algo pior desperta!**")
            start_final_boss_phase2(data)
            write_save(self.uid, data)
            new_msg = "\n".join(lines) + "\n\n🐐 **O Rei Leonking surge na sua forma divina!**"
            await interaction.response.edit_message(embed=embed_boss(data, new_msg), view=BossView(self.uid))
            return

        # Vitória normal
        data["inBossBattle"] = False
        data["finalBossPhase"] = 0
        if boss["n"] not in data["bossDefeated"]:
            data["bossDefeated"].append(boss["n"])
        reward = boss.get("reward", 500)
        data["gold"] = data.get("gold", 0) + reward
        for m in boss.get("mats", []):
            data["materials"][m["n"]] = data["materials"].get(m["n"], 0) + 2
        if active:
            gain_xp(active, 60)

        extra = ""
        if boss.get("special") == "final_boss":
            extra = "\n\n# 🌟 COMPLETASTE O JOGO! 🌟\nDerrotaste o **DEUS ABSOLUTO LEONKING**!"
        elif boss.get("special") == "nico":
            extra = "\n\n🐈 *A Destruidora de Mundos foi vencida!*"

        em = discord.Embed(
            title=f"🏆 {boss['e']} {boss['n']} DERROTADO!",
            description=f"*{boss.get('title', '?')}* caiu!{extra}\n\n"
                        f"💰 +**{fmt_num(reward)}** ouro\n"
                        f"🪨 {', '.join(m['n'] for m in boss.get('mats', []))}\n"
                        f"⭐ +60 XP\n"
                        f"👹 Bosses: **{len(data['bossDefeated'])}/{len(BOSSES)}**",
            color=0xffd700,
        )
        write_save(self.uid, data)
        await interaction.response.edit_message(embed=em, view=None)

    async def _end_defeat(self, interaction, data, lines):
        data["inBossBattle"] = False
        data["finalBossPhase"] = 0
        penalty = int(data.get("gold", 0) * 0.1)
        data["gold"] = max(0, data.get("gold", 0) - penalty)
        lines.append(f"\n💀 Foste derrotado! Perdeste 💰 **{fmt_num(penalty)}**")
        write_save(self.uid, data)
        em = discord.Embed(title="💀 Derrota!", description="\n".join(lines), color=0xe03030)
        await interaction.response.edit_message(embed=em, view=None)

    @discord.ui.button(label="Atacar", emoji="⚔️", style=discord.ButtonStyle.danger, row=0)
    async def attack(self, interaction: discord.Interaction, _: discord.ui.Button):
        data = await self._guard(interaction)
        if not data:
            return
        active = data.get("playerMon") or get_active_mon(data)
        if not active:
            await interaction.response.send_message("❌ Sem monstro ativo!", ephemeral=True)
            return
        refresh_mon_stats(active)
        boss = data["boss"]
        mult = get_type_mult(active.get("t", ""), boss.get("t", ""))
        atk = active["atkStat"]
        if data.get("xatkActive"):
            atk = int(atk * 1.6)
            data["xatkActive"] = False
        dmg = max(1, int(atk * mult * random.uniform(0.85, 1.25)))
        data["bossHp"] = max(0, data["bossHp"] - dmg)
        hint = " ⚡ Super eficaz!" if mult > 1 else (" 💧 Não muito eficaz..." if mult < 1 else "")
        lines = [f"⚔️ {active['e']} {active.get('species', '?')} atacou! **-{fmt_num(dmg)}**{hint}"]

        ratio = data["bossHp"] / max(1, data["bossMaxHp"])
        is_final = boss.get("special") == "final_boss"
        if (ratio <= 0.2 and ratio > 0 and not data.get("lowHpWarned")
                and not (is_final and data.get("finalBossPhase") == 1)
                and boss.get("special") != "master_only"):
            data["lowHpWarned"] = True
            lines.append("⚠️ **Boss abaixo de 20% HP** — considera tentar capturar!")

        if data["bossHp"] <= 0:
            data["bossHp"] = 0
            await self._end_victory(interaction, data, boss, active, lines)
            return

        boss_counterattack(data, lines)
        if data["playerHp"] <= 0:
            await self._end_defeat(interaction, data, lines)
            return
        write_save(self.uid, data)
        await interaction.response.edit_message(embed=embed_boss(data, "\n".join(lines)), view=self)

    @discord.ui.button(label="Defender", emoji="🛡️", style=discord.ButtonStyle.secondary, row=0)
    async def defend(self, interaction: discord.Interaction, _: discord.ui.Button):
        data = await self._guard(interaction)
        if not data:
            return
        data["defending"] = True
        lines = ["🛡️ A defender! Próximo dano reduzido a **40%**."]
        boss_counterattack(data, lines)
        if data["playerHp"] <= 0:
            await self._end_defeat(interaction, data, lines)
            return
        write_save(self.uid, data)
        await interaction.response.edit_message(embed=embed_boss(data, "\n".join(lines)), view=self)

    @discord.ui.button(label="Ball", emoji="🔮", style=discord.ButtonStyle.primary, row=0)
    async def ball(self, interaction: discord.Interaction, _: discord.ui.Button):
        data = await self._guard(interaction)
        if not data:
            return
        boss = data["boss"]

        if boss.get("special") == "final_boss" and data.get("finalBossPhase") == 1:
            await interaction.response.send_message(
                "🌌 A **primeira forma** não pode ser capturada — derrota-a primeiro!", ephemeral=True
            )
            return
        if data.get("bossBallCD", 0) > 0:
            await interaction.response.send_message(
                f"⏳ Ball em recarga! Restam **{data['bossBallCD']}** turno(s).", ephemeral=True
            )
            return

        # Void King (master-only)
        if boss.get("special") == "master_only":
            if data.get("masterball", 0) <= 0:
                await interaction.response.send_message(
                    "👑 **Void King** só pode ser capturado com **Master Ball**!", ephemeral=True
                )
                return
            data["masterball"] -= 1
            chance = 1.0
        else:
            if data.get("balls", 0) <= 0:
                await interaction.response.send_message("❌ Sem Balls!", ephemeral=True)
                return
            data["balls"] -= 1
            data["bossBallCD"] = 3
            ratio = data["bossHp"] / max(1, data["bossMaxHp"])
            chance = 0.15
            if ratio <= 0.5:
                chance += 0.10
            if ratio <= 0.2:
                chance += 0.15
            if data.get("defending"):
                chance += 0.05

        if random.random() < chance:
            data["inBossBattle"] = False
            data["finalBossPhase"] = 0
            if boss["n"] not in data["bossDefeated"]:
                data["bossDefeated"].append(boss["n"])
            captured = {
                "id": data["nextMonId"],
                "species": boss["n"], "n": boss["n"], "e": boss["e"],
                "t": boss.get("t", "boss"), "c": 0xffd700,
                "level": 50, "tier": 5, "xp": 0,
                "baseHp": data["bossMaxHp"], "baseAtk": boss["atk"],
                "hp": data["bossMaxHp"], "maxHp": data["bossMaxHp"], "atkStat": boss["atk"],
                "hpBoost": 0, "atkBoost": 0, "alive": True, "isBoss": True,
            }
            data["nextMonId"] += 1
            if len(data.get("team", [])) < 6:
                data["team"].append(captured)
            else:
                data["box"].append(captured)
            data["gold"] = data.get("gold", 0) + boss.get("reward", 500)
            for m in boss.get("mats", []):
                data["materials"][m["n"]] = data["materials"].get(m["n"], 0) + 2
            write_save(self.uid, data)

            extra = ""
            if boss.get("special") == "final_boss":
                extra = "\n\n# 🌟 CAPTURASTE O DEUS ABSOLUTO LEONKING! 🌟"
            elif boss.get("special") == "nico":
                extra = "\n\n🐈 *A Destruidora de Mundos é agora tua!*"

            em = discord.Embed(
                title=f"✨ {boss['e']} {boss['n']} CAPTURADO!",
                description=f"O boss foi para a tua equipa/box!{extra}\n\n"
                            f"⭐ Tier 5 {tier_stars(5)}\n"
                            f"❤️ {fmt_num(data['bossMaxHp'])} HP · "
                            f"⚔️ {fmt_num(boss['atk'])} ATK\n"
                            f"💰 +{fmt_num(boss.get('reward', 500))} ouro",
                color=0xffd700,
            )
            await interaction.response.edit_message(embed=em, view=None)
            return

        lines = [f"🌀 Ball falhou! (**{int(chance*100)}%**) · 🔮 {data.get('balls', 0)} restantes"]
        boss_counterattack(data, lines)
        if data["playerHp"] <= 0:
            await self._end_defeat(interaction, data, lines)
            return
        write_save(self.uid, data)
        await interaction.response.edit_message(embed=embed_boss(data, "\n".join(lines)), view=self)

    @discord.ui.button(label="Curar", emoji="💊", style=discord.ButtonStyle.success, row=1)
    async def heal(self, interaction: discord.Interaction, _: discord.ui.Button):
        data = await self._guard(interaction)
        if not data:
            return
        items = data.get("items", {})
        max_hp = data.get("playerMaxHp", 100)
        order = [
            ("hyperpotion", max_hp, "✨ Hyper"),
            ("megapotion", max_hp // 2, "💊 Mega"),
            ("superpotion", 150, "💚 Super"),
            ("potion", 60, "🧪"),
        ]
        used_id, heal_amt, label = None, 0, ""
        for iid, amt, lab in order:
            if items.get(iid, 0) > 0:
                used_id, heal_amt, label = iid, amt, lab
                break
        if not used_id:
            await interaction.response.send_message("❌ Sem poções! Compra em `/loja`.", ephemeral=True)
            return
        old = data.get("playerHp", 0)
        data["playerHp"] = min(max_hp, old + heal_amt)
        items[used_id] -= 1
        data["items"] = items
        lines = [f"{label} Poção usada! **+{data['playerHp'] - old} HP** → {data['playerHp']}/{max_hp}"]
        boss_counterattack(data, lines)
        if data["playerHp"] <= 0:
            await self._end_defeat(interaction, data, lines)
            return
        write_save(self.uid, data)
        await interaction.response.edit_message(embed=embed_boss(data, "\n".join(lines)), view=self)

    @discord.ui.button(label="Escudo", emoji="🛡️", style=discord.ButtonStyle.secondary, row=1)
    async def shield(self, interaction: discord.Interaction, _: discord.ui.Button):
        data = await self._guard(interaction)
        if not data:
            return
        items = data.get("items", {})
        if items.get("shield", 0) <= 0:
            await interaction.response.send_message("❌ Sem Escudo Mágico! Compra em `/loja`.", ephemeral=True)
            return
        items["shield"] -= 1
        data["items"] = items
        data["bossShield"] = data.get("bossShield", 0) + 1
        write_save(self.uid, data)
        await interaction.response.edit_message(
            embed=embed_boss(data, "🛡️ **Escudo Mágico ativado!** Absorve 40% do próximo ataque."), view=self
        )

    @discord.ui.button(label="Fugir", emoji="🏃", style=discord.ButtonStyle.danger, row=1)
    async def flee(self, interaction: discord.Interaction, _: discord.ui.Button):
        data = await self._guard(interaction)
        if not data:
            return
        data["inBossBattle"] = False
        data["boss"] = None
        data["finalBossPhase"] = 0
        data["bossCharging"] = False
        data["bossTurn"] = 0
        data["bossBallCD"] = 0
        write_save(self.uid, data)
        await interaction.response.edit_message(content="🏃 Recuaste da batalha!", embed=None, view=None)


# ══════════════════════════════════════════════════════════════
# HELPERS DE BATALHA
# ══════════════════════════════════════════════════════════════

def start_boss_battle(data: dict, boss: dict, mon: dict) -> None:
    refresh_mon_stats(mon)
    is_final = boss.get("special") == "final_boss"
    scale = 1.0 if is_final else compute_boss_scale(data)
    scaled_hp = max(1, int(round(boss["hp"] * scale)))
    scaled_atk = max(1, int(round(boss["atk"] * scale)))

    data["inBossBattle"] = True
    data["boss"] = {**boss, "hp": scaled_hp, "atk": scaled_atk}
    data["bossHp"] = scaled_hp
    data["bossMaxHp"] = scaled_hp
    data["playerHp"] = mon["hp"]
    data["playerMaxHp"] = mon["maxHp"]
    data["playerMon"] = mon
    data["defending"] = False
    data["bossShield"] = 0
    data["bossCharging"] = False
    data["bossTurn"] = 0
    data["bossBallCD"] = 0
    data["lowHpWarned"] = False
    data["finalBossPhase"] = 1 if is_final else 0


# ══════════════════════════════════════════════════════════════
# COMANDOS SLASH
# ══════════════════════════════════════════════════════════════

@tree.command(name="start", description="Começa (ou reinicia) a tua aventura.")
async def cmd_start(interaction: discord.Interaction):
    uid = interaction.user.id
    if os.path.exists(save_path(uid)):
        await interaction.response.send_message(
            "🎮 Já tens um save ativo! Usa `/perfil` para ver o teu progresso ou "
            "`/reset` se queres recomeçar.", ephemeral=True
        )
        return
    data = default_save()
    # Oferece um monstro inicial (comum aleatório)
    starters = [m for m in MONS if m["rare"] == "comum"]
    sp = random.choice(starters)
    starter = create_mon_from_species(sp, data["nextMonId"])
    data["nextMonId"] += 1
    data["team"].append(starter)
    data["activeMonId"] = starter["id"]
    data["caught"].append(sp["n"])
    write_save(uid, data)

    em = discord.Embed(
        title="🎉 Bem-vindo ao Monster Hunter RPG!",
        description=f"Recebeste o teu primeiro monstro: {starter['e']} **{starter['species']}**!\n\n"
                    "Usa `/ajuda` para ver todos os comandos disponíveis.",
        color=0x27ae60,
    )
    em.add_field(name="💰 Ouro inicial", value="50", inline=True)
    em.add_field(name="🔮 Balls", value="5", inline=True)
    em.set_footer(text="Começa a tua jornada com /cacar!")
    await interaction.response.send_message(embed=em)


@tree.command(name="reset", description="Apaga o teu save e recomeça do zero.")
async def cmd_reset(interaction: discord.Interaction):
    uid = interaction.user.id
    if os.path.exists(save_path(uid)):
        os.remove(save_path(uid))
    await interaction.response.send_message(
        "🗑️ Save apagado. Usa `/start` para começar de novo.", ephemeral=True
    )


@tree.command(name="perfil", description="Vê o teu perfil completo.")
async def cmd_perfil(interaction: discord.Interaction):
    data = load_save(interaction.user.id)
    await interaction.response.send_message(embed=embed_profile(interaction.user, data))


@tree.command(name="equipa", description="Vê a tua equipa de monstros.")
async def cmd_equipa(interaction: discord.Interaction):
    data = load_save(interaction.user.id)
    await interaction.response.send_message(embed=embed_team(interaction.user, data))


@tree.command(name="box", description="Vê os monstros na tua box.")
@app_commands.describe(pagina="Página da box (default 1)")
async def cmd_box(interaction: discord.Interaction, pagina: int = 1):
    data = load_save(interaction.user.id)
    await interaction.response.send_message(embed=embed_box(interaction.user, data, pagina - 1))


@tree.command(name="ativar", description="Define o monstro ativo (1-6).")
@app_commands.describe(posicao="Posição na equipa (1-6)")
async def cmd_ativar(interaction: discord.Interaction, posicao: int):
    uid = interaction.user.id
    data = load_save(uid)
    team = data.get("team", [])
    if posicao < 1 or posicao > len(team):
        await interaction.response.send_message(
            f"❌ Posição inválida. A tua equipa tem {len(team)} monstros.", ephemeral=True
        )
        return
    mon = team[posicao - 1]
    data["activeMonId"] = mon["id"]
    write_save(uid, data)
    await interaction.response.send_message(
        f"🎯 Monstro ativo: {mon['e']} **{mon.get('species', '?')}**", ephemeral=True
    )


@tree.command(name="pokedex", description="Vê o teu progresso na Pokédex.")
async def cmd_pokedex(interaction: discord.Interaction):
    data = load_save(interaction.user.id)
    await interaction.response.send_message(embed=embed_pokedex(interaction.user, data))


@tree.command(name="inventario", description="Vê os teus itens e materiais.")
async def cmd_inv(interaction: discord.Interaction):
    data = load_save(interaction.user.id)
    await interaction.response.send_message(embed=embed_inventory(interaction.user, data))


@tree.command(name="loja", description="Abre a loja.")
async def cmd_loja(interaction: discord.Interaction):
    await interaction.response.send_message(embed=embed_shop())


@tree.command(name="comprar", description="Compra um item da loja.")
@app_commands.describe(item="ID do item (ex: potion, balls5, tiercore)", quantidade="Quantidade")
async def cmd_comprar(interaction: discord.Interaction, item: str, quantidade: int = 1):
    uid = interaction.user.id
    data = load_save(uid)
    s = SHOP_INDEX.get(item.lower())
    if not s:
        await interaction.response.send_message("❌ Item inválido. Vê os IDs em `/loja`.", ephemeral=True)
        return
    if quantidade < 1:
        quantidade = 1
    total = s["price"] * quantidade
    if data.get("gold", 0) < total:
        await interaction.response.send_message(
            f"❌ Sem ouro suficiente. Precisas de 💰 **{fmt_num(total)}**.", ephemeral=True
        )
        return
    data["gold"] -= total

    iid = s["id"]
    if iid == "balls5":
        data["balls"] = data.get("balls", 0) + 5 * quantidade
    elif iid == "masterball":
        data["masterball"] = data.get("masterball", 0) + quantidade
    else:
        data["items"][iid] = data["items"].get(iid, 0) + quantidade
    write_save(uid, data)
    await interaction.response.send_message(
        f"✅ Compraste **{quantidade}× {s['n']}** por 💰 **{fmt_num(total)}**.", ephemeral=True
    )


@tree.command(name="curar", description="Cura o monstro ativo com uma poção.")
@app_commands.describe(tipo="Tipo de poção (potion, superpotion, megapotion, hyperpotion, revive, maxrevive)")
async def cmd_curar(interaction: discord.Interaction, tipo: str = "potion"):
    uid = interaction.user.id
    data = load_save(uid)
    active = get_active_mon(data)
    if not active:
        await interaction.response.send_message("❌ Sem monstro ativo!", ephemeral=True)
        return

    tipo = tipo.lower()
    items = data.get("items", {})
    if items.get(tipo, 0) <= 0:
        await interaction.response.send_message(f"❌ Sem **{tipo}** no inventário!", ephemeral=True)
        return

    refresh_mon_stats(active)

    # === EVENTO SECRETO: NICO (3 poções seguidas no OXIGÉNIO) ===
    if tipo == "potion" and active.get("species", "") == "OXIGÉNIO":
        data["nicoPotions"] = data.get("nicoPotions", 0) + 1
        items["potion"] -= 1
        data["items"] = items
        if data["nicoPotions"] >= 3:
            data["nicoPotions"] = 0
            data["pendingBoss"] = "Nico"
            write_save(uid, data)
            em = discord.Embed(
                title="✨ O OXIGÉNIO BRILHA INTENSAMENTE!",
                description="# 🐈 NICO APARECEU!\n*A Destruidora de Mundos ouviu o chamado...*\n\n"
                            "⚠️ **Boss Secreto desbloqueado!** Usa `/boss` para enfrentá-la já.",
                color=0xff00aa,
            )
            await interaction.response.send_message(embed=em)
            return
        write_save(uid, data)
        await interaction.response.send_message(
            f"✨ O Oxigénio absorve a energia... (**{data['nicoPotions']}/3**)\n"
            f"Continua a usar **Poções** no OXIGÉNIO para invocar algo oculto..."
        )
        return

    max_hp = active["maxHp"]
    msg = ""
    if tipo == "potion" and active.get("alive", True) and active["hp"] < max_hp:
        active["hp"] = min(max_hp, active["hp"] + 60)
        items["potion"] -= 1
        msg = f"🧪 +60 HP → {active['hp']}/{max_hp}"
    elif tipo == "superpotion" and active.get("alive", True) and active["hp"] < max_hp:
        active["hp"] = min(max_hp, active["hp"] + 150)
        items["superpotion"] -= 1
        msg = f"💚 +150 HP → {active['hp']}/{max_hp}"
    elif tipo == "megapotion" and active.get("alive", True) and active["hp"] < max_hp:
        heal = int(max_hp * 0.5)
        active["hp"] = min(max_hp, active["hp"] + heal)
        items["megapotion"] -= 1
        msg = f"💊 +{heal} HP → {active['hp']}/{max_hp}"
    elif tipo == "hyperpotion" and active.get("alive", True) and active["hp"] < max_hp:
        active["hp"] = max_hp
        items["hyperpotion"] -= 1
        msg = f"✨ HP totalmente recuperado: {max_hp}/{max_hp}"
    elif tipo == "revive" and not active.get("alive", True):
        active["hp"] = int(max_hp * 0.75)
        active["alive"] = True
        items["revive"] -= 1
        msg = f"❤️ Reanimado com {active['hp']}/{max_hp} HP"
    elif tipo == "maxrevive" and not active.get("alive", True):
        active["hp"] = max_hp
        active["alive"] = True
        items["maxrevive"] -= 1
        msg = f"💖 Reanimado com HP total ({max_hp}/{max_hp})"
    else:
        await interaction.response.send_message(
            "❌ Não é possível usar este item agora (HP cheio ou monstro em estado errado).",
            ephemeral=True,
        )
        return

    data["items"] = items
    write_save(uid, data)
    await interaction.response.send_message(f"✅ {active['e']} {active.get('species', '?')} — {msg}")


@tree.command(name="usar", description="Usa um item permanente no monstro ativo.")
@app_commands.describe(item="protein, heartseed, tiercore")
async def cmd_usar(interaction: discord.Interaction, item: str):
    uid = interaction.user.id
    data = load_save(uid)
    active = get_active_mon(data)
    if not active:
        await interaction.response.send_message("❌ Sem monstro ativo!", ephemeral=True)
        return
    item = item.lower()
    items = data.get("items", {})
    if items.get(item, 0) <= 0:
        await interaction.response.send_message(f"❌ Sem **{item}** no inventário!", ephemeral=True)
        return

    if item == "protein":
        active["atkBoost"] = active.get("atkBoost", 0) + 10
        msg = "💪 +10 ATK permanente!"
    elif item == "heartseed":
        active["hpBoost"] = active.get("hpBoost", 0) + 10
        msg = "🌱 +10 HP permanente!"
    elif item == "tiercore":
        if active.get("tier", 1) >= 5:
            await interaction.response.send_message("⭐ Já está no Tier máximo!", ephemeral=True)
            return
        active["tier"] = active.get("tier", 1) + 1
        msg = f"🔺 Tier subiu para **{active['tier']}** {tier_stars(active['tier'])}"
    else:
        await interaction.response.send_message("❌ Item não utilizável aqui.", ephemeral=True)
        return

    items[item] -= 1
    data["items"] = items
    refresh_mon_stats(active)
    write_save(uid, data)
    await interaction.response.send_message(f"✅ {active['e']} {active.get('species', '?')} — {msg}")


@tree.command(name="cacar", description="Encontra um monstro selvagem para capturar.")
async def cmd_cacar(interaction: discord.Interaction):
    uid = interaction.user.id
    data = load_save(uid)
    if data.get("inBattle") or data.get("inBossBattle"):
        await interaction.response.send_message("⚔️ Já estás em batalha!", ephemeral=True)
        return
    active = get_active_mon(data)
    if not active or not active.get("alive"):
        await interaction.response.send_message(
            "❌ Precisas de um monstro vivo! Usa `/curar` ou `/ativar`.", ephemeral=True
        )
        return

    wild = spawn_wild(data)
    data["inBattle"] = True
    data["wild"] = wild
    data["wildMaxHp"] = wild["hp"]
    data["wildHp"] = wild["hp"]
    write_save(uid, data)
    await interaction.response.send_message(embed=embed_battle(data), view=HuntView(uid))


@tree.command(name="bosses", description="Lista todos os bosses.")
async def cmd_bosses(interaction: discord.Interaction):
    data = load_save(interaction.user.id)
    await interaction.response.send_message(embed=embed_bosses_list(data))


@tree.command(name="boss", description="Desafia um boss.")
@app_commands.describe(nome="Nome do boss (deixa em branco para aleatório)")
async def cmd_boss(interaction: discord.Interaction, nome: Optional[str] = None):
    uid = interaction.user.id
    data = load_save(uid)
    if data.get("inBattle") or data.get("inBossBattle"):
        await interaction.response.send_message("⚔️ Já estás em batalha!", ephemeral=True)
        return
    active = get_active_mon(data)
    if not active or not active.get("alive"):
        await interaction.response.send_message(
            "❌ Precisas de um monstro vivo! Usa `/curar` ou `/ativar`.", ephemeral=True
        )
        return

    pending = data.get("pendingBoss")
    boss: Optional[dict] = None

    if nome:
        boss = BOSS_INDEX.get(nome)
        if not boss:
            nomes = ", ".join(b["n"] for b in BOSSES if not b.get("special"))[:180]
            await interaction.response.send_message(
                f"❌ Boss não encontrado. Exemplos: {nomes}...", ephemeral=True
            )
            return
        if boss.get("special") == "final_boss":
            if not is_pokedex_complete(data):
                await interaction.response.send_message(
                    "🌌 O **DEUS ABSOLUTO** só pode ser desafiado com a Pokédex completa!\n"
                    f"Progresso: **{pokedex_progress(data)}/{pokedex_total()}**",
                    ephemeral=True,
                )
                return
        if boss.get("special") == "nico" and pending != "Nico":
            await interaction.response.send_message(
                "🐈 **Nico** é boss secreto! Usa 3 **Poções** no **OXIGÉNIO** para a invocares.",
                ephemeral=True,
            )
            return
    elif pending and BOSS_INDEX.get(pending):
        boss = BOSS_INDEX[pending]
        data["pendingBoss"] = None
    else:
        defeated = data.get("bossDefeated", [])
        pool = [b for b in BOSSES
                if b["n"] not in defeated
                and b.get("special") not in ("master_only", "nico", "final_boss", "murilo")]
        if not pool:
            pool = [b for b in BOSSES
                    if b.get("special") not in ("master_only", "nico", "final_boss", "murilo")]
        boss = random.choice(pool)

    start_boss_battle(data, boss, active)
    write_save(uid, data)

    em = discord.Embed(
        title=f"⚠️ BOSS APARECEU: {boss['e']} {boss['n']}",
        description=f"*{boss.get('title', '?')}*\n\nPreparado para a batalha?",
        color=0x8a0020,
    )
    em.add_field(name="❤️ HP", value=fmt_num(data["bossMaxHp"]), inline=True)
    em.add_field(name="⚔️ ATK", value=fmt_num(data["boss"]["atk"]), inline=True)
    em.add_field(name="💰 Recompensa", value=fmt_num(boss.get("reward", 0)), inline=True)
    em.set_footer(text="Usa os botões para lutar!")
    await interaction.response.send_message(embed=em)
    # Mostra a HUD completa de seguida
    await interaction.followup.send(embed=embed_boss(data, "A batalha começa!"), view=BossView(uid))


@tree.command(name="desafiar_final", description="🌌 Desafia o DEUS ABSOLUTO (Pokédex completa).")
async def cmd_final(interaction: discord.Interaction):
    uid = interaction.user.id
    data = load_save(uid)
    if data.get("inBattle") or data.get("inBossBattle"):
        await interaction.response.send_message("⚔️ Já estás em batalha!", ephemeral=True)
        return
    if not is_pokedex_complete(data):
        await interaction.response.send_message(
            f"❌ Pokédex incompleta: **{pokedex_progress(data)}/{pokedex_total()}**\n"
            "💡 Captura todos os monstros e derrota todos os bosses para desbloquear!",
            ephemeral=True,
        )
        return
    if "Leonking" in data.get("bossDefeated", []) or "???" in data.get("bossDefeated", []):
        await interaction.response.send_message(
            "👑 Já derrotaste o DEUS ABSOLUTO LEONKING!", ephemeral=True
        )
        return
    active = get_active_mon(data)
    if not active or not active.get("alive"):
        await interaction.response.send_message(
            "❌ Precisas de um monstro vivo!", ephemeral=True
        )
        return

    final = next((b for b in BOSSES if b.get("special") == "final_boss"), None)
    if not final:
        await interaction.response.send_message("❌ Boss final não encontrado!", ephemeral=True)
        return

    start_boss_battle(data, final, active)
    write_save(uid, data)

    em = discord.Embed(
        title="🌌 O DEUS ABSOLUTO DESPERTOU!",
        description=(
            "# ❓ ???\n*O ser que transcende a realidade...*\n\n"
            "⚠️ **Esta é uma batalha em DUAS FASES!**\n"
            "1️⃣ Derrota a forma `???` (não podes capturá-la)\n"
            "2️⃣ Enfrenta então o verdadeiro **Leonking** — O Rei dos Deuses\n\n"
            f"❤️ HP: **{fmt_num(final['hp'])}**  ·  ⚔️ ATK: **{fmt_num(final['atk'])}**"
        ),
        color=0xff00ff,
    )
    em.set_footer(text="💡 Usa 🛡️ Defender quando vires o aviso de ataque especial!")
    await interaction.response.send_message(embed=em)
    await interaction.followup.send(embed=embed_boss(data, "A batalha começa!"), view=BossView(uid))


@tree.command(name="trocar", description="Troca um monstro entre equipa e box.")
@app_commands.describe(acao="enviar (equipa→box) ou trazer (box→equipa)", nome="Nome da espécie")
async def cmd_trocar(interaction: discord.Interaction, acao: str, nome: str):
    uid = interaction.user.id
    data = load_save(uid)
    acao = acao.lower()
    if acao not in ("enviar", "trazer"):
        await interaction.response.send_message("❌ Usa `enviar` ou `trazer`.", ephemeral=True)
        return
    if acao == "enviar":
        team = data.get("team", [])
        idx = next((i for i, m in enumerate(team) if m.get("species", "").lower() == nome.lower()), -1)
        if idx < 0:
            await interaction.response.send_message("❌ Não encontrado na equipa.", ephemeral=True)
            return
        mon = team.pop(idx)
        data["box"].append(mon)
        if data.get("activeMonId") == mon["id"] and team:
            data["activeMonId"] = team[0]["id"]
        write_save(uid, data)
        await interaction.response.send_message(
            f"📦 {mon['e']} **{mon.get('species', '?')}** enviado para a Box.", ephemeral=True
        )
    else:
        if len(data.get("team", [])) >= 6:
            await interaction.response.send_message("❌ Equipa cheia (6/6).", ephemeral=True)
            return
        box = data.get("box", [])
        idx = next((i for i, m in enumerate(box) if m.get("species", "").lower() == nome.lower()), -1)
        if idx < 0:
            await interaction.response.send_message("❌ Não encontrado na Box.", ephemeral=True)
            return
        mon = box.pop(idx)
        data["team"].append(mon)
        write_save(uid, data)
        await interaction.response.send_message(
            f"🎯 {mon['e']} **{mon.get('species', '?')}** trazido para a equipa!", ephemeral=True
        )


@tree.command(name="rebirth", description="Reinicia o progresso ganhando bónus permanente (custa 10.000 ouro).")
async def cmd_rebirth(interaction: discord.Interaction):
    uid = interaction.user.id
    data = load_save(uid)
    if data.get("gold", 0) < 10000:
        await interaction.response.send_message(
            "❌ Precisas de **10.000 ouro** para um Rebirth.", ephemeral=True
        )
        return
    rebirths = data.get("rebirthCount", 0) + 1
    new = default_save()
    new["rebirthCount"] = rebirths
    # Oferece starter novamente
    starters = [m for m in MONS if m["rare"] == "comum"]
    sp = random.choice(starters)
    starter = create_mon_from_species(sp, 1)
    # Bónus: +5 balls por rebirth
    new["balls"] = 5 + rebirths * 5
    new["team"].append(starter)
    new["activeMonId"] = starter["id"]
    new["nextMonId"] = 2
    new["caught"].append(sp["n"])
    write_save(uid, new)
    await interaction.response.send_message(
        f"🌀 **Rebirth #{rebirths}** completo!\n"
        f"Novo starter: {starter['e']} **{starter['species']}**\n"
        f"🔮 Balls iniciais: **{new['balls']}**", ephemeral=True
    )


@tree.command(name="ajuda", description="Lista todos os comandos e mecânicas.")
async def cmd_ajuda(interaction: discord.Interaction):
    em = discord.Embed(
        title="📘 Ajuda — Monster Hunter RPG",
        description="Caça monstros, derrota bosses e desbloqueia o **DEUS ABSOLUTO**!",
        color=0x5090e0,
    )
    em.add_field(
        name="🎮 Comandos principais",
        value=(
            "`/start` — começa a aventura\n"
            "`/cacar` — caça monstros selvagens\n"
            "`/boss [nome?]` — desafia um boss\n"
            "`/desafiar_final` — 🌌 **DEUS ABSOLUTO** (Pokédex completa)\n"
            "`/perfil`, `/equipa`, `/box`, `/pokedex`, `/bosses`\n"
            "`/ativar [pos]` — trocar monstro ativo\n"
            "`/curar [tipo]` — cura com poções\n"
            "`/usar [item]` — protein, heartseed, tiercore\n"
            "`/inventario`, `/loja`, `/comprar [id] [n]`\n"
            "`/trocar [enviar|trazer] [nome]` — equipa ⇄ box\n"
            "`/rebirth` — reinicia com bónus\n"
        ),
        inline=False,
    )
    em.add_field(
        name="⚔️ Mecânicas de Boss",
        value=(
            "⚔️ **Atacar** — dano normal com efectividade de tipo\n"
            "🛡️ **Defender** — reduz próximo dano a **40%** (essencial vs. ataques especiais)\n"
            "🔮 **Ball** — tenta capturar (cooldown **3 turnos**)\n"
            "💊 **Curar** — usa poções durante a batalha\n"
            "🛡️ **Escudo** — absorve 40% do próximo ataque\n"
            "🏃 **Fugir** — abandona a batalha\n\n"
            "⚠️ A cada **3 turnos** o boss carrega um **Ataque Especial** (x1.8)!\n"
            "🌀 Monstros **comuns** sofrem x2 dano, **incomuns** x1.5.\n"
            "📊 Bosses escalam com a força da tua equipa."
        ),
        inline=False,
    )
    em.add_field(
        name="🤫 Segredos",
        value=(
            "🐈 **Nico** — Usa 3 **Poções** no **OXIGÉNIO** para a invocar!\n"
            "👑 **Void King** — Só capturável com **Master Ball**\n"
            "🌌 **Boss Final (???)** — requer **Pokédex completa**\n"
            "🐐 **Leonking** — forma divina que aparece após ??? cair"
        ),
        inline=False,
    )
    em.set_footer(text="Boa caçada, caçador!")
    await interaction.response.send_message(embed=em, ephemeral=True)


# ══════════════════════════════════════════════════════════════
# EVENTOS
# ══════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    print(f"[bot] Ligado como {bot.user} (ID {bot.user.id})")
    try:
        synced = await tree.sync()
        print(f"[bot] {len(synced)} comandos sincronizados.")
    except Exception as e:
        print(f"[bot] Falha ao sincronizar: {e}")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit(
            "❌ DISCORD_TOKEN não definido. Copia `.env.example` para `.env` e coloca o teu token."
        )
    bot.run(TOKEN)

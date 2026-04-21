"""
Monster Hunter RPG - Discord Bot
Porta completa do jogo HTML para Discord usando discord.py com slash commands e botões.
"""

import discord
from discord.ext import commands
from discord import app_commands
import json, os, random, math, asyncio, time
from typing import Optional

# ══════════════════════════════════════════════
# DADOS DO JOGO (portados do HTML)
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
    {"t":"fogo",    "c":0xe2583d, "root":"Flama",  "mat":"Brasa",   "hpMod":0,   "atkMod":0,
     "names":["Flaminho","Labaréu","Brasalto","Fornalix","Tochino","Faíscor","Fogaréu","Pirólito","Chamego","Cinzal","Braseon","Magmário","Ardencor","Vulkar","Solferno"],
     "emojis":["🔥","🦊","🕯️","🐅","🏮","🧨","🐲","🍂","☄️","🦁","🎇","🌋","❤️‍🔥","🐦‍🔥","☀️"]},
    {"t":"água",    "c":0x3a92d9, "root":"Mar",    "mat":"Gota",    "hpMod":-1,  "atkMod":0,
     "names":["Marulhinho","Bolhudo","Aqualume","Mariscoz","Pingorim","Riachito","Mareco","Ondal","Nautelo","Aqualux","Tsuniko","Abissor","Maréon","Leviagota","Tidalux"],
     "emojis":["💧","🐟","🌊","🐠","🫧","🐸","🦦","💦","🦭","🐬","🦈","🐋","🌧️","🪸","🔱"]},
    {"t":"planta",  "c":0x4ea85f, "root":"Folha",  "mat":"Folha",   "hpMod":3,   "atkMod":-1,
     "names":["Brotinho","Ramalho","Trepiko","Verdelim","Mossito","Clorofim","Galhudo","Vinhedo","Botanix","Silvério","Selvar","Espinhaflor","Clorossauro","Floracel","Matrizal"],
     "emojis":["🌿","🍀","🪴","🌱","🍃","🌵","🌾","🌻","🌳","🍄","🌺","🪻","🌴","🌸","🌲"]},
    {"t":"terra",   "c":0x9b7b54, "root":"Pedra",  "mat":"Pedra",   "hpMod":8,   "atkMod":-2,
     "names":["Cascalho","Barrolho","Territo","Tremorim","Areíto","Pedrino","Lamosso","Sedento","Gravito","Monterro","Basalto","Colossalmo","Terragor","Pedrax","Titanterra"],
     "emojis":["🪨","🦔","🐗","🪵","🏜️","⛰️","🐢","🦬","🐘","🦏","🧱","🏔️","🗿","⚒️","🌍"]},
    {"t":"ar",      "c":0x80cde0, "root":"Vento",  "mat":"Pluma",   "hpMod":-3,  "atkMod":1,
     "names":["Assobinho","Névolo","Brisito","Volitro","Nublim","Aeral","Celsito","Ventor","Ciclar","Nebulon","Furavento","Aerólux","Tempespin","Estratelo","Skythar"],
     "emojis":["🪶","☁️","🕊️","🌬️","🪽","🪁","🎈","🦅","🌪️","🦉","🦤","🐦","🪂","🌫️","🚬"]},
    {"t":"gelo",    "c":0x77c9df, "root":"Gelo",   "mat":"Cristal", "hpMod":4,   "atkMod":1,
     "names":["Gelito","Nevisco","Frigelo","Branquim","Geadinho","Cristagel","Polarim","Nevon","Brisagel","Granizo","Gelágio","Glacialto","Cryonix","Nevastro","Zeroar"],
     "emojis":["❄️","⛄","🧊","🐧","🛷","🥶","🐻‍❄️","🏔️","🦣","🧤","🎿","⛸️","🍧","🐺","☃️"]},
    {"t":"trovão",  "c":0xe4c243, "root":"Raio",   "mat":"Faísca",  "hpMod":-2,  "atkMod":2,
     "names":["Raiolho","Choquito","Faíscudo","Pulsarim","Estaleco","Voltino","Troval","Neonchoque","Descargor","Eletrux","Tempestral","Raiotron","Fulminax","Arcozapp","Stormvolt"],
     "emojis":["⚡","🔋","🐹","💡","📻","💾","🦘","🌩️","📀","🔌","🚨","🪫","📱","🗜️","🥁"]},
    {"t":"sombra",  "c":0x5960b8, "root":"Sombra", "mat":"Essência","hpMod":-1,  "atkMod":3,
     "names":["Breuzinho","Sombralho","Ocultim","Vultito","Umbralim","Nocturo","Escurix","Véunegra","Tenebris","Mistumbrio","Abysmino","Sombrakar","Vaziurno","Crepux","Noxthar"],
     "emojis":["🌑","🦇","🐈‍⬛","🕳️","🕸️","🎩","♠️","🌘","🕷️","🖤","🌒","🥷","🌌","👁️","🎩"]},
    {"t":"cristal", "c":0x73cfe0, "root":"Cristal","mat":"Gema",    "hpMod":1,   "atkMod":2,
     "names":["Facetim","Brilhux","Vidrilho","Lúmino","Gemarim","Prismal","Reflexor","Cintilux","Quartzel","Luzcrist","Diamar","Shinério","Prismon","Glamyte","Luxórion"],
     "emojis":["💎","🪩","🔷","💠","🔮","💍","👑","🪞","🪩","🧂","🔹","🧿","🪙","🪬","❇️"]},
    {"t":"veneno",  "c":0x8e4ac2, "root":"Tóxico", "mat":"Toxina",  "hpMod":2,   "atkMod":1,
     "names":["Toxito","Peçonhudo","Bafumeio","Ácidim","Nocivo","Vaporoz","Miasmelo","Corrosix","Venomix","Biletor","Toxibras","Podrino","Morbax","Peçonrex","Nexovina"],
     "emojis":["☠️","🧪","🐍","🦂","🪱","🦠","🐌","🦨","🦎","🧫","☣️","🦟","🗑️","🧟","🪦"]},
    {"t":"som",     "c":0xff9ff3, "root":"Eco",    "mat":"Vibração","hpMod":-3,  "atkMod":4,
     "names":["Notinha","Apito","Vibrax","Ecoante","Resson","Sônico","Ressonância","Batida","Melódico","Grito","Harmon","Bumbo","Agudo","Sinfon","Ópera"],
     "emojis":["🎵","🔔","📣","🎼","🎷","🎸","🎹","🎺","🎻","🎙️","📻","🔉","🔈","🔇","🔊"]},
    {"t":"tempo",   "c":0x54a0ff, "root":"Cronos", "mat":"Engrenagem","hpMod":5, "atkMod":2,
     "names":["Tique","Toque","Ampulim","Relogito","Sécullus","Erax","Momentum","Pendor","Eterno","Cronix","Antigo","Futuro","Paradoxo","Zênite","Infinito"],
     "emojis":["⌛","⏳","⌚","⏰","🕰️","📅","📆","🗓️","🌀","⚙️","🔙","🔜","♾️","🗝️","🏛️"]},
    {"t":"luz",     "c":0xfeca57, "root":"Brilho", "mat":"Fóton",   "hpMod":2,   "atkMod":1,
     "names":["Faisquinha","Raioluz","Lume","Solaris","Claro","Aura","Relampo","Radiante","Glorioso","Cintilo","Ilumin","Candela","Facho","Prisma","Divino"],
     "emojis":["☀️","⭐","🌟","✨","🔦","💡","🕯️","🌕","🌅","🌤️","🎥","📸","🎐","🔆","👼"]},
    {"t":"cosmos",  "c":0x2e86de, "root":"Astro",  "mat":"Poeira Estelar","hpMod":0,"atkMod":6,
     "names":["Nebulino","Cometa","Orbital","Galaxico","Quasar","Pulzar","Sideral","Vácuo","Astro","Luneto","Solfar","Planeta","Constela","Zenit","Universo"],
     "emojis":["🌌","🪐","☄️","🛰️","🛸","🌑","🌘","🔭","🌌","☄️","🛸","🚀","👽","🛰️","🌠"]},
    {"t":"metal",   "c":0x95a5a6, "root":"Aço",    "mat":"Lingote", "hpMod":10,  "atkMod":0,
     "names":["Prequinho","Latão","Blindado","Chapa","Mecano","Tanque","Escudo","Lâmina","Broca","Titânio","Robusto","Cromo","Bigorna","Colosso","Muralha"],
     "emojis":["🔩","⚙️","⛓️","🗡️","🛡️","⚓","⚔️","⚒️","🛠️","⛏️","🚜","🏗️","🏢","🚄","🦾"]},
    {"t":"fantasma","c":0x9b59b6, "root":"Espectro","mat":"Ectoplasma","hpMod":-2,"atkMod":3,
     "names":["Fantasminha","Vaporzinho","Espectrim","Sombraluz","Aparião","Poltergeist","Etéreo","Wraitho","Spectrax","Bansheiro","Hauntelo","Phantomix","Espírito","Revenant","Necrovolt"],
     "emojis":["👻","🫥","💨","🌫️","👁️","🕯️","🪦","🕸️","🌒","🦴","💀","🪄","🌑","⛧","🔮"]},
    {"t":"dragão",  "c":0xc0392b, "root":"Dracônico","mat":"Escama","hpMod":6,   "atkMod":4,
     "names":["Drakoninho","Wyvernito","Serpelux","Ryudrak","Winguim","Dracozar","Fyrrex","Drakonis","Ignithorn","Scalethar","Clawmere","Draklord","Vyraxion","Nidragor","Dragonyx"],
     "emojis":["🐉","🦕","🦖","🐲","🔥","🌋","⚔️","🛡️","🌪️","🌊","⚡","❄️","☄️","💫","👑"]},
    {"t":"fada",    "c":0xff6eb4, "root":"Encanto","mat":"Pó de Fada","hpMod":0, "atkMod":2,
     "names":["Fadinhas","Encantura","Pixelim","Glitterix","Sparkelo","Lumiríx","Feerinha","Dazzlim","Wisping","Shimmerix","Blossomix","Glowette","Twinkling","Sprinklex","Celestira"],
     "emojis":["🧚","🌸","✨","🦋","🌺","🎀","💗","🌈","🪷","🌠","💖","🫧","🪻","🎆","🔮"]},
    {"t":"psíquico","c":0x8e44ad, "root":"Mental","mat":"Frag. Psíquico","hpMod":-1,"atkMod":4,
     "names":["Psiquim","Mentalis","Telepatix","Alucinex","Premonix","Clairix","Psivolt","Mindmere","Intuidor","Kinesis","Espatix","Telekin","Cognithor","Visionix","Omegamind"],
     "emojis":["🔮","🧠","👁️","🌀","💜","🪬","⭐","🌊","🎭","💭","🫀","🔵","🧿","💫","🌌"]},
    {"t":"luta",    "c":0xe74c3c, "root":"Golpe", "mat":"Fita de Treino","hpMod":2,"atkMod":5,
     "names":["Soqinho","Pontapelux","Upperim","Jabhero","Kombatik","Rushador","Strikelux","Grapplino","Punchix","Kicker","Kickzilla","Sluggerax","Brutegor","Ironknuckle","Ultimapunch"],
     "emojis":["👊","🥊","🥋","🤼","💪","🦵","🦶","⚡","🔥","🏋️","🤺","🥷","🏆","⚔️","💢"]},
    {"t":"inseto",  "c":0x27ae60, "root":"Quitina","mat":"Casulo",  "hpMod":1,   "atkMod":2,
     "names":["Lagartixa","Besourelo","Borbolim","Formigor","Escaravim","Gafanhotix","Larviço","Cocônix","Chrysalis","Antleon","Scarabeux","Beetlord","Mothwing","Mantidor","Hexapod"],
     "emojis":["🐛","🦋","🐝","🐜","🦗","🕷️","🐞","🪲","🪳","🦟","🦠","🌿","🍃","🌱","🪸"]},
    {"t":"néon",    "c":0x00ffcc, "root":"Néon",  "mat":"Plasma Néon","hpMod":-3,"atkMod":5,
     "names":["Néonix","Glitchim","Ciberlink","Pixelglow","Synthrix","Databit","Wireframe","Glowbyte","Circuitex","Lagzero","Flashnet","Hyperglow","Matrixter","Virtuelux","Cybercore"],
     "emojis":["🟢","💚","🔋","📡","💻","🖥️","📺","🎮","🕹️","🔌","📱","💾","🛜","🔆","⚡"]},
    {"t":"nuclear", "c":0xf39c12, "root":"Atômico","mat":"Urânio",  "hpMod":0,   "atkMod":6,
     "names":["Radiino","Atomillo","Nucléix","Fusionix","Fissurex","Radiotor","Halflifo","Decayix","Isótopo","Falloutix","Gammaray","Reatorix","Critimass","Meltorex","Nucleagor"],
     "emojis":["☢️","⚗️","💥","🔬","🧬","⚡","🌡️","🧪","💣","🔥","🌋","☄️","💫","🌀","🔶"]},
    {"t":"espírito","c":0x1abc9c, "root":"Alma",  "mat":"Essência Espiritual","hpMod":3,"atkMod":2,
     "names":["Alminha","Kamirix","Shintorix","Ancestrix","Espirix","Soulix","Totemix","Orixim","Blessor","Holyrim","Sacredix","Mantra","Divinix","Transcend","Enlighten"],
     "emojis":["🙏","⛩️","🎋","🪬","🔯","☯️","🕉️","✡️","🔱","⚜️","🪷","🌸","🌟","💫","👼"]},
    {"t":"mecânico","c":0x7f8c8d, "root":"Máquina","mat":"Peça Mecânica","hpMod":8,"atkMod":1,
     "names":["Robotinho","Automec","Dronix","Cogwheelx","Steamrix","Pistonix","Valvulor","Turbinix","Transmitor","Gearborg","Motorax","Clockwork","Steamborg","Technogor","Mekavolt"],
     "emojis":["🤖","⚙️","🔧","🔩","🛠️","🚜","🏗️","🚂","✈️","🚀","🛸","🦾","🦿","🧲","💡"]},
    {"t":"ventos",  "c":0x3498db, "root":"Tufão", "mat":"Redemoinho","hpMod":-2, "atkMod":3,
     "names":["Brisim","Tufarix","Zonalix","Cyclonix","Galerix","Tempestix","Twistix","Squallo","Zephyrion","Anemix","Typhonex","Sirocco","Mistral","Boreamix","Zondragor"],
     "emojis":["🌪️","🌀","💨","🌬️","🌊","⛵","🪁","🎑","🎐","☁️","🌩️","⛈️","🌧️","🌦️","🪂"]},
    {"t":"magma",   "c":0xe67e22, "root":"Magma", "mat":"Lava Solidificada","hpMod":5,"atkMod":3,
     "names":["Lavinha","Magmarim","Ignerix","Pyroclax","Emberlux","Calderon","Scorcherix","Infernix","Lavabeast","Moltenix","Cinder","Eruption","Volcanus","Firestorm","Magmarex"],
     "emojis":["🌋","🔥","💥","🧱","🏔️","☄️","🫧","🌡️","⚗️","🔶","🟠","🟤","🫁","🪨","⛏️"]},
    {"t":"arcano",  "c":0x8e44ad, "root":"Arcanjo","mat":"Cristal Arcano","hpMod":1,"atkMod":5,
     "names":["Arcalix","Rúnico","Spellrix","Glamorix","Hexamix","Grimora","Occultix","Witchix","Conjuror","Runeborn","Eldritch","Sorceron","Arcanix","Mystara","Sorceling"],
     "emojis":["🪄","✨","🔮","📖","🌙","⭐","💜","🎩","🃏","🪬","📜","🔯","🌀","💫","🧿"]},
]

TYPE_CHART = {
    "fogo":    {"adv":["gelo","planta"],        "dis":["terra","água"]},
    "água":    {"adv":["fogo","gelo"],          "dis":["planta","trovão"]},
    "planta":  {"adv":["água","terra"],         "dis":["fogo","veneno"]},
    "terra":   {"adv":["trovão","fogo"],        "dis":["planta","cristal"]},
    "ar":      {"adv":["veneno","sombra"],      "dis":["cosmos","metal"]},
    "gelo":    {"adv":["luz","veneno"],         "dis":["fogo","água"]},
    "trovão":  {"adv":["água","som"],           "dis":["terra","sombra"]},
    "sombra":  {"adv":["cosmos","trovão"],      "dis":["luz","ar"]},
    "cristal": {"adv":["terra","tempo"],        "dis":["som"]},
    "veneno":  {"adv":["planta","metal"],       "dis":["ar","gelo"]},
    "som":     {"adv":["cristal","metal"],      "dis":["cosmos","trovão"]},
    "luz":     {"adv":["tempo","sombra"],       "dis":["metal","gelo"]},
    "tempo":   {"adv":["cosmos","trovão"],      "dis":["luz","cristal"]},
    "metal":   {"adv":["luz","ar"],             "dis":["som","veneno"]},
    "cosmos":  {"adv":["ar","som"],             "dis":["tempo","sombra"]},
    "fantasma":{"adv":["psíquico","luta"],      "dis":["arcano","metal"]},
    "dragão":  {"adv":["metal","arcano"],       "dis":["gelo","fada"]},
    "fada":    {"adv":["dragão","luta"],        "dis":["veneno","metal"]},
    "psíquico":{"adv":["luta","fantasma"],      "dis":["sombra","inseto"]},
    "luta":    {"adv":["metal","gelo"],         "dis":["fada","psíquico"]},
    "inseto":  {"adv":["psíquico","planta"],    "dis":["fogo","ar"]},
    "néon":    {"adv":["mecânico","sombra"],    "dis":["nuclear","arcano"]},
    "nuclear": {"adv":["néon","inseto"],        "dis":["espírito","terra"]},
    "espírito":{"adv":["nuclear","sombra"],     "dis":["dragão","metal"]},
    "mecânico":{"adv":["ar","gelo"],            "dis":["néon","nuclear"]},
    "ventos":  {"adv":["inseto","fogo"],        "dis":["metal","terra"]},
    "magma":   {"adv":["gelo","terra"],         "dis":["água","ventos"]},
    "arcano":  {"adv":["fantasma","cosmos"],    "dis":["dragão","sombra"]},
}

BOSSES = [
    {"n":"Rei das Chamas",      "t":"fogo",    "e":"👹", "hp":1000,"atk":35,"reward":500,  "title":"Senhor do Inferno",       "mats":[{"n":"Coroa de Fogo","v":200}]},
    {"n":"Titã dos Mares",      "t":"água",    "e":"🐋", "hp":1400,"atk":30,"reward":600,  "title":"Leviatã Ancestral",       "mats":[{"n":"Escudo Abissal","v":200}]},
    {"n":"Lorde das Sombras",   "t":"sombra",  "e":"🌑", "hp":420, "atk":40,"reward":700,  "title":"Devorador de Almas",      "mats":[{"n":"Cristal Negro","v":200}]},
    {"n":"Maestro do Caos",     "t":"som",     "e":"🎻", "hp":1900,"atk":55,"reward":1600, "title":"O Regente do Silêncio",   "mats":[{"n":"Vibração","v":400}]},
    {"n":"Guardião das Eras",   "t":"tempo",   "e":"🕰️","hp":2400,"atk":40,"reward":1900, "title":"Aquele que Parou o Tempo","mats":[{"n":"Engrenagem","v":450}]},
    {"n":"Arcanjo Solar",       "t":"luz",     "e":"👼", "hp":2100,"atk":50,"reward":2500, "title":"O Esplendor do Meio-Dia", "mats":[{"n":"Fóton","v":500}]},
    {"n":"Vazio Estelar",       "t":"cosmos",  "e":"🕳️","hp":2600,"atk":65,"reward":3000, "title":"O Devorador de Galáxias", "mats":[{"n":"Poeira Estelar","v":550}]},
    {"n":"Leviatã de Ferro",    "t":"metal",   "e":"⛓️","hp":3800,"atk":35,"reward":2200, "title":"A Fortaleza Móvel",       "mats":[{"n":"Lingote","v":600}]},
    {"n":"Dragão do Apocalipse","t":"ar",      "e":"🐲", "hp":4000,"atk":45,"reward":900,  "title":"Fim dos Tempos",          "mats":[{"n":"Dente do Apocalipse","v":200}]},
    {"n":"DEUS DO CAOS",        "t":"veneno",  "e":"💀", "hp":6666,"atk":666,"reward":1500,"title":"O Inominável",            "mats":[{"n":"Fragmento Divino","v":200}]},
    {"n":"Void King",           "t":"cristal", "e":"👑", "hp":5800,"atk":1000,"reward":1200,"title":"Rei do Vazio",           "mats":[{"n":"Coroa do Vazio","v":2000}],"special":"master_only"},
    {"n":"Entidade Verdejante", "t":"planta",  "e":"🌳", "hp":2200,"atk":38,"reward":1400, "title":"O Coração da Floresta",   "mats":[{"n":"Folha Ancestral","v":350}]},
    {"n":"Colosso da Montanha", "t":"terra",   "e":"🗿", "hp":3500,"atk":42,"reward":1600, "title":"O Guardião da Rocha",     "mats":[{"n":"Pedra Titânica","v":400}]},
    {"n":"Senhor dos Vendavais","t":"ar",      "e":"🌪️","hp":1900,"atk":48,"reward":1500, "title":"A Fúria do Céu",          "mats":[{"n":"Pluma da Tempestade","v":380}]},
    {"n":"Tirano Glacial",      "t":"gelo",    "e":"❄️", "hp":2800,"atk":36,"reward":1700, "title":"O Inverno Eterno",        "mats":[{"n":"Cristal Gélido","v":420}]},
    {"n":"Deus da Tempestade",  "t":"trovão",  "e":"⚡", "hp":2100,"atk":52,"reward":1800, "title":"O Arauto dos Céus",       "mats":[{"n":"Faísca Divina","v":450}]},
    {"n":"Mente Suprema",       "t":"psíquico","e":"🧠", "hp":1800,"atk":55,"reward":2000, "title":"O Oráculo Cósmico",       "mats":[{"n":"Frag. Psíquico","v":500}]},
    {"n":"Campeão Indomável",   "t":"luta",    "e":"👊", "hp":3000,"atk":50,"reward":1600, "title":"O Punho Inquebrável",     "mats":[{"n":"Fita Lendária","v":400}]},
    {"n":"Imperador dos Enxames","t":"inseto", "e":"🐝", "hp":1700,"atk":40,"reward":1400, "title":"A Colmeia Viva",          "mats":[{"n":"Casulo Real","v":350}]},
    {"n":"Soberano de Néon",    "t":"néon",    "e":"🟢", "hp":2000,"atk":54,"reward":2000, "title":"A Grade Digital",         "mats":[{"n":"Plasma Néon","v":500}]},
    {"n":"Entidade Radioativa", "t":"nuclear", "e":"☢️", "hp":3200,"atk":60,"reward":2200, "title":"O Núcleo Instável",       "mats":[{"n":"Urânio Puro","v":550}]},
    {"n":"Ancestral Sagrado",   "t":"espírito","e":"🙏", "hp":2300,"atk":44,"reward":1800, "title":"A Voz dos Antigos",       "mats":[{"n":"Essência Espiritual","v":450}]},
    {"n":"Engenheiro do Caos",  "t":"mecânico","e":"🤖", "hp":4000,"atk":46,"reward":2100, "title":"A Máquina Perfeita",      "mats":[{"n":"Peça Mecânica Lendária","v":520}]},
    {"n":"Senhor do Magma",     "t":"magma",   "e":"🌋", "hp":3600,"atk":48,"reward":2000, "title":"O Coração da Terra",      "mats":[{"n":"Lava Solidificada","v":500}]},
    {"n":"Mestre Arcano",       "t":"arcano",  "e":"🔮", "hp":2500,"atk":56,"reward":2300, "title":"O Guardião dos Segredos", "mats":[{"n":"Cristal Arcano","v":600}]},
    {"n":"Espectro do Vazio",   "t":"fantasma","e":"👻", "hp":1500,"atk":58,"reward":1900, "title":"A Alma Perdida",          "mats":[{"n":"Ectoplasma","v":480}]},
    {"n":"Dragão Primordial",   "t":"dragão",  "e":"🐉", "hp":5000,"atk":70,"reward":3000, "title":"O Primeiro dos Dragões",  "mats":[{"n":"Escama Ancestral","v":800}]},
    {"n":"Rainha das Fadas",    "t":"fada",    "e":"🧚", "hp":1600,"atk":42,"reward":1700, "title":"A Protetora dos Reinos",  "mats":[{"n":"Pó de Fada","v":420}]},
    {"n":"Nico",                "t":"fofa",    "e":"🐈", "hp":1500,"atk":150,"reward":5000, "title":"A Destruidora de Mundos","mats":[{"n":"Pelo Cósmico","v":999}],"special":"nico"},
]

SHOP_ITEMS = [
    {"id":"superball",  "n":"Super Ball",       "e":"🔵","desc":"Ball +15% captura",              "price":40},
    {"id":"ultraball",  "n":"Ultra Ball",       "e":"🟣","desc":"Ball +25% captura",              "price":90},
    {"id":"masterball", "n":"Master Ball",      "e":"⭐","desc":"Captura garantida (1x)",         "price":220},
    {"id":"potion",     "n":"Poção",            "e":"🧪","desc":"Cura 60 HP",                     "price":25},
    {"id":"superpotion","n":"Super Poção",      "e":"💚","desc":"Cura 150 HP",                    "price":70},
    {"id":"megapotion", "n":"Mega Poção",       "e":"💊","desc":"Cura 50% do HP máximo",          "price":120},
    {"id":"revive",     "n":"Revive",           "e":"❤️","desc":"Revive com 75% HP",             "price":120},
    {"id":"maxrevive",  "n":"Max Revive",       "e":"💖","desc":"Revive com HP total",            "price":280},
    {"id":"protein",    "n":"Proteína",         "e":"💪","desc":"+10 ATK permanente",             "price":95},
    {"id":"heartseed",  "n":"Heart Seed",       "e":"🌱","desc":"+10 HP permanente",             "price":95},
    {"id":"tiercore",   "n":"Tier Core",        "e":"🔺","desc":"+1 Tier no monstro ativo",      "price":500},
    {"id":"charm",      "n":"Amuleto",          "e":"🍀","desc":"+drops materiais (passivo)",     "price":60},
    {"id":"xatk",       "n":"X-Ataque",         "e":"💢","desc":"+60% dano no próximo ataque",   "price":20},
    {"id":"balls5",     "n":"Pack Balls",       "e":"🔮","desc":"+5 Monster Balls",              "price":35},
    {"id":"shield",     "n":"Escudo Mágico",    "e":"🛡️","desc":"Absorve 40% dano boss (1x)",   "price":80},
    {"id":"ritual",     "n":"Ritual Boss",      "e":"🕯️","desc":"Convoca um boss",              "price":180},
    {"id":"raredecoy",  "n":"Isco Raro",        "e":"🧲","desc":"Força spawn Raro+ (1x)",        "price":250},
    {"id":"epicdecoy",  "n":"Isco Épico",       "e":"💎","desc":"Força spawn Épico+ (1x)",       "price":500},
    {"id":"goldenball", "n":"Golden Ball",      "e":"🌟","desc":"+60% captura, quebra se falha", "price":350},
    {"id":"megaincense","n":"Mega Incenso",     "e":"🌺","desc":"+300% raros por 30s",           "price":400},
    {"id":"raredecoy",  "n":"Isco Raro",        "e":"🧲","desc":"Força monstro Raro+",           "price":250},
]

RARE_COLOR = {
    "comum":    0x888888,
    "incomum":  0x50c050,
    "raro":     0x5090e0,
    "épico":    0xa050e0,
    "lendário": 0xe0a020,
    "mítico":   0xff4080,
    "divino":   0xffd700,
    "Divino":   0xffd700,
    "boss":     0xff0000,
}

RANK_INFO = [
    (10000,"MESTRE",    "👑", 0xff00ff),
    (8000, "JEDI",      "🟢", 0x00ff00),
    (7000, "RADIOATIVO","☢️", 0xffaa00),
    (6000, "DIAMANTE",  "💎", 0x5bc0de),
    (5000, "PLATINA",   "🔷", 0xa29bfe),
    (4000, "OURO",      "🥇", 0xffd700),
    (3000, "PRATA",     "🥈", 0xbdc3c7),
    (2000, "BRONZE",    "🥉", 0xcd7f32),
    (1000, "MADEIRA",   "🪵", 0x8B4513),
    (0,    "PLÁSTICO",  "♻️", 0x95a5a6),
]

# ══════════════════════════════════════════════
# FUNÇÕES DO JOGO
# ══════════════════════════════════════════════

def build_mons():
    mons = []
    for td in TYPE_DEFS:
        for i, plan in enumerate(RARITY_PLAN):
            if i < len(td["names"]):
                mons.append({
                    "n": td["names"][i],
                    "e": td["emojis"][i % len(td["emojis"])],
                    "t": td["t"],
                    "c": td["c"],
                    "r": plan["catch"],
                    "hp": max(1, plan["hp"] + td["hpMod"]),
                    "atk": max(1, plan["atk"] + td["atkMod"]),
                    "mats": [{"n": f"{td['mat']} {td['t']}", "v": plan["mat"]}],
                    "rare": plan["rare"],
                })
    # Especiais divinos
    mons += [
        {"n":"OXIGÉNIO",    "e":"💨","t":"Ar",      "c":0xaae0ff,"r":0.05,"hp":95,"atk":88,"mats":[{"n":"02","v":130}],"rare":"divino"},
        {"n":"Ciclone-Rei", "e":"🌀","t":"caos",    "c":0x6b44d9,"r":0.06,"hp":122,"atk":28,"mats":[{"n":"Olho do Caos","v":120}],"rare":"Divino"},
        {"n":"DEUS-DRAGÃO", "e":"🐲","t":"absoluto","c":0xffd700,"r":0.06,"hp":165,"atk":33,"mats":[{"n":"Alma do Dragão","v":160}],"rare":"Divino"},
    ]
    return mons

MONS = build_mons()
MON_INDEX = {m["n"]: m for m in MONS}
BOSS_INDEX = {b["n"]: b for b in BOSSES}

def xp_need(level):
    return max(10, int(10 * (level ** 1.4)))

def tier_roll(rare):
    weights = {"comum":[50,30,15,4,1],"incomum":[35,35,20,8,2],"raro":[20,30,30,15,5],
               "épico":[10,20,30,30,10],"lendário":[5,10,20,35,30],"mítico":[2,5,15,28,50],
               "divino":[1,2,8,19,70],"Divino":[1,2,8,19,70],"boss":[0,0,0,0,100]}
    w = weights.get(rare, [40,30,20,8,2])
    roll = random.randint(1,100)
    cum = 0
    for i, ww in enumerate(w):
        cum += ww
        if roll <= cum:
            return i + 1
    return 1

def tier_mult(tier):
    return [1.0, 1.3, 1.7, 2.2, 3.0][min(tier-1, 4)]

def refresh_mon_stats(mon):
    sp = MON_INDEX.get(mon["species"], BOSS_INDEX.get(mon["species"], {}))
    base_hp = mon.get("baseHp") or sp.get("hp", 20)
    base_atk = mon.get("baseAtk") or sp.get("atk", 5)
    lv = mon.get("level", 1)
    tier = mon.get("tier", 1)
    tm = tier_mult(tier)
    mon["maxHp"] = max(1, int((base_hp + lv * 2.5 + mon.get("hpBoost", 0)) * tm))
    mon["atkStat"] = max(1, int((base_atk + lv * 1.5 + mon.get("atkBoost", 0)) * tm))
    mon["hp"] = min(mon.get("hp", mon["maxHp"]), mon["maxHp"])

def get_type_mult(atk_type, def_type):
    info = TYPE_CHART.get(atk_type, {})
    if def_type in info.get("adv", []):
        return 1.5
    if def_type in info.get("dis", []):
        return 0.67
    return 1.0

def get_rank_info(elo):
    for threshold, label, icon, color in RANK_INFO:
        if elo >= threshold:
            return {"label": label, "icon": icon, "color": color}
    return {"label": "PLÁSTICO", "icon": "♻️", "color": 0x95a5a6}

def generate_wild_mon(forced_rarity=None, forced_type=None):
    if forced_rarity:
        rarities = ["comum","incomum","raro","épico","lendário","mítico","divino"]
        min_idx = rarities.index(forced_rarity) if forced_rarity in rarities else 0
        eligible = [p for p in RARITY_PLAN if rarities.index(p["rare"]) >= min_idx]
        plan = random.choice(eligible) if eligible else random.choice(RARITY_PLAN)
    else:
        roll = random.random() * 100
        if roll < 70:    plan = RARITY_PLAN[random.randint(0,2)]
        elif roll < 90:  plan = RARITY_PLAN[random.randint(3,5)]
        elif roll < 97:  plan = RARITY_PLAN[random.randint(6,8)]
        elif roll < 99:  plan = RARITY_PLAN[random.randint(9,10)]
        else:            plan = RARITY_PLAN[random.randint(11,14)]

    if forced_type:
        td = next((t for t in TYPE_DEFS if t["t"] == forced_type), None)
    else:
        td = random.choice(TYPE_DEFS)

    if not td:
        td = random.choice(TYPE_DEFS)

    idx = RARITY_PLAN.index(plan)
    name = td["names"][min(idx, len(td["names"])-1)]
    emoji = td["emojis"][random.randint(0, len(td["emojis"])-1)]

    return {
        "n": name,
        "t": td["t"],
        "e": emoji,
        "r": plan["rare"],
        "hp": max(1, plan["hp"] + td["hpMod"]),
        "maxHp": max(1, plan["hp"] + td["hpMod"]),
        "atk": max(1, plan["atk"] + td["atkMod"]),
        "catch": plan["catch"],
        "rare": plan["rare"],
        "color": td["c"],
    }

def get_catch_chance(wild_mon, player_data, using_golden=False):
    base = wild_mon.get("catch", 0.5)
    # Penalidade por nível alto da equipa
    team = player_data.get("team", [])
    max_lv = max((m.get("level",1) for m in team), default=1)
    penalty = max(0, (max_lv - 10) * 0.005)
    # Bónus de batalha
    battle_bonus = player_data.get("battleBonus", 0)
    catch_bonus = player_data.get("catchBonus", 0)
    total = min(0.97, base + battle_bonus + catch_bonus - penalty)
    if using_golden:
        total = min(0.97, total + 0.60)
    return max(0.01, total)

# ══════════════════════════════════════════════
# PERSISTÊNCIA (JSON por utilizador)
# ══════════════════════════════════════════════

SAVE_DIR = "saves"
os.makedirs(SAVE_DIR, exist_ok=True)

def save_path(uid):
    return os.path.join(SAVE_DIR, f"{uid}.json")

def default_save():
    return {
        "gold": 0, "balls": 10, "masterball": 0,
        "items": {}, "materials": {}, "caught": [], "bossDefeated": [],
        "team": [], "box": [], "activeMonId": None, "nextMonId": 1,
        "catchBonus": 0, "battleBonus": 0, "matBonus": 0,
        "wild": None,  # monstro selvagem atual
        "inBattle": False, "inBossBattle": False,
        "boss": None, "bossHp": 0, "bossMaxHp": 0,
        "playerHp": 100, "playerMaxHp": 100,
        "defending": False, "bossShield": 0,
        "ritualStock": 0, "xatkActive": False,
        "rankedElo": 1200, "rankedWins": 0, "rankedLosses": 0,
        "playerName": None, "playerId": None,
        "friendScores": {},
        "achievements": {},
        "rebirthCount": 0,
        "level": 1, "battles": 0,
        "forcedRarity": None, "forcedType": None,
    }

def load_save(uid):
    p = save_path(uid)
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                raw = f.read().strip()
            if not raw:
                raise ValueError("ficheiro vazio")
            data = json.loads(raw)
            d = default_save()
            d.update(data)
            return d
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Save corrompido para {uid}: {e} — a criar novo save")
            backup = p + ".corrupted"
            try:
                os.rename(p, backup)
            except Exception:
                pass
    return default_save()

def write_save(uid, data):
    p = save_path(uid)
    tmp = p + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, p)
    except Exception as e:
        print(f"Erro ao guardar save de {uid}: {e}")
        try:
            os.remove(tmp)
        except Exception:
            pass

def get_active_mon(data):
    aid = data.get("activeMonId")
    for m in data.get("team", []):
        if m.get("id") == aid:
            return m
    if data["team"]:
        return data["team"][0]
    return None

# ══════════════════════════════════════════════
# BOT DISCORD
# ══════════════════════════════════════════════

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ══════════════════════════════════════════════
# VIEWS (Botões Interativos)
# ══════════════════════════════════════════════

class BattleView(discord.ui.View):
    def __init__(self, uid, wild_defeated=False, timeout=120):
        super().__init__(timeout=timeout)
        self.uid = uid
        if wild_defeated:
            for child in self.children:
                if getattr(child, "label", "") == "Lutar":
                    child.disabled = True

    def _end_battle(self, data):
        data["inBattle"] = False
        data["wild"] = None
        data["battleBonus"] = 0
        data["balls"] = min(99, data.get("balls", 0) + 2)

    async def _reload(self, interaction):
        data = load_save(self.uid)
        wild = data.get("wild")
        if not wild or not data.get("inBattle"):
            await interaction.response.edit_message(content="Sem batalha ativa. Usa /cacar.", embed=None, view=None)
            return None, None
        return data, wild

    @discord.ui.button(label="Lutar", emoji="\u2694\ufe0f", style=discord.ButtonStyle.danger, custom_id="fight")
    async def fight(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.uid:
            await interaction.response.send_message("Nao e a tua batalha!", ephemeral=True)
            return
        data, wild = await self._reload(interaction)
        if not data:
            return

        mon = get_active_mon(data)
        if not mon or not mon.get("alive", True):
            self._end_battle(data)
            write_save(self.uid, data)
            await interaction.response.edit_message(content="Todos os teus monstros estao KO! Usa /curar.", embed=None, view=None)
            return

        refresh_mon_stats(mon)
        atk = mon["atkStat"]
        mult = get_type_mult(mon.get("t", ""), wild.get("t", ""))
        if data.get("xatkActive"):
            atk = int(atk * 1.6)
            data["xatkActive"] = False

        dmg = max(1, int(atk * mult * random.uniform(0.85, 1.15)))
        wild["hp"] = max(0, wild["hp"] - dmg)
        data["battleBonus"] = min(0.55, data.get("battleBonus", 0) + 0.05)

        mult_txt = ""
        if mult > 1.2:
            mult_txt = " Super eficaz!"
        elif mult < 0.8:
            mult_txt = " Nao muito eficaz..."

        mon_name = mon.get("species", mon.get("n", "?"))
        msg_parts = [f"{mon.get('e','?')} **{mon_name}** atacou! Dano: **{dmg}**{mult_txt}"]

        if wild["hp"] <= 0:
            wild["hp"] = 0
            xp = max(5, int(wild.get("atk", 5) * 0.8 + random.randint(3, 8)))
            gainXp_data(mon, xp, data)
            data["battleBonus"] = min(0.65, data["battleBonus"] + 0.15)
            data["wild"] = wild
            write_save(self.uid, data)
            msg_parts.append(f"**{wild['n']}** foi derrotado! +{xp} XP")
            msg_parts.append("Usa Ball para capturar ou Fugir para sair.")
            bar = hp_bar(0.0)
            embed = make_wild_embed(wild, bar, "\n".join(msg_parts))
            await interaction.response.edit_message(embed=embed, view=BattleView(self.uid, wild_defeated=True))
            return

        enemy_dmg = max(1, int(wild.get("atk", 5) * random.uniform(0.7, 1.1)))
        mon["hp"] = max(0, mon["hp"] - enemy_dmg)
        msg_parts.append(f"{wild.get('e','?')} {wild['n']} contra-atacou: **-{enemy_dmg}**")

        if mon["hp"] == 0:
            mon["alive"] = False
            msg_parts.append(f"{mon.get('e','?')} **{mon_name}** desmaiou!")
            outros = [m for m in data.get("team", []) if m.get("alive", True) and m.get("id") != mon.get("id")]
            if outros:
                msg_parts.append(f"Ainda tens {len(outros)} monstro(s) vivo(s). Usa /ativar.")
            else:
                msg_parts.append("Todos os monstros KO. Usa /curar.")
            self._end_battle(data)
            write_save(self.uid, data)
            hp_pct = wild["hp"] / max(1, wild.get("maxHp", max(wild["hp"], 1)))
            bar = hp_bar(hp_pct)
            embed = make_wild_embed(wild, bar, "\n".join(msg_parts))
            await interaction.response.edit_message(embed=embed, view=None)
            return

        msg_parts.append(f"HP do teu monstro: **{mon['hp']}/{mon.get('maxHp','?')}**")
        data["wild"] = wild
        write_save(self.uid, data)
        hp_pct = wild["hp"] / max(1, wild.get("maxHp", wild["hp"]))
        bar = hp_bar(hp_pct)
        embed = make_wild_embed(wild, bar, "\n".join(msg_parts))
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Ball", emoji="\U0001f52e", style=discord.ButtonStyle.primary, custom_id="ball")
    async def ball(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.uid:
            await interaction.response.send_message("Nao e a tua batalha!", ephemeral=True)
            return
        data, wild = await self._reload(interaction)
        if not data:
            return
        if data.get("balls", 0) <= 0:
            await interaction.response.send_message("Sem Balls! Usa /loja.", ephemeral=True)
            return

        golden = data.get("items", {}).get("goldenball", 0) > 0
        chance = get_catch_chance(wild, data, using_golden=golden)
        if golden:
            data["items"]["goldenball"] -= 1
        data["balls"] -= 1

        if random.random() < chance:
            captured = capture_wild(wild, data)
            self._end_battle(data)
            if captured["n"] not in data["caught"]:
                data["caught"].append(captured["n"])
            write_save(self.uid, data)
            prefix = "Golden Ball! " if golden else ""
            embed = discord.Embed(
                title=f"{wild.get('e','?')} {wild['n']} Capturado!",
                description=(
                    prefix +
                    f"Tier: {captured['tier']} | HP: {captured['maxHp']} | ATK: {captured['atkStat']}\n"
                    f"Pokedex: {len(data['caught'])}/{len(MONS)} | Balls: {data['balls']}"
                ),
                color=RARE_COLOR.get(wild.get("rare", "comum"), 0x888888)
            )
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            msgs = ["Quase!", "Escapou!", "Muito rapido!", "Muito forte!"]
            msg = "Golden Ball falhou!" if golden else random.choice(msgs)
            write_save(self.uid, data)
            hp_pct = wild["hp"] / max(1, wild.get("maxHp", wild["hp"]))
            embed = make_wild_embed(wild, hp_bar(hp_pct), f"{msg} | Chance: {int(chance*100)}% | Balls: {data['balls']}")
            await interaction.response.edit_message(embed=embed, view=BattleView(self.uid, wild_defeated=(wild["hp"] <= 0)))

    @discord.ui.button(label="Fugir", emoji="\U0001f3c3", style=discord.ButtonStyle.secondary, custom_id="flee")
    async def flee(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.uid:
            await interaction.response.send_message("Nao e a tua batalha!", ephemeral=True)
            return
        data = load_save(self.uid)
        self._end_battle(data)
        write_save(self.uid, data)
        await interaction.response.edit_message(content=f"Fugiste! Balls: {data['balls']}", embed=None, view=None)

    @discord.ui.button(label="Master Ball", emoji="\u2b50", style=discord.ButtonStyle.success, custom_id="masterball")
    async def masterball_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.uid:
            await interaction.response.send_message("Nao e a tua batalha!", ephemeral=True)
            return
        data, wild = await self._reload(interaction)
        if not data:
            return
        if data.get("masterball", 0) <= 0:
            await interaction.response.send_message("Sem Master Ball! Compra em /loja.", ephemeral=True)
            return
        data["masterball"] -= 1
        captured = capture_wild(wild, data)
        self._end_battle(data)
        if captured["n"] not in data["caught"]:
            data["caught"].append(captured["n"])
        write_save(self.uid, data)
        embed = discord.Embed(
            title=f"{wild.get('e','?')} {wild['n']} Capturado com Master Ball!",
            description=(
                f"Captura garantida!\n"
                f"Tier: {captured['tier']} | HP: {captured['maxHp']} | ATK: {captured['atkStat']}\n"
                f"Pokedex: {len(data['caught'])}/{len(MONS)}"
            ),
            color=0xffd700
        )
        await interaction.response.edit_message(embed=embed, view=None)

    async def on_timeout(self):
        try:
            data = load_save(self.uid)
            if data.get("inBattle"):
                self._end_battle(data)
                write_save(self.uid, data)
        except Exception:
            pass

class BossView(discord.ui.View):
    """Botões da batalha de Boss."""
    def __init__(self, uid, timeout=300):
        super().__init__(timeout=timeout)
        self.uid = uid

    async def _reload(self, interaction):
        data = load_save(self.uid)
        if not data.get("inBossBattle") or not data.get("boss"):
            await interaction.response.edit_message(content="❌ Sem batalha de boss ativa.", embed=None, view=None)
            return None
        return data

    @discord.ui.button(label="⚔️ Atacar", style=discord.ButtonStyle.danger)
    async def boss_attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.uid:
            await interaction.response.send_message("❌ Não é a tua batalha!", ephemeral=True); return
        data = await self._reload(interaction)
        if not data: return

        mon = data.get("playerMon") or get_active_mon(data)
        if not mon:
            await interaction.response.send_message("❌ Sem monstro ativo!", ephemeral=True); return

        refresh_mon_stats(mon)
        boss = data["boss"]
        atk = mon["atkStat"]
        mult = get_type_mult(mon.get("t",""), boss.get("t",""))
        if data.get("xatkActive"):
            atk = int(atk * 1.6)
            data["xatkActive"] = False

        dmg = max(1, int(atk * mult * random.uniform(0.8, 1.2)))
        data["bossHp"] = max(0, data["bossHp"] - dmg)
        data["defending"] = False

        mult_txt = ""
        if mult > 1: mult_txt = " ⚡ Super eficaz!"
        elif mult < 1: mult_txt = " 💧 Não muito eficaz..."

        lines = [f"**{mon['e']} {mon.get('species', mon.get('n','?'))}** atacou o boss! Dano: **{dmg}**{mult_txt}"]

        if data["bossHp"] <= 0:
            # Boss derrotado
            data["bossHp"] = 0
            data["inBossBattle"] = False
            boss_name = boss["n"]
            if boss_name not in data["bossDefeated"]:
                data["bossDefeated"].append(boss_name)
            reward = boss.get("reward", 500)
            data["gold"] = data.get("gold", 0) + reward
            for mat in boss.get("mats", []):
                nm = mat["n"]
                data["materials"][nm] = data["materials"].get(nm, 0) + 1
            gainXp_data(mon, 60, data)
            write_save(self.uid, data)
            embed = discord.Embed(
                title=f"🏆 {boss['e']} {boss['n']} Derrotado!",
                description=f"**Recompensa:** 💰{reward}\n**Bosses derrotados:** {len(data['bossDefeated'])}\n{chr(10).join(lines)}",
                color=0xffd700
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return
        else:
            # Boss contra-ataca
            boss_dmg = max(1, int(boss["atk"] * random.uniform(0.7, 1.2)))
            if data.get("bossShield", 0) > 0:
                absorbed = int(boss_dmg * 0.4)
                boss_dmg -= absorbed
                data["bossShield"] -= 1
                lines.append(f"🛡️ Escudo absorveu {absorbed} dano!")
            data["playerHp"] = max(0, data.get("playerHp", 100) - boss_dmg)
            lines.append(f"👹 {boss['e']} {boss['n']} atacou! Dano: -{boss_dmg}")
            lines.append(f"❤️ O teu HP: {data['playerHp']}/{data.get('playerMaxHp',100)}")

            if data["playerHp"] <= 0:
                data["inBossBattle"] = False
                penalty = int(data.get("gold", 0) * 0.1)
                data["gold"] = max(0, data.get("gold",0) - penalty)
                lines.append(f"\n💀 Foste derrotado! Perdeste 💰{penalty}")
                write_save(self.uid, data)
                embed = discord.Embed(title="💀 Derrota contra o Boss", description="\n".join(lines), color=0xe03030)
                await interaction.response.edit_message(embed=embed, view=None)
                return

        write_save(self.uid, data)
        embed = make_boss_embed(data, "\n".join(lines))
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🛡️ Defender", style=discord.ButtonStyle.secondary)
    async def boss_defend(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.uid:
            await interaction.response.send_message("❌ Não é a tua batalha!", ephemeral=True); return
        data = await self._reload(interaction)
        if not data: return

        data["defending"] = True
        boss = data["boss"]
        boss_dmg = max(1, int(boss["atk"] * random.uniform(0.3, 0.6)))  # 30-60% dano ao defender
        data["playerHp"] = max(0, data.get("playerHp", 100) - boss_dmg)

        msg = f"🛡️ Defendeste! Dano reduzido: -{boss_dmg}\n❤️ HP: {data['playerHp']}/{data.get('playerMaxHp',100)}"

        if data["playerHp"] <= 0:
            data["inBossBattle"] = False
            penalty = int(data.get("gold",0) * 0.1)
            data["gold"] = max(0, data.get("gold",0) - penalty)
            msg += f"\n💀 Foste derrotado! Perdeste 💰{penalty}"
            write_save(self.uid, data)
            embed = discord.Embed(title="💀 Derrota contra o Boss", description=msg, color=0xe03030)
            await interaction.response.edit_message(embed=embed, view=None)
            return

        write_save(self.uid, data)
        embed = make_boss_embed(data, msg)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔮 Tentar Capturar", style=discord.ButtonStyle.primary)
    async def boss_catch(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.uid:
            await interaction.response.send_message("❌ Não é a tua batalha!", ephemeral=True); return
        data = await self._reload(interaction)
        if not data: return

        boss = data["boss"]
        if boss.get("special") == "master_only":
            if data.get("masterball", 0) <= 0:
                await interaction.response.send_message("👑 Void King só pode ser capturado com Master Ball!", ephemeral=True); return
            data["masterball"] -= 1
        elif data.get("balls", 0) <= 0:
            await interaction.response.send_message("❌ Sem Balls!", ephemeral=True); return
        else:
            data["balls"] -= 1

        hp_ratio = data["bossHp"] / max(1, data["bossMaxHp"])
        catch_chance = 0.15
        if hp_ratio <= 0.5: catch_chance += 0.10
        if data.get("defending"): catch_chance += 0.05

        if random.random() < catch_chance:
            data["inBossBattle"] = False
            boss_name = boss["n"]
            if boss_name not in data["bossDefeated"]:
                data["bossDefeated"].append(boss_name)
            # Adicionar boss como monstro
            boss_mon = {
                "id": data["nextMonId"], "species": boss["n"], "n": boss["n"],
                "e": boss["e"], "t": "boss", "c": boss.get("c", 0xffd700),
                "level": 50, "tier": 5, "hp": data["bossMaxHp"],
                "maxHp": data["bossMaxHp"], "atkStat": boss["atk"],
                "hpBoost": 0, "atkBoost": 0, "alive": True, "isBoss": True,
                "baseHp": data["bossMaxHp"], "baseAtk": boss["atk"],
            }
            data["nextMonId"] += 1
            if len(data.get("team",[])) < 6:
                data["team"].append(boss_mon)
            else:
                data["box"].append(boss_mon)
            data["gold"] = data.get("gold",0) + boss.get("reward",500)
            write_save(self.uid, data)
            embed = discord.Embed(
                title=f"✨ {boss['e']} {boss['n']} CAPTURADO!",
                description=f"Boss adicionado à tua equipa/box!\n💰 +{boss.get('reward',500)} gold",
                color=0xffd700
            )
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            write_save(self.uid, data)
            embed = make_boss_embed(data, f"🌀 Ball falhou! ({int(catch_chance*100)}% de chance)\nBalls: {data.get('balls',0)}")
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🏃 Retirar", style=discord.ButtonStyle.danger, row=1)
    async def boss_retreat(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.uid:
            await interaction.response.send_message("❌ Não é a tua batalha!", ephemeral=True); return
        data = load_save(self.uid)
        data["inBossBattle"] = False
        data["boss"] = None
        write_save(self.uid, data)
        await interaction.response.edit_message(content="🏃 Recuaste da batalha com o Boss!", embed=None, view=None)


class ShopView(discord.ui.View):
    def __init__(self, uid, page=0):
        super().__init__(timeout=60)
        self.uid = uid
        self.page = page
        self._update_buttons()

    def _update_buttons(self):
        self.clear_items()
        items_per_page = 5
        start = self.page * items_per_page
        shown = SHOP_ITEMS[start:start+items_per_page]

        for item in shown:
            btn = discord.ui.Button(
                label=f"{item['e']} {item['n']} ({item['price']}💰)",
                style=discord.ButtonStyle.secondary,
                custom_id=f"buy_{item['id']}"
            )
            btn.callback = self._make_buy(item)
            self.add_item(btn)

        if self.page > 0:
            prev = discord.ui.Button(label="◀ Anterior", style=discord.ButtonStyle.primary, row=4)
            prev.callback = self._prev_page
            self.add_item(prev)

        if (self.page + 1) * items_per_page < len(SHOP_ITEMS):
            nxt = discord.ui.Button(label="▶ Próxima", style=discord.ButtonStyle.primary, row=4)
            nxt.callback = self._next_page
            self.add_item(nxt)

    def _make_buy(self, item):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.uid:
                await interaction.response.send_message("❌ Não é a tua loja!", ephemeral=True); return
            data = load_save(self.uid)
            if data.get("gold", 0) < item["price"]:
                await interaction.response.send_message(f"❌ Ouro insuficiente! Precisas de 💰{item['price']}.", ephemeral=True); return

            data["gold"] -= item["price"]
            iid = item["id"]

            if iid == "masterball":
                data["masterball"] = data.get("masterball", 0) + 1
            elif iid == "balls5":
                data["balls"] = min(99, data.get("balls", 0) + 5)
            elif iid == "charm":
                data["matBonus"] = min(3, data.get("matBonus", 0) + 1)
            elif iid == "ritual":
                data["ritualStock"] = min(3, data.get("ritualStock", 0) + 1)
            elif iid == "xatk":
                data["xatkActive"] = True
            elif iid == "shield":
                data["bossShield"] = min(1, data.get("bossShield", 0) + 1)
            else:
                data.setdefault("items", {})[iid] = data["items"].get(iid, 0) + 1

            write_save(self.uid, data)
            await interaction.response.send_message(f"✅ {item['e']} **{item['n']}** comprado! 💰 restantes: {data['gold']}", ephemeral=True)
        return callback

    async def _prev_page(self, interaction: discord.Interaction):
        self.page = max(0, self.page - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=make_shop_embed(self.page), view=self)

    async def _next_page(self, interaction: discord.Interaction):
        max_page = (len(SHOP_ITEMS) - 1) // 5
        self.page = min(max_page, self.page + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=make_shop_embed(self.page), view=self)


# ══════════════════════════════════════════════
# FUNÇÕES AUXILIARES DE EMBED
# ══════════════════════════════════════════════

def hp_bar(pct, length=10):
    filled = round(pct * length)
    bar = "█" * filled + "░" * (length - filled)
    if pct > 0.6:   color = "🟩"
    elif pct > 0.3: color = "🟨"
    else:           color = "🟥"
    return f"{color} `{bar}` {int(pct*100)}%"

def make_wild_embed(wild, bar, msg=""):
    rare = wild.get("rare", "comum")
    color = RARE_COLOR.get(rare, 0x888888)
    embed = discord.Embed(
        title=f"{wild['e']} {wild['n']}",
        description=msg or "Escolhe uma ação!",
        color=color
    )
    embed.add_field(name="Tipo", value=wild.get("t","?"), inline=True)
    embed.add_field(name="Raridade", value=rare.upper(), inline=True)
    embed.add_field(name="HP", value=bar, inline=False)
    embed.add_field(name="ATK", value=str(wild.get("atk", "?")), inline=True)
    return embed

def make_boss_embed(data, msg=""):
    boss = data.get("boss", {})
    hp_pct = data.get("bossHp", 0) / max(1, data.get("bossMaxHp", 1))
    bar = hp_bar(hp_pct)
    embed = discord.Embed(
        title=f"👹 Boss: {boss.get('e','')} {boss.get('n','?')}",
        description=msg or "Boss em batalha!",
        color=0x8a0020
    )
    embed.add_field(name="HP Boss", value=f"{bar}\n{data.get('bossHp',0)}/{data.get('bossMaxHp',1)}", inline=False)
    embed.add_field(name="HP Jogador", value=f"❤️ {data.get('playerHp',0)}/{data.get('playerMaxHp',100)}", inline=True)
    embed.add_field(name="ATK Boss", value=str(boss.get("atk","?")), inline=True)
    return embed

def make_shop_embed(page=0):
    items_per_page = 5
    start = page * items_per_page
    shown = SHOP_ITEMS[start:start+items_per_page]
    desc = "\n".join([f"**{i['e']} {i['n']}** — 💰{i['price']}\n*{i['desc']}*" for i in shown])
    embed = discord.Embed(title="🛒 Loja", description=desc, color=0xffd700)
    total = (len(SHOP_ITEMS)-1)//5+1
    embed.set_footer(text=f"Página {page+1}/{total}")
    return embed

# ══════════════════════════════════════════════
# FUNÇÕES DE JOGO
# ══════════════════════════════════════════════

def gainXp_data(mon, amount, data):
    mon["xp"] = mon.get("xp", 0) + amount
    leveled = False
    while mon["xp"] >= xp_need(mon.get("level",1)) and mon.get("level",1) < 1000:
        mon["xp"] -= xp_need(mon["level"])
        mon["level"] = mon.get("level",1) + 1
        leveled = True
    if leveled:
        refresh_mon_stats(mon)
        mon["hp"] = mon["maxHp"]
        mon["alive"] = True
    return leveled

def capture_wild(wild, data):
    sp = MON_INDEX.get(wild["n"], wild)
    captured = {
        "id": data.get("nextMonId", 1),
        "species": wild["n"],
        "n": wild["n"],
        "e": wild.get("e","❓"),
        "t": wild.get("t","?"),
        "level": max(1, data.get("level",1)),
        "xp": 0,
        "hp": wild.get("hp", 20),
        "maxHp": wild.get("hp", 20),
        "atkStat": wild.get("atk", 5),
        "hpBoost": 0, "atkBoost": 0,
        "alive": True,
        "tier": tier_roll(wild.get("rare","comum")),
        "baseHp": wild.get("hp", 20),
        "baseAtk": wild.get("atk", 5),
        "customBaseStats": True,
        "color": wild.get("color", 0x888888),
    }
    data["nextMonId"] = data.get("nextMonId",1) + 1
    refresh_mon_stats(captured)

    if not data.get("activeMonId"):
        data["activeMonId"] = captured["id"]

    if len(data.get("team",[])) < 6:
        data.setdefault("team",[]).append(captured)
    else:
        data.setdefault("box",[]).append(captured)

    # Materiais
    for mat in wild.get("mats", []):
        qty = 1 + (1 if data.get("matBonus",0) > 0 and random.random() < 0.4 else 0)
        data.setdefault("materials",{})[mat["n"]] = data["materials"].get(mat["n"],0) + qty

    # Ouro
    gold = max(5, int(6 + data.get("level",1)*3 + random.random()*10))
    data["gold"] = data.get("gold",0) + gold

    return captured

# ══════════════════════════════════════════════
# SLASH COMMANDS
# ══════════════════════════════════════════════

tree = bot.tree

@tree.command(name="cacar", description="Encontra um monstro selvagem para caçar!")
async def hunt(interaction: discord.Interaction):
    uid = interaction.user.id
    data = load_save(uid)

    if data.get("inBattle") or data.get("inBossBattle"):
        await interaction.response.send_message("⚔️ Já estás em batalha! Termina primeiro a batalha atual.", ephemeral=True); return

    wild = generate_wild_mon(
        forced_rarity=data.get("forcedRarity"),
        forced_type=data.get("forcedType")
    )
    wild["hp"] = wild["maxHp"] = wild["hp"]
    data["wild"] = wild
    data["inBattle"] = True
    data["battleBonus"] = 0
    data["forcedRarity"] = None
    data["forcedType"] = None
    write_save(uid, data)

    bar = hp_bar(1.0)
    embed = make_wild_embed(wild, bar, f"Um **{wild['n']}** apareceu! O que fazes?\n\n🔮 Balls: {data.get('balls',0)} | ⭐ Master: {data.get('masterball',0)}")
    view = BattleView(uid)
    await interaction.response.send_message(embed=embed, view=view)

@tree.command(name="equipa", description="Vê a tua equipa de monstros")
async def team_cmd(interaction: discord.Interaction):
    uid = interaction.user.id
    data = load_save(uid)
    team = data.get("team", [])

    if not team:
        await interaction.response.send_message("😔 Ainda não tens monstros! Usa `/cacar` para capturar o teu primeiro.", ephemeral=True); return

    embed = discord.Embed(title="🐾 A Tua Equipa", color=0xffd700)
    active_id = data.get("activeMonId")

    for mon in team:
        refresh_mon_stats(mon)
        sp_name = mon.get("species", mon.get("n","?"))
        active = "⭐ " if mon.get("id") == active_id else ""
        status = "😵 KO" if not mon.get("alive", True) else f"❤️ {mon['hp']}/{mon['maxHp']}"
        embed.add_field(
            name=f"{active}{mon.get('e','❓')} {sp_name}",
            value=f"Lv.**{mon.get('level',1)}** | Tier **{mon.get('tier',1)}**\n"
                  f"⚔️ ATK: {mon.get('atkStat','?')} | {status}\n"
                  f"Tipo: {mon.get('t','?')}",
            inline=True
        )

    embed.set_footer(text=f"💰 {data.get('gold',0)} | 🔮 {data.get('balls',0)} balls | Capturados: {len(data.get('caught',[]))}/{len(MONS)}")
    await interaction.response.send_message(embed=embed)

@tree.command(name="box", description="Vê a tua box de monstros")
async def box_cmd(interaction: discord.Interaction):
    uid = interaction.user.id
    data = load_save(uid)
    box = data.get("box", [])

    if not box:
        await interaction.response.send_message("📦 A tua box está vazia!", ephemeral=True); return

    embed = discord.Embed(title="📦 Box de Monstros", description=f"{len(box)} monstro(s) na box", color=0x5090e0)
    for mon in box[:20]:  # Mostrar max 20
        refresh_mon_stats(mon)
        sp_name = mon.get("species", mon.get("n","?"))
        embed.add_field(
            name=f"{mon.get('e','❓')} {sp_name}",
            value=f"Lv.{mon.get('level',1)} | T{mon.get('tier',1)} | ❤️{mon.get('maxHp','?')} ⚔️{mon.get('atkStat','?')}",
            inline=True
        )
    if len(box) > 20:
        embed.set_footer(text=f"Mostrando 20/{len(box)} monstros")
    await interaction.response.send_message(embed=embed)

@tree.command(name="ativar", description="Define o teu monstro ativo pelo número na equipa (1-6)")
@app_commands.describe(posicao="Posição na equipa (1-6)")
async def set_active(interaction: discord.Interaction, posicao: int):
    uid = interaction.user.id
    data = load_save(uid)
    team = data.get("team", [])

    if not 1 <= posicao <= len(team):
        await interaction.response.send_message(f"❌ Posição inválida. A tua equipa tem {len(team)} monstros.", ephemeral=True); return

    mon = team[posicao - 1]
    data["activeMonId"] = mon["id"]
    write_save(uid, data)
    refresh_mon_stats(mon)
    await interaction.response.send_message(f"✅ {mon.get('e','❓')} **{mon.get('species', mon.get('n','?'))}** definido como monstro ativo! (Lv.{mon.get('level',1)} | ATK:{mon.get('atkStat','?')} | HP:{mon.get('hp','?')}/{mon.get('maxHp','?')})")

@tree.command(name="curar", description="Cura o monstro ativo com uma poção")
@app_commands.describe(tipo="Tipo de poção: poção, superpoção, megapoção, revive, maxrevive")
async def heal(interaction: discord.Interaction, tipo: str = "poção"):
    uid = interaction.user.id
    data = load_save(uid)
    mon = get_active_mon(data)

    if not mon:
        await interaction.response.send_message("❌ Sem monstro ativo!", ephemeral=True); return

    mapa = {"poção":"potion","superpoção":"superpotion","megapoção":"megapotion","revive":"revive","maxrevive":"maxrevive"}
    item_id = mapa.get(tipo.lower(), "potion")
    items = data.get("items", {})

    if items.get(item_id, 0) <= 0:
        await interaction.response.send_message(f"❌ Sem **{tipo}** no inventário! Compra em `/loja`.", ephemeral=True); return

    refresh_mon_stats(mon)
    msg = ""
    if item_id == "potion":
        if mon.get("alive",True) and mon["hp"] < mon["maxHp"]:
            mon["hp"] = min(mon["maxHp"], mon["hp"] + 60)
            msg = f"🧪 Poção usada! +60 HP → {mon['hp']}/{mon['maxHp']}"
        else:
            await interaction.response.send_message("❌ Monstro já tem HP cheio ou está KO!", ephemeral=True); return
    elif item_id == "superpotion":
        if mon.get("alive",True) and mon["hp"] < mon["maxHp"]:
            mon["hp"] = min(mon["maxHp"], mon["hp"] + 150)
            msg = f"💚 Super Poção! +150 HP → {mon['hp']}/{mon['maxHp']}"
        else:
            await interaction.response.send_message("❌ Monstro já tem HP cheio ou está KO!", ephemeral=True); return
    elif item_id == "megapotion":
        if mon.get("alive",True) and mon["hp"] < mon["maxHp"]:
            heal_amount = int(mon["maxHp"] * 0.5)
            mon["hp"] = min(mon["maxHp"], mon["hp"] + heal_amount)
            msg = f"💊 Mega Poção! +{heal_amount} HP → {mon['hp']}/{mon['maxHp']}"
        else:
            await interaction.response.send_message("❌ Inválido!", ephemeral=True); return
    elif item_id == "revive":
        if not mon.get("alive", True):
            mon["hp"] = max(1, int(mon["maxHp"] * 0.75))
            mon["alive"] = True
            msg = f"❤️ Revive! {mon.get('e','')} {mon.get('species',mon.get('n','?'))} voltou com {mon['hp']}/{mon['maxHp']} HP"
        else:
            await interaction.response.send_message("❌ Monstro não está KO!", ephemeral=True); return
    elif item_id == "maxrevive":
        if not mon.get("alive", True):
            mon["hp"] = mon["maxHp"]
            mon["alive"] = True
            msg = f"💖 Max Revive! HP totalmente restaurado: {mon['hp']}/{mon['maxHp']}"
        else:
            await interaction.response.send_message("❌ Monstro não está KO!", ephemeral=True); return

    items[item_id] -= 1
    data["items"] = items
    write_save(uid, data)
    await interaction.response.send_message(msg)

@tree.command(name="inventario", description="Vê o teu inventário de itens e materiais")
async def inventory(interaction: discord.Interaction):
    uid = interaction.user.id
    data = load_save(uid)

    embed = discord.Embed(title="🎒 Inventário", color=0x5090e0)
    embed.add_field(name="💰 Ouro", value=str(data.get("gold",0)), inline=True)
    embed.add_field(name="🔮 Balls", value=str(data.get("balls",0)), inline=True)
    embed.add_field(name="⭐ Master Balls", value=str(data.get("masterball",0)), inline=True)

    items = data.get("items", {})
    item_map = {i["id"]: i for i in SHOP_ITEMS}
    item_lines = []
    for iid, qty in items.items():
        if qty > 0:
            info = item_map.get(iid, {"e":"📦","n":iid})
            item_lines.append(f"{info['e']} **{info['n']}**: x{qty}")
    if item_lines:
        embed.add_field(name="🧪 Itens", value="\n".join(item_lines), inline=False)
    else:
        embed.add_field(name="🧪 Itens", value="Nenhum item", inline=False)

    mats = data.get("materials", {})
    mat_lines = [f"**{k}**: x{v}" for k,v in list(mats.items())[:15] if v > 0]
    if mat_lines:
        embed.add_field(name="🪨 Materiais", value="\n".join(mat_lines), inline=False)

    await interaction.response.send_message(embed=embed)

@tree.command(name="loja", description="Abre a loja de itens")
async def shop(interaction: discord.Interaction):
    uid = interaction.user.id
    data = load_save(uid)
    embed = make_shop_embed(0)
    embed.set_footer(text=f"💰 Tens {data.get('gold',0)} de ouro")
    view = ShopView(uid)
    await interaction.response.send_message(embed=embed, view=view)

@tree.command(name="pokedex", description="Vê a tua Pokédex de monstros capturados")
async def pokedex(interaction: discord.Interaction):
    uid = interaction.user.id
    data = load_save(uid)
    caught = data.get("caught", [])
    bosses = data.get("bossDefeated", [])
    total = len(MONS) + len(BOSSES)

    embed = discord.Embed(
        title=f"📖 Pokédex — {len(caught)}/{len(MONS)} monstros + {len(bosses)}/{len(BOSSES)} bosses",
        color=0xffd700
    )

    # Raridades capturadas
    from collections import Counter
    rarities = Counter()
    for nm in caught:
        sp = MON_INDEX.get(nm)
        if sp:
            rarities[sp.get("rare","?")] += 1

    lines = []
    for rare in ["comum","incomum","raro","épico","lendário","mítico","divino","Divino"]:
        count = rarities.get(rare, 0)
        if count > 0:
            lines.append(f"**{rare.upper()}**: {count}")
    if lines:
        embed.add_field(name="Por Raridade", value="\n".join(lines), inline=True)

    if bosses:
        embed.add_field(name="👹 Bosses Derrotados", value=", ".join(bosses[:10]) + ("..." if len(bosses)>10 else ""), inline=False)

    # Últimas capturas
    if caught:
        last5 = caught[-5:]
        last_names = []
        for nm in reversed(last5):
            sp = MON_INDEX.get(nm,{})
            last_names.append(f"{sp.get('e','❓')} {nm}")
        embed.add_field(name="✨ Últimas Capturas", value="\n".join(last_names), inline=False)

    pct = int((len(caught) + len(bosses)) / total * 100) if total > 0 else 0
    embed.set_footer(text=f"Completado: {pct}%")
    await interaction.response.send_message(embed=embed)

@tree.command(name="boss", description="Convoca e enfrenta um boss!")
@app_commands.describe(nome="Nome do boss (deixa em branco para um aleatório)")
async def boss_cmd(interaction: discord.Interaction, nome: Optional[str] = None):
    uid = interaction.user.id
    data = load_save(uid)

    if data.get("inBattle") or data.get("inBossBattle"):
        await interaction.response.send_message("⚔️ Já estás em batalha!", ephemeral=True); return

    mon = get_active_mon(data)
    if not mon or not mon.get("alive", True):
        await interaction.response.send_message("❌ Precisas de um monstro vivo! Usa `/curar` ou `/ativar`.", ephemeral=True); return

    if nome:
        boss = BOSS_INDEX.get(nome)
        if not boss:
            names = ", ".join(b["n"] for b in BOSSES[:10])
            await interaction.response.send_message(f"❌ Boss não encontrado. Alguns bosses: {names}...", ephemeral=True); return
    else:
        # Escolher boss não derrotado ou aleatório
        defeated = data.get("bossDefeated", [])
        available = [b for b in BOSSES if b["n"] not in defeated and b.get("special") not in ["master_only","nico"]]
        if not available:
            available = [b for b in BOSSES if b.get("special") not in ["master_only","nico"]]
        boss = random.choice(available)

    refresh_mon_stats(mon)
    player_hp = mon["maxHp"]

    data["inBossBattle"] = True
    data["boss"] = boss
    data["bossHp"] = boss["hp"]
    data["bossMaxHp"] = boss["hp"]
    data["playerHp"] = player_hp
    data["playerMaxHp"] = player_hp
    data["playerMon"] = mon
    data["defending"] = False
    write_save(uid, data)

    embed = discord.Embed(
        title=f"👹 BOSS: {boss['e']} {boss['n']}",
        description=f"*{boss.get('title','?')}*\n\n⚔️ Batalha de Boss iniciada!",
        color=0x8a0020
    )
    embed.add_field(name="Boss HP", value=f"❤️ {boss['hp']}/{boss['hp']}", inline=True)
    embed.add_field(name="Boss ATK", value=str(boss["atk"]), inline=True)
    embed.add_field(name="O teu Monstro", value=f"{mon.get('e','')} {mon.get('species', mon.get('n','?'))} Lv.{mon.get('level',1)}\nATK:{mon['atkStat']} | HP:{player_hp}", inline=False)
    embed.set_footer(text=f"Tip: Defender reduz o dano a 30-60%! Balls restantes: {data.get('balls',0)}")
    view = BossView(uid)
    await interaction.response.send_message(embed=embed, view=view)

@tree.command(name="bosses", description="Lista todos os bosses disponíveis")
async def bosses_list(interaction: discord.Interaction):
    uid = interaction.user.id
    data = load_save(uid)
    defeated = data.get("bossDefeated", [])

    embed = discord.Embed(title="👹 Bosses", color=0x8a0020)
    for boss in BOSSES:
        status = "✅" if boss["n"] in defeated else "🔒"
        special_tag = f" [{boss.get('special','').upper()}]" if boss.get("special") else ""
        embed.add_field(
            name=f"{status} {boss['e']} {boss['n']}{special_tag}",
            value=f"*{boss.get('title','?')}* | HP:{boss['hp']} | ATK:{boss['atk']} | 💰{boss['reward']}",
            inline=False
        )
    embed.set_footer(text=f"Derrotados: {len(defeated)}/{len(BOSSES)}")
    await interaction.response.send_message(embed=embed)

@tree.command(name="usar", description="Usa um item do inventário no monstro ativo")
@app_commands.describe(item="Nome do item (proteína, heartseed, tiercore, xatk, etc)")
async def use_item(interaction: discord.Interaction, item: str):
    uid = interaction.user.id
    data = load_save(uid)
    mon = get_active_mon(data)

    if not mon:
        await interaction.response.send_message("❌ Sem monstro ativo!", ephemeral=True); return

    item_map = {
        "proteína":"protein","protein":"protein",
        "heartseed":"heartseed",
        "tiercore":"tiercore","tier core":"tiercore",
        "xatk":"xatk","x-ataque":"xatk",
        "raredecoy":"raredecoy","isco raro":"raredecoy",
        "epicdecoy":"epicdecoy","isco épico":"epicdecoy",
        "goldenball":"goldenball","golden ball":"goldenball",
        "megaincense":"megaincense","mega incenso":"megaincense",
    }
    item_id = item_map.get(item.lower())
    if not item_id:
        await interaction.response.send_message(f"❌ Item desconhecido: **{item}**. Verifica o teu inventário.", ephemeral=True); return

    items = data.get("items", {})
    if items.get(item_id, 0) <= 0:
        await interaction.response.send_message(f"❌ Não tens **{item}** no inventário!", ephemeral=True); return

    refresh_mon_stats(mon)
    msg = ""
    if item_id == "protein":
        mon["atkBoost"] = mon.get("atkBoost",0) + 10
        refresh_mon_stats(mon)
        msg = f"💪 {mon.get('e','')} {mon.get('species',mon.get('n','?'))} ganhou +10 ATK permanente! (Total: +{mon['atkBoost']})"
    elif item_id == "heartseed":
        mon["hpBoost"] = mon.get("hpBoost",0) + 10
        refresh_mon_stats(mon)
        msg = f"🌱 {mon.get('e','')} {mon.get('species',mon.get('n','?'))} ganhou +10 HP permanente! (Total: +{mon['hpBoost']})"
    elif item_id == "tiercore":
        if mon.get("tier",1) >= 5:
            await interaction.response.send_message("❌ Tier já está no máximo (5)!", ephemeral=True); return
        mon["tier"] = mon.get("tier",1) + 1
        refresh_mon_stats(mon)
        mon["hp"] = mon["maxHp"]
        msg = f"🔺 {mon.get('e','')} {mon.get('species',mon.get('n','?'))} subiu para Tier **{mon['tier']}**! HP:{mon['maxHp']} ATK:{mon['atkStat']}"
    elif item_id == "xatk":
        data["xatkActive"] = True
        msg = "💢 X-Ataque ativado! Próximo ataque terá +60% de dano."
    elif item_id == "raredecoy":
        data["forcedRarity"] = "raro"
        msg = "🧲 Isco Raro ativado! O próximo monstro será Raro ou superior!"
    elif item_id == "epicdecoy":
        data["forcedRarity"] = "épico"
        msg = "💎 Isco Épico ativado! O próximo monstro será Épico ou superior!"
    elif item_id == "goldenball":
        msg = "🌟 Golden Ball pronta! Será usada automaticamente no próximo `/cacar` → Ball."

    items[item_id] -= 1
    data["items"] = items
    write_save(uid, data)
    await interaction.response.send_message(msg)

@tree.command(name="trocar", description="Troca um monstro entre equipa e box")
@app_commands.describe(acao="'box' para guardar da equipa, 'equipa' para trazer da box", nome="Nome do monstro")
async def swap(interaction: discord.Interaction, acao: str, nome: str):
    uid = interaction.user.id
    data = load_save(uid)

    if acao.lower() == "box":
        team = data.get("team", [])
        if len(team) <= 1:
            await interaction.response.send_message("❌ Não podes ter menos de 1 monstro na equipa!", ephemeral=True); return
        mon = next((m for m in team if nome.lower() in m.get("species", m.get("n","")).lower()), None)
        if not mon:
            await interaction.response.send_message(f"❌ **{nome}** não está na tua equipa!", ephemeral=True); return
        data["team"].remove(mon)
        data.setdefault("box",[]).append(mon)
        if data.get("activeMonId") == mon.get("id"):
            data["activeMonId"] = data["team"][0]["id"] if data["team"] else None
        write_save(uid, data)
        await interaction.response.send_message(f"📦 {mon.get('e','')} **{mon.get('species', mon.get('n','?'))}** guardado na Box!")

    elif acao.lower() in ["equipa","team"]:
        if len(data.get("team",[])) >= 6:
            await interaction.response.send_message("❌ Equipa cheia (máx 6)! Guarda primeiro um monstro.", ephemeral=True); return
        box = data.get("box", [])
        mon = next((m for m in box if nome.lower() in m.get("species", m.get("n","")).lower()), None)
        if not mon:
            await interaction.response.send_message(f"❌ **{nome}** não está na tua Box!", ephemeral=True); return
        data["box"].remove(mon)
        data.setdefault("team",[]).append(mon)
        if not data.get("activeMonId"):
            data["activeMonId"] = mon["id"]
        write_save(uid, data)
        await interaction.response.send_message(f"🐾 {mon.get('e','')} **{mon.get('species', mon.get('n','?'))}** trazido para a Equipa!")
    else:
        await interaction.response.send_message("❌ Ação inválida. Usa `box` ou `equipa`.", ephemeral=True)

@tree.command(name="ranked", description="Vê o teu perfil ranked e leaderboard de amigos")
async def ranked_cmd(interaction: discord.Interaction):
    uid = interaction.user.id
    data = load_save(uid)

    elo = data.get("rankedElo", 1200)
    rank = get_rank_info(elo)
    wins = data.get("rankedWins", 0)
    losses = data.get("rankedLosses", 0)
    name = data.get("playerName", f"Jogador_{uid}")

    embed = discord.Embed(
        title=f"{rank['icon']} {name} — {rank['label']}",
        description=f"**ELO:** {elo}\n**Vitórias:** {wins} | **Derrotas:** {losses}",
        color=rank["color"]
    )

    # Amigos no leaderboard
    friends = data.get("friendScores", {})
    if friends:
        all_players = [{"name":name,"elo":elo}] + list(friends.values())
        all_players.sort(key=lambda x: x["elo"], reverse=True)
        lb_lines = []
        for i, p in enumerate(all_players[:10]):
            r = get_rank_info(p["elo"])
            marker = " ← **Tu**" if p.get("name")==name and p.get("elo")==elo else ""
            lb_lines.append(f"**#{i+1}** {r['icon']} {p['name']} — ELO {p['elo']}{marker}")
        embed.add_field(name="🏆 Leaderboard de Amigos", value="\n".join(lb_lines), inline=False)

    # Gerar código de partilha
    import base64
    score_data = {"id":str(uid),"name":name,"elo":elo,"wins":wins,"losses":losses,"ts":int(time.time())}
    code = "MHRPG:" + base64.b64encode(json.dumps(score_data).encode()).decode()
    embed.add_field(name="📋 O teu Código de Pontuação", value=f"`{code[:60]}...`\nUsa `/ranked-import` para adicionar amigos", inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="ranked-import", description="Importa a pontuação de um amigo")
@app_commands.describe(codigo="Código MHRPG: do teu amigo")
async def ranked_import(interaction: discord.Interaction, codigo: str):
    import base64
    uid = interaction.user.id
    data = load_save(uid)

    try:
        if not codigo.startswith("MHRPG:"):
            await interaction.response.send_message("❌ Código inválido! Deve começar com `MHRPG:`", ephemeral=True); return
        friend_data = json.loads(base64.b64decode(codigo[6:]).decode())
        if not all(k in friend_data for k in ["id","name","elo"]):
            raise ValueError
    except:
        await interaction.response.send_message("❌ Código corrompido ou inválido.", ephemeral=True); return

    if str(friend_data["id"]) == str(uid):
        await interaction.response.send_message("😄 Esse código és tu!", ephemeral=True); return

    data.setdefault("friendScores",{})[friend_data["id"]] = friend_data
    write_save(uid, data)
    rank = get_rank_info(friend_data["elo"])
    await interaction.response.send_message(f"✅ **{friend_data['name']}** adicionado ao leaderboard! {rank['icon']} ELO {friend_data['elo']}")

@tree.command(name="rebirth", description="Faz Rebirth (custa 10.000 💰) — reinicia com bónus permanente!")
async def rebirth(interaction: discord.Interaction):
    uid = interaction.user.id
    data = load_save(uid)

    if data.get("gold", 0) < 10000:
        await interaction.response.send_message(f"❌ Precisas de 💰10.000 para Rebirth. Tens apenas 💰{data.get('gold',0)}.", ephemeral=True); return

    data["gold"] -= 10000
    data["rebirthCount"] = data.get("rebirthCount",0) + 1
    rb = data["rebirthCount"]

    # Reset parcial - mantém monstros e conquistas
    data["balls"] = 10 + rb * 2
    data["items"] = {}
    data["materials"] = {}
    data["battleBonus"] = 0
    data["catchBonus"] = 0
    data["level"] = 1

    write_save(uid, data)
    await interaction.response.send_message(
        f"🌀 **Rebirth #{rb} realizado!**\n"
        f"XP e drops x{1+rb}! Balls de início: {data['balls']}\n"
        f"Os teus monstros e conquistas foram mantidos!"
    )

@tree.command(name="perfil", description="Vê o teu perfil completo")
async def profile(interaction: discord.Interaction):
    uid = interaction.user.id
    data = load_save(uid)

    embed = discord.Embed(
        title=f"👤 Perfil de {data.get('playerName', interaction.user.display_name)}",
        color=0xffd700
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)

    caught = data.get("caught", [])
    bosses_def = data.get("bossDefeated", [])
    team = data.get("team", [])
    elo = data.get("rankedElo", 1200)
    rank = get_rank_info(elo)

    embed.add_field(name="💰 Ouro", value=str(data.get("gold",0)), inline=True)
    embed.add_field(name="🔮 Balls", value=str(data.get("balls",0)), inline=True)
    embed.add_field(name="🌀 Rebirths", value=str(data.get("rebirthCount",0)), inline=True)
    embed.add_field(name="📖 Pokédex", value=f"{len(caught)}/{len(MONS)}", inline=True)
    embed.add_field(name="👹 Bosses", value=f"{len(bosses_def)}/{len(BOSSES)}", inline=True)
    embed.add_field(name=f"{rank['icon']} Rank", value=f"{rank['label']} ({elo} ELO)", inline=True)
    embed.add_field(name="🐾 Equipa", value=f"{len(team)}/6 monstros", inline=True)
    embed.add_field(name="⚔️ Ranked", value=f"{data.get('rankedWins',0)}W / {data.get('rankedLosses',0)}L", inline=True)

    mon = get_active_mon(data)
    if mon:
        refresh_mon_stats(mon)
        embed.add_field(
            name="⭐ Monstro Ativo",
            value=f"{mon.get('e','')} {mon.get('species',mon.get('n','?'))} Lv.{mon.get('level',1)} Tier {mon.get('tier',1)}\n❤️{mon.get('hp','?')}/{mon.get('maxHp','?')} ⚔️{mon.get('atkStat','?')}",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

@tree.command(name="ajuda", description="Mostra todos os comandos disponíveis")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🐲 Monster Hunter RPG — Ajuda",
        description="Bem-vindo ao Monster Hunter RPG! Captura monstros, enfrenta bosses e sobe no ranking!",
        color=0xffd700
    )
    cmds = [
        ("🏹 `/cacar`", "Encontra e captura um monstro selvagem"),
        ("🐾 `/equipa`", "Vê a tua equipa de monstros"),
        ("📦 `/box`", "Vê os monstros na tua Box"),
        ("⭐ `/ativar [pos]`", "Define o monstro ativo (posição 1-6)"),
        ("💊 `/curar [tipo]`", "Cura o monstro ativo (poção, superpoção, etc)"),
        ("🎒 `/inventario`", "Vê itens, materiais e recursos"),
        ("🛒 `/loja`", "Abre a loja de itens"),
        ("🧪 `/usar [item]`", "Usa um item no monstro ativo"),
        ("📖 `/pokedex`", "Vê os monstros capturados"),
        ("👹 `/boss [nome?]`", "Enfrenta um boss!"),
        ("📋 `/bosses`", "Lista todos os bosses"),
        ("🔄 `/trocar [ação] [nome]`", "Troca monstros entre equipa e box"),
        ("🏆 `/ranked`", "Vê o teu rank e leaderboard"),
        ("📥 `/ranked-import [código]`", "Adiciona pontuação de amigo"),
        ("🌀 `/rebirth`", "Rebirth (custa 10.000💰)"),
        ("👤 `/perfil`", "Vê o teu perfil completo"),
    ]
    for name, desc in cmds:
        embed.add_field(name=name, value=desc, inline=False)
    embed.set_footer(text="💡 Dica: Luta contra monstros selvagens para aumentar a taxa de captura!")
    await interaction.response.send_message(embed=embed)

@tree.command(name="nomear", description="Define o teu nome de jogador para o ranked")
@app_commands.describe(nome="O teu nome de jogador")
async def set_name(interaction: discord.Interaction, nome: str):
    if len(nome) < 2 or len(nome) > 24:
        await interaction.response.send_message("❌ Nome deve ter entre 2 e 24 caracteres.", ephemeral=True); return
    uid = interaction.user.id
    data = load_save(uid)
    data["playerName"] = nome
    write_save(uid, data)
    await interaction.response.send_message(f"✅ Nome definido: **{nome}**! Já apareces no leaderboard.")

# ══════════════════════════════════════════════
# EVENTOS DO BOT
# ══════════════════════════════════════════════

@bot.event
async def on_ready():
    print(f"Bot conectado: {bot.user} (ID: {bot.user.id})")
    try:
        synced = await tree.sync()
        print(f"Comandos sincronizados: {len(synced)}")
        for cmd in synced:
            print(f"  /{cmd.name}")
    except Exception as e:
        print(f"Erro ao sincronizar: {e}")
        import traceback; traceback.print_exc()
    await bot.change_presence(activity=discord.Game(name="/ajuda | Monster Hunter RPG"))

@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    cmd_name = interaction.command.name if interaction.command else "?"
    print(f"Erro no comando /{cmd_name}: {error}")
    import traceback; traceback.print_exc()
    try:
        msg = "Ocorreu um erro interno. Tenta novamente."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
    except Exception:
        pass

if __name__ == "__main__":
    TOKEN = os.environ.get("DISCORD_TOKEN", "")
    if not TOKEN:
        print("ERRO: Define DISCORD_TOKEN.")
        print("  Windows: set DISCORD_TOKEN=o_teu_token")
        print("  Linux:   export DISCORD_TOKEN=o_teu_token")
        exit(1)
    print("A iniciar o bot...")
    print("A iniciar o bot...")
    bot.run(TOKEN)

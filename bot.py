"""
Monster Hunter RPG - Discord Bot - V118 HTML-Synced
Sincronizado com monster_hunter_V117.html — mecânicas, HUD e sistema de batalha completos
"""

import discord
from discord.ext import commands
from discord import app_commands
import json, os, random, math, asyncio, time
from typing import Optional

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
    {"n":"Rei das Chamas","t":"fogo","e":"👹","hp":1000,"atk":35,"reward":500,"title":"Senhor do Inferno","mats":[{"n":"Coroa de Fogo","v":200}]},
    {"n":"Titã dos Mares","t":"água","e":"🐋","hp":1400,"atk":30,"reward":600,"title":"Leviatã Ancestral","mats":[{"n":"Escudo Abissal","v":200}]},
    {"n":"Lorde das Sombras","t":"sombra","e":"🌑","hp":420,"atk":40,"reward":700,"title":"Devorador de Almas","mats":[{"n":"Cristal Negro","v":200}]},
    {"n":"Maestro do Caos","t":"som","e":"🎻","hp":1900,"atk":55,"reward":1600,"title":"O Regente do Silêncio","mats":[{"n":"Vibração","v":400}]},
    {"n":"Guardião das Eras","t":"tempo","e":"🕰️","hp":2400,"atk":40,"reward":1900,"title":"Aquele que Parou o Tempo","mats":[{"n":"Engrenagem","v":450}]},
    {"n":"Arcanjo Solar","t":"luz","e":"👼","hp":2100,"atk":50,"reward":2500,"title":"O Esplendor do Meio-Dia","mats":[{"n":"Fóton","v":500}]},
    {"n":"Vazio Estelar","t":"cosmos","e":"🕳️","hp":2600,"atk":65,"reward":3000,"title":"O Devorador de Galáxias","mats":[{"n":"Poeira Estelar","v":550}]},
    {"n":"Leviatã de Ferro","t":"metal","e":"⛓️","hp":3800,"atk":35,"reward":2200,"title":"A Fortaleza Móvel","mats":[{"n":"Lingote","v":600}]},
    {"n":"Dragão do Apocalipse","t":"ar","e":"🐲","hp":4000,"atk":45,"reward":900,"title":"Fim dos Tempos","mats":[{"n":"Dente do Apocalipse","v":200}]},
    {"n":"DEUS DO CAOS","t":"veneno","e":"💀","hp":6666,"atk":666,"reward":1500,"title":"O Inominável","mats":[{"n":"Fragmento Divino","v":200}]},
    {"n":"Entidade Verdejante","t":"planta","e":"🌳","hp":2200,"atk":38,"reward":1400,"title":"O Coração da Floresta","mats":[{"n":"Folha Ancestral","v":350}]},
    {"n":"Colosso da Montanha","t":"terra","e":"🗿","hp":3500,"atk":42,"reward":1600,"title":"O Guardião da Rocha","mats":[{"n":"Pedra Titânica","v":400}]},
    {"n":"Senhor dos Vendavais","t":"ar","e":"🌪️","hp":1900,"atk":48,"reward":1500,"title":"A Fúria do Céu","mats":[{"n":"Pluma da Tempestade","v":380}]},
    {"n":"Tirano Glacial","t":"gelo","e":"❄️","hp":2800,"atk":36,"reward":1700,"title":"O Inverno Eterno","mats":[{"n":"Cristal Gélido","v":420}]},
    {"n":"Deus da Tempestade","t":"trovão","e":"⚡","hp":2100,"atk":52,"reward":1800,"title":"O Arauto dos Céus","mats":[{"n":"Faísca Divina","v":450}]},
    {"n":"Mente Suprema","t":"psíquico","e":"🧠","hp":1800,"atk":55,"reward":2000,"title":"O Oráculo Cósmico","mats":[{"n":"Frag. Psíquico","v":500}]},
    {"n":"Campeão Indomável","t":"luta","e":"👊","hp":3000,"atk":50,"reward":1600,"title":"O Punho Inquebrável","mats":[{"n":"Fita Lendária","v":400}]},
    {"n":"Imperador dos Enxames","t":"inseto","e":"🐝","hp":1700,"atk":40,"reward":1400,"title":"A Colmeia Viva","mats":[{"n":"Casulo Real","v":350}]},
    {"n":"Soberano de Néon","t":"néon","e":"🟢","hp":2000,"atk":54,"reward":2000,"title":"A Grade Digital","mats":[{"n":"Plasma Néon","v":500}]},
    {"n":"Entidade Radioativa","t":"nuclear","e":"☢️","hp":3200,"atk":60,"reward":2200,"title":"O Núcleo Instável","mats":[{"n":"Urânio Puro","v":550}]},
    {"n":"Ancestral Sagrado","t":"espírito","e":"🙏","hp":2300,"atk":44,"reward":1800,"title":"A Voz dos Antigos","mats":[{"n":"Essência Espiritual","v":450}]},
    {"n":"Engenheiro do Caos","t":"mecânico","e":"🤖","hp":4000,"atk":46,"reward":2100,"title":"A Máquina Perfeita","mats":[{"n":"Peça Mecânica Lendária","v":520}]},
    {"n":"Senhor do Magma","t":"magma","e":"🌋","hp":3600,"atk":48,"reward":2000,"title":"O Coração da Terra","mats":[{"n":"Lava Solidificada","v":500}]},
    {"n":"Mestre Arcano","t":"arcano","e":"🔮","hp":2500,"atk":56,"reward":2300,"title":"O Guardião dos Segredos","mats":[{"n":"Cristal Arcano","v":600}]},
    {"n":"Espectro do Vazio","t":"fantasma","e":"👻","hp":1500,"atk":58,"reward":1900,"title":"A Alma Perdida","mats":[{"n":"Ectoplasma","v":480}]},
    {"n":"Dragão Primordial","t":"dragão","e":"🐉","hp":5000,"atk":70,"reward":3000,"title":"O Primeiro dos Dragões","mats":[{"n":"Escama Ancestral","v":800}]},
    {"n":"Rainha das Fadas","t":"fada","e":"🧚","hp":1600,"atk":42,"reward":1700,"title":"A Protetora dos Reinos","mats":[{"n":"Pó de Fada","v":420}]},
    {"n":"Void King","t":"cristal","e":"👑","hp":5800,"atk":1000,"reward":1200,"title":"Rei do Vazio","mats":[{"n":"Coroa do Vazio","v":2000}],"special":"master_only"},
    {"n":"Nico","t":"fofa","e":"🐈","hp":1500,"atk":150,"reward":5000,"title":"A Destruidora de Mundos","mats":[{"n":"Pelo Cósmico","v":999}],"special":"nico"},
    {"n":"murilo","t":"molestador","e":"👨‍🦽","hp":3000,"atk":150,"reward":5000,"title":"O Inominável do Caos","mats":[{"n":"esperma","v":999}],"special":"murilo"},
    {"n":"???","t":"???","e":"❓","hp":999999,"atk":12000,"reward":10000,"title":"???","mats":[{"n":"Essência Divina","v":1000}],"special":"final_boss"},
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

def build_mons():
    mons = []
    for td in TYPE_DEFS:
        for i, plan in enumerate(RARITY_PLAN):
            if i < len(td["names"]):
                mons.append({
                    "n":td["names"][i],"e":td["emojis"][i%len(td["emojis"])],
                    "t":td["t"],"c":td["c"],"r":plan["catch"],
                    "hp":max(1,plan["hp"]+td["hpMod"]),"atk":max(1,plan["atk"]+td["atkMod"]),
                    "mats":[{"n":f"{td['mat']} {td['t']}","v":plan["mat"]}],"rare":plan["rare"],
                })
    # Monstros especiais (sincronizados com HTML)
    mons += [
        {"n":"OXIGÉNIO","e":"💨","t":"Ar","c":0xaae0ff,"r":0.05,"hp":95,"atk":88,"mats":[{"n":"O2","v":130}],"rare":"divino"},
        {"n":"Ciclone-Rei","e":"🌀","t":"caos","c":0x6b44d9,"r":0.06,"hp":122,"atk":28,"mats":[{"n":"Olho do Caos","v":120}],"rare":"Divino"},
        {"n":"DEUS-DRAGÃO","e":"🐲","t":"absoluto","c":0xffd700,"r":0.06,"hp":165,"atk":33,"mats":[{"n":"Alma do Dragão","v":160}],"rare":"Divino"},
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

def generate_wild_mon(forced_rarity=None,forced_type=None,data=None):
    """Gera monstro selvagem com suporte a iscas e modo pesadelo"""
    # Isco de raridade
    if forced_rarity:
        rord=["comum","incomum","raro","épico","lendário","mítico","divino","Divino"]
        mi=rord.index(forced_rarity) if forced_rarity in rord else 0
        elig=[p for p in RARITY_PLAN if rord.index(p["rare"])>=mi]
        plan=random.choice(elig) if elig else random.choice(RARITY_PLAN)
    else:
        # Pesos de raridade (sincronizados com HTML)
        wm={"comum":12,"incomum":7,"raro":4.5,"épico":2.2,"lendário":1,"mítico":0.5}
        if data:
            # Ajuste de spawn baseado em incenso raro
            stacks = data.get("rareSpawnPassive", 0)
            if stacks > 0:
                wm["comum"] = max(1, wm["comum"] - stacks * 1.44)
                wm["incomum"] = max(1, wm["incomum"] - stacks * 0.42)
                wm["raro"] = min(20, wm["raro"] + stacks * 1.575)
                wm["épico"] = min(15, wm["épico"] + stacks * 1.21)
                wm["lendário"] = min(10, wm["lendário"] + stacks * 0.8)
                wm["mítico"] = min(8, wm["mítico"] + stacks * 0.55)
        pw=[(p,wm.get(p["rare"],5)) for p in RARITY_PLAN]
        tot=sum(w for _,w in pw); rnd=random.random()*tot
        plan=RARITY_PLAN[-1]
        for p,w in pw:
            rnd-=w
            if rnd<=0: plan=p; break
    td=next((t for t in TYPE_DEFS if t["t"]==forced_type),None) if forced_type else random.choice(TYPE_DEFS)
    if not td: td=random.choice(TYPE_DEFS)
    idx=RARITY_PLAN.index(plan)
    name=td["names"][min(idx,len(td["names"])-1)]
    emoji=td["emojis"][idx%len(td["emojis"])]
    wild = {
        "n":name,"t":td["t"],"e":emoji,"rare":plan["rare"],
        "hp":max(1,plan["hp"]+td["hpMod"]),"maxHp":max(1,plan["hp"]+td["hpMod"]),
        "atk":max(1,plan["atk"]+td["atkMod"]),"catch":plan["catch"],
        "color":td["c"],"mats":[{"n":f"{td['mat']} {td['t']}","v":plan["mat"]}],
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
    rare=wild.get("rare","comum"); color=RARE_COLOR.get(rare,0x888888)
    hp=wild.get("hp",0); mhp=wild.get("maxHp",1); pct=hp/max(1,mhp); bar=hp_bar(pct)
    embed=discord.Embed(title="⚔️ Batalha Selvagem",color=color)
    embed.add_field(name="💰 Ouro",value=f"**{data.get('gold',0)}**",inline=True)
    embed.add_field(name="🔮 Balls",value=f"**{data.get('balls',0)}**",inline=True)
    embed.add_field(name="⭐ Master",value=f"**{data.get('masterball',0)}**",inline=True)
    embed.add_field(name=f"{wild['e']} **{wild['n']}**",
        value=f"{type_badge(wild.get('t','?'))} · {rare_badge(rare)}\nHP: **{hp}/{mhp}**\n{bar}\n⚔️ ATK: **{wild.get('atk','?')}**",inline=False)
    if msg: embed.add_field(name="📋 Log",value=msg,inline=False)
    mon=get_active_mon(data)
    if mon:
        refresh_mon_stats(mon)
        mpct=mon["hp"]/max(1,mon["maxHp"]); mbar=hp_bar(mpct,10)
        alive="💚" if mon.get("alive",True) else "💀"
        cd=max(0,int(math.ceil(data.get("attackCooldownUntil",0)-time.time())))
        cd_txt=f"⏳ Ataque em **{cd}s**" if cd>0 else "⚔️ Pronto para atacar!"
        sp=mon.get("species",mon.get("n","?"))
        # Calcular penalidade de nível para mostrar no HUD
        lv_penalty = get_team_level_catch_penalty(data)
        penalty_pct = int((1 - 1/lv_penalty) * 100) if lv_penalty > 1 else 0
        penalty_txt = f" 🔒 Captura -{penalty_pct}%" if penalty_pct > 5 else ""
        embed.add_field(name=f"{alive} {mon.get('e','')} **{sp}** — Lv.{mon.get('level',1)} {tier_stars(mon.get('tier',1))}",
            value=f"{type_badge(mon.get('t','?'))}\n❤️ **{mon['hp']}/{mon['maxHp']}** · ⚔️ **{mon.get('atkStat','?')}**\n{mbar}\n{cd_txt}{penalty_txt}",inline=False)
    else:
        embed.add_field(name="⚔️ Sem Monstro Ativo",value="Usa 🔮 Ball para capturar o teu primeiro monstro!",inline=False)
        enemy_hits=data.get("enemyHits",0)
    max_hits=3 if is_nightmare_mode(data) else 5
    footer=f"⚔️ Lutar tem cooldown 5s · 🐾 Monster Fight disponível · ⚠️ Inimigo ataca a cada 10s ({enemy_hits}/{max_hits} ataques para fugir) · 🏃 Fugir"
    embed.set_footer(text=footer)
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

SAVE_DIR="saves"
os.makedirs(SAVE_DIR,exist_ok=True)

def save_path(uid): return os.path.join(SAVE_DIR,f"{uid}.json")

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

def load_save(uid):
    p=save_path(uid)
    if os.path.exists(p):
        try:
            with open(p,encoding="utf-8") as f: raw=f.read().strip()
            if not raw: raise ValueError("vazio")
            d=default_save(); d.update(json.loads(raw)); return d
        except Exception as e:
            print(f"Save corrompido {uid}: {e}")
            try: os.rename(p,p+".corrupted")
            except: pass
    return default_save()

def write_save(uid,data):
    p=save_path(uid); tmp=p+".tmp"
    try:
        with open(tmp,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
        os.replace(tmp,p)
    except Exception as e: print(f"Erro ao guardar {uid}: {e}")

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
    data=load_save(uid)
    if sanitize_save(data): write_save(uid,data)
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
# VIEW BATALHA SELVAGEM
# ══════════════════════════════════════════════

class BattleView(discord.ui.View):
    def __init__(self,uid,timeout=180):
        super().__init__(timeout=timeout); self.uid=uid; self._sync()
        def _sync(self):
        data=load_clean_save(self.uid)
        cd=max(0,int(math.ceil(data.get("attackCooldownUntil",0)-time.time())))
        mon=get_active_mon(data)
        can_monster=bool(mon and mon.get("alive",True))
        for c in self.children:
            cid=getattr(c,"custom_id","")
            if cid=="fight_mon":
                c.label=f"⚔️ Lutar ({cd}s)" if cd>0 else "⚔️ Lutar"
                c.disabled=(cd>0)
            elif cid=="throw_ball":
                c.label=f"🔮 Ball ({data.get('balls',0)})"
                c.disabled=(data.get("balls",0)<=0)
            elif cid=="throw_master":
                c.label=f"⭐ Master ({data.get('masterball',0)})"
                c.disabled=(data.get("masterball",0)<=0)
            elif cid=="monster_fight":
                c.label="🐾 Monster Fight"
                c.disabled=not can_monster
        if data.get("inBattle") and data.get("wild"):
            now=time.time()
            last_atk=data.get("lastEnemyAtk",0)
            if now-last_atk>=10:
                mon2=get_active_mon(data)
                wild2=data["wild"]
                if mon2 and mon2.get("alive",True):
                    dmg=max(1,int(wild2.get("atk",5)*(0.5+random.random()*0.45)))
                    mon2["hp"]=max(0,mon2["hp"]-dmg)
                    data["enemyHits"]=data.get("enemyHits",0)+1
                    data["lastEnemyAtk"]=now
                    max_hits=3 if is_nightmare_mode(data) else 5
                    if data["enemyHits"]>=max_hits:
                        data["wild"]=None
                        clear_wild_state(data)
                write_save(self.uid,data)
        return data
        
    async def _chk(self,interaction):
        data=load_clean_save(self.uid)
        if not data.get("inBattle") or not data.get("wild"):
            try: await interaction.response.edit_message(content="❌ Sem batalha. Usa `/caçar`.",embed=None,view=None)
            except: pass
            return None
        return data

           @discord.ui.button(label="⚔️ Lutar",style=discord.ButtonStyle.danger,custom_id="fight_mon",row=0)
    async def fight_mon(self,interaction:discord.Interaction,button:discord.ui.Button):
        if interaction.user.id!=self.uid: await interaction.response.send_message("❌ Não é a tua batalha!",ephemeral=True); return
        data=await self._chk(interaction)
        if not data: return
        cd=max(0,int(math.ceil(data.get("attackCooldownUntil",0)-time.time())))
        if cd>0: await interaction.response.send_message(f"⏳ Aguarda **{cd}s**!",ephemeral=True); return
        
        wild=data["wild"]
        mon=get_active_mon(data)
        
        # Jogador ataca sozinho (sem monstro)
        if not mon or not mon.get("alive",True):
            dmg=max(1,int(8+random.random()*6))
            ret=max(1,int(wild.get("atk",5)*(0.5+random.random()*0.45)))
            wild["hp"]=max(0,wild["hp"]-dmg)
            data["attackCooldownUntil"]=time.time()+5.0
            data["battleBonus"]=max(-0.4,data.get("battleBonus",0)-0.05)
            lines=[]
            lines.append(f"👊 Atacaste com as próprias mãos! **{dmg}** dano!")
            lines.append(f"🗡️ **{wild['e']} {wild['n']}** contra-atacou! **-{ret}** HP (ignorado - sem monstro)")
            if wild["hp"]<=0:
                wild["hp"]=0; lines.append(f"✅ **{wild['n']}** derrotado! Usa 🔮 Ball para capturar!")
                data["wild"]=wild; data["battleBonus"]=min(0.65,data.get("battleBonus",0)+0.10)
                write_save(self.uid,data)
                view=BattleView(self.uid)
                for c in view.children:
                    if getattr(c,"custom_id","")=="fight_mon": c.disabled=True; c.label="⚔️ Derrotado"
                await interaction.response.edit_message(embed=make_wild_embed(wild,data,"\n".join(lines)),view=view); return
            data["wild"]=wild; write_save(self.uid,data)
            view=BattleView(self.uid)
            await interaction.response.edit_message(embed=make_wild_embed(wild,data,"\n".join(lines)),view=view); return
        
        # Monstro ataca pelo jogador
        refresh_mon_stats(mon)
        at,effect=get_type_effect(mon.get("t",""),wild.get("t",""))
        rt,rteffect=get_type_effect(wild.get("t",""),mon.get("t",""))
        db=1+data.get("rebirthCount",0)*0.5; xb=1.6 if data.get("xatkActive") else 1.0
        if data.get("xatkActive"): data["xatkActive"]=False
        dmg=max(1,int(mon["atkStat"]*(0.75+random.random()*0.45)*db*at*xb))
        ret=max(1,int(wild.get("atk",5)*(0.5+random.random()*0.45)*rt))
        mon["hp"]=max(0,mon["hp"]-ret)
        wild["hp"]=max(0,wild["hp"]-dmg)
        data["battleBonus"]=max(-0.4,data.get("battleBonus",0)-0.08)
        gainXp(mon,8+int(wild.get("atk",5)*1.6),data)
        data["attackCooldownUntil"]=time.time()+5.0
        lines=[]
        if at>1: lines.append(f"⚡ **Super eficaz!** {mon.get('e','')} causou **{dmg}** dano!")
        elif at<1: lines.append(f"💧 *Pouco eficaz...* {mon.get('e','')} causou **{dmg}** dano.")
        else: lines.append(f"⚔️ {mon.get('e','')} **{mon.get('species',mon.get('n','?'))}** causou **{dmg}** dano!")
        if rt>1: lines.append(f"⚡ **{wild['e']} {wild['n']}** contra-atacou com **{ret}** dano! *Super eficaz!*")
        elif rt<1: lines.append(f"💧 **{wild['e']} {wild['n']}** contra-atacou com **{ret}** dano. *Pouco eficaz...*")
        else: lines.append(f"🗡️ **{wild['e']} {wild['n']}** contra-atacou! **-{ret}** HP")
        if mon["hp"]<=0:
            mon["alive"]=False; lines.append(f"💀 **{mon.get('species',mon.get('n','?'))}** desmaiou!")
            outros=[m for m in data.get("team",[]) if m.get("alive",True) and m.get("id")!=mon.get("id")]
            lines.append(f"Ainda tens **{len(outros)}** monstro(s) vivo(s). Usa `/ativar`." if outros else "💀 Todos os monstros KO! Usa `/curar`.")
            clear_wild_state(data); write_save(self.uid,data)
            await interaction.response.edit_message(embed=make_wild_embed(wild,data,"\n".join(lines)),view=None); return
        if wild["hp"]<=0:
            wild["hp"]=0; lines.append(f"✅ **{wild['n']}** derrotado! Usa 🔮 Ball para capturar!")
            data["wild"]=wild; data["battleBonus"]=min(0.65,data.get("battleBonus",0)+0.15)
            write_save(self.uid,data)
            view=BattleView(self.uid)
            for c in view.children:
                if getattr(c,"custom_id","")=="fight_mon": c.disabled=True; c.label="⚔️ Derrotado"
            await interaction.response.edit_message(embed=make_wild_embed(wild,data,"\n".join(lines)),view=view); return
        lines.append(f"💚 Teu monstro: **{mon['hp']}/{mon.get('maxHp','?')}** HP")
        data["wild"]=wild; write_save(self.uid,data)
        view=BattleView(self.uid)
        await interaction.response.edit_message(embed=make_wild_embed(wild,data,"\n".join(lines)),view=view)
    
    @discord.ui.button(label="🐾 Monster Fight",style=discord.ButtonStyle.success,custom_id="monster_fight",row=0)
    async def monster_fight(self,interaction:discord.Interaction,button:discord.ui.Button):
        if interaction.user.id!=self.uid: await interaction.response.send_message("❌ Não é a tua batalha!",ephemeral=True); return
        data=await self._chk(interaction)
        if not data: return
        mon=get_active_mon(data)
        if not mon or not mon.get("alive",True): await interaction.response.send_message("❌ Monstro KO! Usa `/curar` ou `/ativar`.",ephemeral=True); return
        wild=data["wild"]; refresh_mon_stats(mon)
        at,effect=get_type_effect(mon.get("t",""),wild.get("t",""))
        rt,rteffect=get_type_effect(wild.get("t",""),mon.get("t",""))
        db=1+data.get("rebirthCount",0)*0.5
        dmg=max(1,int(mon["atkStat"]*(0.9+random.random()*0.5)*db*at))
        ret=max(1,int(wild.get("atk",5)*(0.5+random.random()*0.45)*rt))
        mon["hp"]=max(0,mon["hp"]-ret)
        wild["hp"]=max(0,wild["hp"]-dmg)
        data["battleBonus"]=max(-0.4,data.get("battleBonus",0)-0.08)
        gainXp(mon,8+int(wild.get("atk",5)*1.6),data)
        lines=[]
        if at>1: lines.append(f"⚡ **Super eficaz!** {mon.get('e','')} causou **{dmg}** dano!")
        elif at<1: lines.append(f"💧 *Pouco eficaz...* {mon.get('e','')} causou **{dmg}** dano.")
        else: lines.append(f"🐾 {mon.get('e','')} **{mon.get('species',mon.get('n','?'))}** lutou! **{dmg}** dano!")
        if rt>1: lines.append(f"⚡ **{wild['e']} {wild['n']}** contra-atacou com **{ret}** dano! *Super eficaz!*")
        elif rt<1: lines.append(f"💧 **{wild['e']} {wild['n']}** contra-atacou com **{ret}** dano. *Pouco eficaz...*")
        else: lines.append(f"🗡️ **{wild['e']} {wild['n']}** contra-atacou! **-{ret}** HP")
        if mon["hp"]<=0:
            mon["alive"]=False; lines.append(f"💀 **{mon.get('species',mon.get('n','?'))}** desmaiou!")
            clear_wild_state(data); write_save(self.uid,data)
            await interaction.response.edit_message(embed=make_wild_embed(wild,data,"\n".join(lines)),view=None); return
        if wild["hp"]<=0:
            wild["hp"]=0; lines.append(f"✅ **{wild['n']}** derrotado! Usa 🔮 Ball para capturar!")
            data["wild"]=wild; data["battleBonus"]=min(0.65,data.get("battleBonus",0)+0.15)
            write_save(self.uid,data)
            view=BattleView(self.uid)
            for c in view.children:
                if getattr(c,"custom_id","")=="monster_fight": c.disabled=True; c.label="🐾 Derrotado"
            await interaction.response.edit_message(embed=make_wild_embed(wild,data,"\n".join(lines)),view=view); return
        lines.append(f"💚 Teu monstro: **{mon['hp']}/{mon.get('maxHp','?')}** HP")
        data["wild"]=wild; write_save(self.uid,data)
        view=BattleView(self.uid)
        await interaction.response.edit_message(embed=make_wild_embed(wild,data,"\n".join(lines)),view=view)

    @discord.ui.button(label="🔮 Ball",style=discord.ButtonStyle.primary,custom_id="throw_ball",row=0)
    async def throw_ball(self,interaction:discord.Interaction,button:discord.ui.Button):
        if interaction.user.id!=self.uid: await interaction.response.send_message("❌ Não é a tua batalha!",ephemeral=True); return
        data=await self._chk(interaction)
        if not data: return
        if data.get("balls",0)<=0: await interaction.response.send_message("❌ Sem Balls!",ephemeral=True); return
        wild=data["wild"]; bt="normal"; items=data.get("items",{})
        if items.get("goldenball",0)>0: bt="golden"; items["goldenball"]-=1
        data["balls"]-=1; chance=get_catch_chance(wild,data,bt)
        if random.random()<chance:
            captured=capture_wild(wild,data)
            if wild["n"] not in data["caught"]: data["caught"].append(wild["n"])
            clear_wild_state(data); data["balls"]=min(99,data["balls"]+2); write_save(self.uid,data)
            pf="🌟 **Golden Ball!** " if bt=="golden" else "🔮 "
            embed=discord.Embed(title=f"✅ {wild.get('e','')} {wild['n']} Capturado!",
                description=f"{pf}Sucesso! ({int(chance*100)}%)\n\n{type_badge(wild.get('t','?'))} · {rare_badge(wild.get('rare','comum'))}\nTier **{captured['tier']}** {tier_stars(captured['tier'])}\n❤️ **{captured['maxHp']}** · ⚔️ **{captured['atkStat']}**\n📖 **{len(data['caught'])}/{len(MONS)}**",
                color=RARE_COLOR.get(wild.get("rare","comum"),0x888888))
            await interaction.response.edit_message(embed=embed,view=None)
        else:
            msgs=["😅 Quase!","💨 Fugiu!","⚡ Rápido demais!","💪 Muito forte!"]; m="💥 **Golden Ball falhou!**" if bt=="golden" else random.choice(msgs)
            write_save(self.uid,data)
            await interaction.response.edit_message(embed=make_wild_embed(wild,data,f"{m} | Chance: **{int(chance*100)}%** | 🔮 {data['balls']}"),view=BattleView(self.uid))

    @discord.ui.button(label="⭐ Master Ball",style=discord.ButtonStyle.success,custom_id="throw_master",row=0)
    async def throw_master(self,interaction:discord.Interaction,button:discord.ui.Button):
        if interaction.user.id!=self.uid: await interaction.response.send_message("❌ Não é a tua batalha!",ephemeral=True); return
        data=await self._chk(interaction)
        if not data: return
        if data.get("masterball",0)<=0: await interaction.response.send_message("❌ Sem Master Ball!",ephemeral=True); return
        wild=data["wild"]; data["masterball"]-=1; captured=capture_wild(wild,data)
        if wild["n"] not in data["caught"]: data["caught"].append(wild["n"])
        clear_wild_state(data); write_save(self.uid,data)
        embed=discord.Embed(title=f"⭐ {wild.get('e','')} {wild['n']} Capturado!",
            description=f"**Captura garantida!** 👑\n\n{type_badge(wild.get('t','?'))} · {rare_badge(wild.get('rare','comum'))}\nTier **{captured['tier']}** {tier_stars(captured['tier'])}\n❤️ **{captured['maxHp']}** · ⚔️ **{captured['atkStat']}**\n📖 **{len(data['caught'])}/{len(MONS)}**",
            color=0xffd700)
        await interaction.response.edit_message(embed=embed,view=None)

    @discord.ui.button(label="🏃 Fugir",style=discord.ButtonStyle.secondary,custom_id="flee",row=1)
    async def flee(self,interaction:discord.Interaction,button:discord.ui.Button):
        if interaction.user.id!=self.uid: await interaction.response.send_message("❌ Não é a tua batalha!",ephemeral=True); return
        data=load_clean_save(self.uid); clear_wild_state(data); write_save(self.uid,data)
        await interaction.response.edit_message(content=f"🏃 Fugiste! 🔮 Balls: **{data['balls']}**",embed=None,view=None)

    async def on_timeout(self):
        try:
            data=load_clean_save(self.uid)
            if data.get("inBattle"): clear_wild_state(data); write_save(self.uid,data)
        except: pass

# ══════════════════════════════════════════════
# VIEW DE BOSS
# ══════════════════════════════════════════════

class BossView(discord.ui.View):
    def __init__(self,uid,timeout=600):
        super().__init__(timeout=timeout); self.uid=uid
    async def _chk(self,interaction):
        data=load_clean_save(self.uid)
        if not data.get("inBossBattle") or not data.get("boss"):
            try: await interaction.response.edit_message(content="❌ Sem batalha de boss.",embed=None,view=None)
            except: pass
            return None
        return data
    async def _defeat(self,interaction,data,lines):
        clear_boss_state(data); pen=int(data.get("gold",0)*0.1)
        data["gold"]=max(0,data.get("gold",0)-pen); lines.append(f"\n💀 **Derrotado!** Perdeste 💰**{pen:,}**")
        write_save(self.uid,data)
        await interaction.response.edit_message(embed=discord.Embed(title="💀 Derrota contra o Boss",description="\n".join(lines),color=0xe03030),view=None)
    async def _boss_dead(self,interaction,data,boss,mon,lines):
        if boss.get("special")=="final_boss" and data.get("finalBossPhase")==1:
            lines.append("\n💥 **Primeira forma caiu! A forma divina emerge!**")
            start_final_boss_phase2(data); write_save(self.uid,data)
            await interaction.response.edit_message(embed=make_boss_embed(data,"\n".join(lines)+"\n\n🐐 **LEONKING surge!**"),view=BossView(self.uid)); return True
        bn=boss["n"]
        if bn not in data["bossDefeated"]: data["bossDefeated"].append(bn)
        rw=boss.get("reward",500); data["gold"]=data.get("gold",0)+int(rw*0.6)
        for mat in boss.get("mats",[]): data.setdefault("materials",{})[mat["n"]]=data["materials"].get(mat["n"],0)+1
        if mon: gainXp(mon,60,data)
        mn=f"{mon.get('e','')} {mon.get('species',mon.get('n','?'))}" if mon else "o teu monstro"
        clear_boss_state(data); write_save(self.uid,data)
        ex="\n\n# 🌟 COMPLETASTE O JOGO! 🌟" if boss.get("special")=="final_boss" else ""
        embed=discord.Embed(title=f"🏆 {boss['e']} {boss['n']} DERROTADO!",
            description=f"# 🎉 Vitória!\n*{boss.get('title','?')}*{ex}\n\n💰 +**{rw:,}** ouro\n🪨 {', '.join(m['n'] for m in boss.get('mats',[]))}\n⭐ +60 XP para {mn}",color=0xffd700)
        await interaction.response.edit_message(embed=embed,view=None); return True

    @discord.ui.button(label="⚔️ Atacar",style=discord.ButtonStyle.danger,row=0)
    async def atk(self,interaction:discord.Interaction,button:discord.ui.Button):
        if interaction.user.id!=self.uid: await interaction.response.send_message("❌",ephemeral=True); return
        data=await self._chk(interaction)
        if not data: return
        mon=data.get("playerMon") or get_active_mon(data)
        if not mon: await interaction.response.send_message("❌ Sem monstro!",ephemeral=True); return
        refresh_mon_stats(mon); boss=data["boss"]
        mt,effect = get_type_effect(mon.get("t",""),boss.get("t","")); xb=1.6 if data.get("xatkActive") else 1.0
        if data.get("xatkActive"): data["xatkActive"]=False
        dmg=max(1,int(mon["atkStat"]*mt*(0.85+random.random()*0.4)*xb))
        
        # Confirmar ataque se boss < 20% (sincronizado com HTML)
        future_hp = data["bossHp"] - dmg
        limit_20 = data["bossMaxHp"] * 0.2
        if not data.get("confirmAtk20") and future_hp <= limit_20 and future_hp > 0:
            data["confirmAtk20"] = True
            write_save(self.uid, data)
            await interaction.response.send_message(
                f"⚠️ O Boss está com **20% ou menos de HP**!\nQueres continuar o ataque e arriscar matá-lo?\n\n✅ Confirma com **Atacar** novamente para golpear!\n⏸️ Usa **Defender** ou **Curar** se quiseres tentar capturar.",
                ephemeral=True
            )
            return
        
        data["confirmAtk20"] = False
        data["bossHp"]=max(0,data["bossHp"]-dmg)
        mn=f"{mon.get('e','')} {mon.get('species',mon.get('n','?'))}"
        lines=[]
        hint = get_type_hint_text(effect)
        if mt>1: lines.append(f"⚡ **Super eficaz!** {mn} causou **{dmg:,}**!")
        elif mt<1: lines.append(f"💧 *Pouco eficaz...* {mn} causou **{dmg:,}**.")
        else: lines.append(f"⚔️ {mn} atacou! **{dmg:,}** dano!")
        is_final=boss.get("special")=="final_boss"
        hr=data["bossHp"]/max(1,data["bossMaxHp"])
        if hr<=0.20 and hr>0 and not data.get("lowHpWarned") and not (is_final and data.get("finalBossPhase")==1):
            data["lowHpWarned"]=True; lines.append("⚠️ **Boss abaixo de 20%! Tenta capturá-lo!**")
        if data["bossHp"]<=0:
            if await self._boss_dead(interaction,data,boss,mon,lines): return
        boss_counterattack(data,lines)
        if data["playerHp"]<=0: await self._defeat(interaction,data,lines); return
        write_save(self.uid,data); await interaction.response.edit_message(embed=make_boss_embed(data,"\n".join(lines)),view=self)

    @discord.ui.button(label="🛡️ Defender",style=discord.ButtonStyle.secondary,row=0)
    async def defend(self,interaction:discord.Interaction,button:discord.ui.Button):
        if interaction.user.id!=self.uid: await interaction.response.send_message("❌",ephemeral=True); return
        data=await self._chk(interaction)
        if not data: return
        data["confirmAtk20"] = False  # Resetar confirmação ao defender
        data["defending"]=True; lines=["🛡️ A defender! Dano reduzido a **40%**."]
        boss_counterattack(data,lines)
        if data["playerHp"]<=0: await self._defeat(interaction,data,lines); return
        write_save(self.uid,data); await interaction.response.edit_message(embed=make_boss_embed(data,"\n".join(lines)),view=self)

    @discord.ui.button(label="🔮 Tentar Capturar",style=discord.ButtonStyle.primary,row=0)
    async def catch(self,interaction:discord.Interaction,button:discord.ui.Button):
        if interaction.user.id!=self.uid: await interaction.response.send_message("❌",ephemeral=True); return
        data=await self._chk(interaction)
        if not data: return
        data["confirmAtk20"] = False  # Resetar confirmação ao capturar
        boss=data["boss"]
        if boss.get("special")=="final_boss" and data.get("finalBossPhase")==1:
            await interaction.response.send_message("🌌 A primeira forma não pode ser capturada!",ephemeral=True); return
        if data.get("bossBallCD",0)>0:
            await interaction.response.send_message(f"⏳ Ball em recarga! **{data['bossBallCD']}** turno(s).",ephemeral=True); return
        if boss.get("special")=="master_only":
            if data.get("masterball",0)<=0: await interaction.response.send_message("👑 **Void King** só capturável com Master Ball!",ephemeral=True); return
            data["masterball"]-=1
        elif data.get("balls",0)<=0: await interaction.response.send_message("❌ Sem Balls!",ephemeral=True); return
        else: data["balls"]-=1; data["bossBallCD"]=3
        hr=data["bossHp"]/max(1,data["bossMaxHp"])
        cc=1.0 if boss.get("special")=="master_only" else min(0.95,0.15+(0.10 if hr<=0.5 else 0)+(0.15 if hr<=0.2 else 0)+(0.05 if data.get("defending") else 0))
        if random.random()<cc:
            bmh=data["bossMaxHp"]; bn=boss["n"]
            if bn not in data["bossDefeated"]: data["bossDefeated"].append(bn)
            bmon={"id":data["nextMonId"],"species":bn,"n":bn,"e":boss["e"],"t":"boss","level":50,"tier":5,
                  "hp":bmh,"maxHp":bmh,"atkStat":boss["atk"],"hpBoost":0,"atkBoost":0,"alive":True,"isBoss":True,"baseHp":bmh,"baseAtk":boss["atk"],"xp":0}
            data["nextMonId"]+=1
            if len(data.get("team",[]))<6: data["team"].append(bmon)
            else: data["box"].append(bmon)
            data["gold"]=data.get("gold",0)+boss.get("reward",500)
            for mat in boss.get("mats",[]): data.setdefault("materials",{})[mat["n"]]=data["materials"].get(mat["n"],0)+2
            clear_boss_state(data); write_save(self.uid,data)
            ex="\n\n# 🌟 CAPTURASTE O DEUS ABSOLUTO LEONKING! 🌟" if boss.get("special")=="final_boss" else ""
            embed=discord.Embed(title=f"✨ {boss['e']} {bn} CAPTURADO!",
                description=f"# 🎊 Incrível!{ex}\n\n⭐ Tier **5** {tier_stars(5)}\n❤️ **{bmh:,}** HP · ⚔️ **{boss['atk']:,}** ATK\n💰 +**{boss.get('reward',500):,}** ouro",
                color=0xffd700)
            await interaction.response.edit_message(embed=embed,view=None); return
        lines=[f"🌀 Ball falhou! (**{int(cc*100)}%**) · 🔮 {data.get('balls',0)}"]
        boss_counterattack(data,lines)
        if data["playerHp"]<=0: await self._defeat(interaction,data,lines); return
        write_save(self.uid,data); await interaction.response.edit_message(embed=make_boss_embed(data,"\n".join(lines)),view=self)

    @discord.ui.button(label="💊 Curar (Poções)",style=discord.ButtonStyle.success,row=1)
    async def heal(self,interaction:discord.Interaction,button:discord.ui.Button):
        if interaction.user.id!=self.uid: await interaction.response.send_message("❌",ephemeral=True); return
        data=await self._chk(interaction)
        if not data: return
        data["confirmAtk20"] = False
        items=data.get("items",{}); mhp=data.get("playerMaxHp",100); h=0; u=""; em=""
        if items.get("hyperpotion",0)>0: h=mhp; u="hyperpotion"; em="✨"
        elif items.get("megapotion",0)>0: h=int(mhp*0.5); u="megapotion"; em="💊"
        elif items.get("superpotion",0)>0: h=150; u="superpotion"; em="💚"
        elif items.get("potion",0)>0: h=60; u="potion"; em="🧪"
        else: await interaction.response.send_message("❌ Sem poções!",ephemeral=True); return
        old=data.get("playerHp",0); data["playerHp"]=min(mhp,old+h); act=data["playerHp"]-old
        items[u]-=1; data["items"]=items
        lines=[f"{em} +{act:,} HP → {data['playerHp']:,}/{mhp:,}"]
        boss_counterattack(data,lines)
        if data["playerHp"]<=0: await self._defeat(interaction,data,lines); return
        write_save(self.uid,data); await interaction.response.edit_message(embed=make_boss_embed(data,"\n".join(lines)),view=self)

    @discord.ui.button(label="🏃 Retirar",style=discord.ButtonStyle.danger,row=1)
    async def retreat(self,interaction:discord.Interaction,button:discord.ui.Button):
        if interaction.user.id!=self.uid: await interaction.response.send_message("❌",ephemeral=True); return
        data=load_clean_save(self.uid); clear_boss_state(data); write_save(self.uid,data)
        await interaction.response.edit_message(content="🏃 Recuaste da batalha!",embed=None,view=None)

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
    await interaction.response.send_message(embed=make_wild_embed(wild,data,f"Um **{wild['n']}** selvagem apareceu!"),view=BattleView(uid))

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
    ]
    for n,d in cmds: embed.add_field(name=n,value=d,inline=False)
    embed.add_field(name="⚔️ Batalha Selvagem",
        value="⚔️ **Lutar** — Ataca (cooldown 5s, inimigo contra-ataca simultaneamente!)\n🔮 **Ball** — Tenta capturar\n⭐ **Master Ball** — Captura garantida\n🏃 **Fugir**",inline=False)
    embed.add_field(name="👹 Batalha de Boss",
        value="⚔️ Atacar · 🛡️ Defender (-60% dano) · 🔮 Ball (cd 3 turnos) · 💊 Poção · 🏃 Retirar\n⚠️ A cada 3 turnos o boss carrega **Ataque Especial** (x1.8)!\n⚠️ Confirmação extra ao atacar boss <20% HP!",inline=False)
    embed.add_field(name="🤫 Segredos",
        value="🐈 **Nico** — Usa 3 Poções no **OXIGÉNIO** → `/caçar`\n👑 **Void King** — Só com Master Ball\n🌌 **Boss Final** — Pokédex completa → botão em `/pokedex`\n🐐 **Leonking** — Fase 2 do Boss Final\n📡 **Detector de Tipos** — Revela tipo do próximo monstro",inline=False)
    await interaction.response.send_message(embed=embed)

# ══════════════════════════════════════════════
# EVENTOS
# ══════════════════════════════════════════════

@bot.event
async def on_ready():
    print(f"Bot conectado: {bot.user} (ID: {bot.user.id})")
    try:
        synced=await tree.sync(); print(f"Comandos sincronizados: {len(synced)}")
        for cmd in synced: print(f"  /{cmd.name}")
    except Exception as e: print(f"Erro sync: {e}"); import traceback; traceback.print_exc()
    await bot.change_presence(activity=discord.Game(name="/ajuda | Monster Hunter RPG"))

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
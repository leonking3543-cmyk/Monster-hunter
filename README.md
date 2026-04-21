🐲 Monster Hunter RPG — Bot de Discord
Porta completa do jogo Monster Hunter RPG V117 para Discord usando slash commands e botões interativos.
---
⚙️ Instalação
1. Instalar dependências
```bash
pip install discord.py
```
2. Criar o Bot no Discord
Vai a https://discord.com/developers/applications
Clica em New Application → dá um nome
Vai a Bot → clica Add Bot
Em Privileged Gateway Intents, ativa Message Content Intent
Copia o Token do bot
Vai a OAuth2 → URL Generator:
Scopes: `bot`, `applications.commands`
Bot Permissions: `Send Messages`, `Use Slash Commands`, `Embed Links`
Abre o link gerado para adicionar o bot ao teu servidor
3. Configurar e executar
```bash
# Windows
set DISCORD_TOKEN=o_teu_token_aqui
python bot.py

# Linux/Mac
export DISCORD_TOKEN="o_teu_token_aqui"
python bot.py
```
---
🎮 Comandos
Comando	Descrição
`/ajuda`	Lista todos os comandos
`/caçar`	Encontra um monstro selvagem
`/equipa`	Vê a tua equipa (até 6 monstros)
`/box`	Vê os monstros na box
`/ativar [pos]`	Define o monstro ativo (1-6)
`/curar [tipo]`	Cura o monstro (poção/superpoção/megapoção/revive/maxrevive)
`/inventário`	Vê itens, ouro e materiais
`/loja`	Compra itens com ouro
`/usar [item]`	Usa item no monstro ativo
`/pokedex`	Vê monstros capturados
`/boss [nome?]`	Enfrenta um boss
`/bosses`	Lista todos os bosses
`/trocar [ação] [nome]`	Troca monstros entre equipa e box
`/perfil`	Vê o perfil completo
`/ranked`	Rank e leaderboard
`/ranked-import [código]`	Adiciona amigo ao leaderboard
`/nomear [nome]`	Define nome no ranked
`/rebirth`	Rebirth (custa 10.000💰)
---
🐲 Sistema de Batalha
Monstros Selvagens (botões):
⚔️ Lutar — Ataca o monstro (aumenta chance de captura)
🔮 Ball — Tenta capturar
⭐ Master Ball — Captura garantida
🏃 Fugir — Foge da batalha
Batalha de Boss (botões):
⚔️ Atacar — Ataca o boss
🛡️ Defender — Reduz dano recebido (30-60%)
🔮 Tentar Capturar — Chance de capturar o boss
🏃 Retirar — Foge da batalha
---
📦 Dados do Jogo
Cada jogador tem o seu save independente em `saves/<user_id>.json`.
27 tipos de monstros (fogo, água, planta, terra, ar, gelo, trovão, sombra, cristal, veneno, som, tempo, luz, cosmos, metal, fantasma, dragão, fada, psíquico, luta, inseto, néon, nuclear, espírito, mecânico, ventos, magma, arcano)
405+ monstros captitráveis + 3 especiais divinos
29 bosses com mecânicas únicas
Tabela de vantagens/desvantagens por tipo
Sistema de Tier (1-5, afeta stats)
Sistema de XP e Níveis (máx 1000)
ELO Ranked com leaderboard por código
---
🗂️ Estrutura
```
monster_hunter_bot/
├── bot.py          # Bot principal
├── requirements.txt
├── README.md
└── saves/          # Criado automaticamente
    └── <user_id>.json
```

import os
import json
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# === CONFIG ===
ROLE_YOK2 = 1386349220683972618
ROLE_YOK3 = 1386350165073592340
ROLE_YOK4 = 1386350406027706549
ROLE_PREMIUM = 1356933506898333707
ROLE_YOK5 = 1390647923288834110

CHANNEL_PROGRESS = 1389939258676088953
CHANNEL_BONUS = 1390648831234015352
LOG_CHANNEL_ID = 1356684226384101467  # Salon log DMs

COLOR_ORANGE = 0xfd9f05
TIMESTAMP_FILE = "role_timestamps.json"

DELAY_STEPS = [
    (timedelta(days=3), "72h"),
    (timedelta(days=7), "1 semaine"),
    (timedelta(days=30), "1 mois"),
    (timedelta(days=60), "2 mois"),
    (timedelta(days=90), "3 mois"),
    (timedelta(days=120), "4 mois"),
    (timedelta(days=150), "5 mois"),
    (timedelta(days=180), "6 mois"),
    (timedelta(days=210), "7 mois"),
    (timedelta(days=240), "8 mois"),
    (timedelta(days=270), "9 mois"),
    (timedelta(days=300), "10 mois"),
    (timedelta(days=330), "11 mois"),
    (timedelta(days=365), "12 mois"),
]

DM_MESSAGES = {
    "yok1_24h": "Salut ! N'oublie pas de regarder ta première vidéo et de valider ton round dans le salon Portes d'entrée pour débloquer Yók Thîi 2 et continuer ton accompagnement ! 💥",
    "yok2_24h": "Hey ! Tu peux maintenant débloquer Yók Thîi 3 ! Valide le salon No Pain No Muay pour continuer ta progression 💪",
    "yok3_24h": "🔥 Tu as super bien avancé ! Valide Yók Thîi 3 et accéder à la suite !",
    "post_yok4_24h": "Salut ! Je vois que tu prends au sérieux ton projet de séjour en Thaïlande. Afin de mieux t'accompagner au mieux, je te propose de réserver un appel gratuit avec moi ici : https://yokacademy.fr/rdv-saiyok 💪 On pourra discuter de tes objectifs, de ton budget, de tes difficultés et trouver des solutions ensemble !",
    "post_yok4_48h": "Jette un œil à ça, un abonné s'est rendu en Thaïlande sans avoir jamais boxé et a décroché un combat au bout de quelques jours ! Une interview inspirante : https://yokacademy.fr/itw-abo 🙏"
}

# === UTIL ===
def load_timestamps():
    if os.path.exists(TIMESTAMP_FILE):
        with open(TIMESTAMP_FILE, "r") as f:
            return json.load(f)
    return {}

def save_timestamps(data):
    with open(TIMESTAMP_FILE, "w") as f:
        json.dump(data, f)

async def send_dm_safe(member, message, context=""):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    try:
        await member.send(message)
        if log_channel:
            await log_channel.send(f"✅ DM envoyé à {member.mention} pour **{context}**")
        return True
    except discord.Forbidden:
        if log_channel:
            await log_channel.send(f"❌ DM refusé par {member.mention} pour **{context}** (DM désactivé ?)")
        return False
    except Exception as e:
        if log_channel:
            await log_channel.send(f"⚠️ Erreur DM {member.mention} ({context}) : `{e}`")
        return False

# === EVENTS ===
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    check_relances.start()

@bot.event
async def on_member_update(before, after):
    before_roles = {r.id for r in before.roles}
    after_roles = {r.id for r in after.roles}
    new_roles = after_roles - before_roles

    timestamps = load_timestamps()
    uid = str(after.id)

    niveau_roles = {
        ROLE_YOK2: ("yok2", "Yok 2", "<#1386343269859987476>"),
        ROLE_YOK3: ("yok3", "Yok 3", "<#1386343994287456428>"),
        ROLE_YOK4: ("yok4", "Yok 4", "<#1356961119377428594>")
    }

    for role_id in new_roles:
        if role_id in niveau_roles:
            key, name, next_channel = niveau_roles[role_id]
            if uid not in timestamps:
                timestamps[uid] = {}
            timestamps[uid][key] = datetime.now(timezone.utc).isoformat()
            save_timestamps(timestamps)

            embed = discord.Embed(
                title=f"🎖️ {after.display_name} a atteint le niveau {name} !",
                description=f"Tu peux maintenant accéder au salon {next_channel} !",
                color=COLOR_ORANGE
            )
            embed.set_footer(text="Continue comme ça, champion ! 🥊")
            channel = bot.get_channel(CHANNEL_PROGRESS)
            await channel.send(f"{after.mention}", allowed_mentions=discord.AllowedMentions(users=True))
            await channel.send(embed=embed)

# === RELANCES ===
@tasks.loop(hours=24)
async def check_relances():
    now = datetime.now(timezone.utc)
    timestamps = load_timestamps()

    for guild in bot.guilds:
        for member in guild.members:
            if member.bot:
                continue

            uid = str(member.id)
            roles = {r.id for r in member.roles}
            joined = member.joined_at or now

            try:
                # Yok2 - DM 24h après arrivée
                if ROLE_YOK2 not in roles and timedelta(hours=24) <= now - joined < timedelta(hours=48):
                    await send_dm_safe(member, DM_MESSAGES["yok1_24h"], context="yok1_24h")

                # Yok3 - DM 24h après rôle Yok2
                elif ROLE_YOK2 in roles and ROLE_YOK3 not in roles:
                    if uid in timestamps and "yok2" in timestamps[uid]:
                        r_time = datetime.fromisoformat(timestamps[uid]["yok2"])
                        if timedelta(hours=24) <= now - r_time < timedelta(hours=48):
                            await send_dm_safe(member, DM_MESSAGES["yok2_24h"], context="yok2_24h")

                # Yok4 - DM 24h après rôle Yok3
                elif ROLE_YOK3 in roles and ROLE_YOK4 not in roles:
                    if uid in timestamps and "yok3" in timestamps[uid]:
                        r_time = datetime.fromisoformat(timestamps[uid]["yok3"])
                        if timedelta(hours=24) <= now - r_time < timedelta(hours=48):
                            await send_dm_safe(member, DM_MESSAGES["yok3_24h"], context="yok3_24h")

                # Premium - DM 24h + 48h après rôle Yok4
                elif ROLE_YOK4 in roles and ROLE_PREMIUM not in roles:
                    if uid in timestamps and "yok4" in timestamps[uid]:
                        r_time = datetime.fromisoformat(timestamps[uid]["yok4"])
                        if timedelta(hours=24) <= now - r_time < timedelta(hours=48):
                            await send_dm_safe(member, DM_MESSAGES["post_yok4_24h"], context="post_yok4_24h")
                        elif timedelta(hours=48) <= now - r_time < timedelta(hours=72):
                            await send_dm_safe(member, DM_MESSAGES["post_yok4_48h"], context="post_yok4_48h")

                # Ajout Yok5 après 72h si pas Premium (sans message bonus)
                if ROLE_YOK4 in roles and ROLE_PREMIUM not in roles and ROLE_YOK5 not in roles:
                    if uid in timestamps and "yok4" in timestamps[uid]:
                        r_time = datetime.fromisoformat(timestamps[uid]["yok4"])
                        if now - r_time >= timedelta(hours=72):
                            await member.add_roles(discord.Object(id=ROLE_YOK5))
                            # Pas besoin d'envoyer de message ici, le salon bonus est déjà configuré avec l'embed.

                # Relances publiques
                progression_channel = bot.get_channel(CHANNEL_PROGRESS)
                public_check = [
                    (ROLE_YOK2, "yok2", "Yok 2", "<#1356633471665180802>", ROLE_YOK3),
                    (ROLE_YOK3, "yok3", "Yok 3", "<#1386343269859987476>", ROLE_YOK4),
                    (ROLE_YOK4, "yok4", "Yok 4", "<#1386343994287456428>", ROLE_PREMIUM),
                ]

                for role, key, objectif, salon, next_role in public_check:
                    if role in roles and next_role not in roles and uid in timestamps and key in timestamps[uid]:
                        r_time = datetime.fromisoformat(timestamps[uid][key])
                        for delay, label in DELAY_STEPS:
                            if abs((now - r_time - delay).total_seconds()) < 3600:
                                await progression_channel.send(
                                    f"{member.mention} N'oublie pas de valider ta progression dans {salon} pour obtenir le niveau **{objectif}** et continuer ton accompagnement ! 💪",
                                    allowed_mentions=discord.AllowedMentions(users=True)
                                )
                                break

            except discord.Forbidden:
                continue

bot.run(os.getenv("DISCORD_TOKEN"))

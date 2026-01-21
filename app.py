import discord
from discord.ext import commands
from discord.ui import Select, View, Button
import asyncio
import logging
import json
import os
import datetime

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = 'Dein_Token'
LOG_CHANNEL_ID = 
ADMIN_ROLE_ID = 
OWNER_ROLE_ID = 
VERIFIED_ROLE_ID =   # Bitte mit der echten ID ersetzen

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True

bot = commands.Bot(command_prefix="/", intents=intents)


ticket_counter = 2
active_tickets = set()
user_ticket_map = {}
message_cache = {}

blocked_users = set()

BANNER_URL = ""
LOGO_URL = ""

TICKET_DATA_FILE = "ticket_data.json"


def save_active_tickets():
    data = {
        "ticket_counter": ticket_counter,
        "active_tickets": list(active_tickets),
        "user_ticket_map": user_ticket_map,
        "blocked_users": list(blocked_users)
    }
    with open(TICKET_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

def load_active_tickets():
    global ticket_counter, active_tickets, user_ticket_map, blocked_users
    if os.path.exists(TICKET_DATA_FILE):
        with open(TICKET_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            ticket_counter = data.get("ticket_counter", 1)
            active_tickets = set(data.get("active_tickets", []))
            user_ticket_map = data.get("user_ticket_map", {})
            blocked_users = set(data.get("blocked_users", []))


# Kategorie-Beschreibungen für Tickets
CATEGORY_DESCRIPTIONS = {
    "Support": "🛠️ **Support-Ticket**\nHier kannst du allgemeine Support-Fragen stellen. Unser Team wird sich so schnell wie möglich um dein Anliegen kümmern.",
    "Report": "🚨 **Report-Ticket**\nMelde Spieler, die gegen unsere Regeln verstoßen haben. Bitte gib möglichst viele Details an.",
    "Unban": "🔓 **Unban-Ticket**\nStelle einen Entbannungsantrag hier. Beschreibe warum dein Ban aufgehoben werden sollte.",
    "Bewerbung": "📋 **Bewerbungs-Ticket**\nBewirb dich für unser Team. Stelle sicher, dass du alle Anforderungen erfüllst.",
    "Administration": "⚖️ **Administrations-Ticket**\nKontaktiere die Projektleitung bei wichtigen Anliegen oder Problemen mit Teammitgliedern."
}

CATEGORY_ID_MAP = {
    "Support": ,
    "Report": ,
    "Unban": ,
    "Bewerbung": ,
    "Administration": ,
}

ROLE_ID_MAP = {
    "Support": ,
    "Report": ,
    "Unban": ,
    "Bewerbung": ,
    "Administration": ,
}

BEANSPRUCHUNGS_ROLE_ID = {
    "Support": ,
    "Report": ,
    "Unban": ,
    "Bewerbung": ,
    "Administration": ,
}


def sanitize_channel_name(name: str) -> str:
    # Erlaubt nur Kleinbuchstaben, Zahlen und Bindestriche
    import re
    name = name.lower()
    name = re.sub(r'[^a-z0-9-]', '-', name)
    name = re.sub(r'-+', '-', name)
    return name.strip('-')


async def create_ticket(interaction: discord.Interaction, category: str, followup):
    global ticket_counter
    guild = interaction.guild
    uid = interaction.user.id

    # Blockierte User dürfen kein Ticket erstellen
    if uid in blocked_users:
        warn_embed = discord.Embed(
            title="🚫 Zugriff verweigert",
            description="Du wurdest für die Ticket-Erstellung blockiert und kannst kein Ticket öffnen.",
            color=discord.Color.red()
        )
        await followup.send(embed=warn_embed, ephemeral=True)
        return

    # Verifizierung prüfen
    verified_role = guild.get_role(VERIFIED_ROLE_ID)
    if not verified_role or verified_role not in interaction.user.roles:
        warn_embed = discord.Embed(
            title="❌ Verifizierung erforderlich",
            description="Du musst verifiziert sein, um ein Ticket zu öffnen.",
            color=discord.Color.red()
        )
        await followup.send(embed=warn_embed, ephemeral=True)
        return

    # Maximal 2 Tickets pro User gleichzeitig
    user_tickets = user_ticket_map.get(uid, [])
    if len(user_tickets) >= 2:
        warn_embed = discord.Embed(
            title="❌ Ticket-Limit erreicht",
            description="Du kannst maximal 2 offene Tickets gleichzeitig haben.",
            color=discord.Color.red()
        )
        await followup.send(warn_embed, ephemeral=True)
        return

    role_id = ROLE_ID_MAP.get(category)
    cat_role = guild.get_role(role_id) if role_id else None
    category_obj = discord.utils.get(guild.categories, id=CATEGORY_ID_MAP.get(category))

    # Setze die Berechtigungen so, dass nur der Ersteller und das Team den Kanal sehen können
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False, view_channel=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)
    }

    # Füge Berechtigungen für die Team-Rolle hinzu
    if cat_role:
        overwrites[cat_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)

    # Füge Berechtigungen für Admin- und Owner-Rollen hinzu
    admin_role = guild.get_role(ADMIN_ROLE_ID)
    owner_role = guild.get_role(OWNER_ROLE_ID)
    if admin_role:
        overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)
    if owner_role:
        overwrites[owner_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)

    # Kanalname nach Nutzername + Ticketnummer
    sanitized_name = sanitize_channel_name(interaction.user.name)
    channel_name = f"ticket-{sanitized_name}-{ticket_counter}"
    ticket_counter += 1
    save_active_tickets()

    ch = await guild.create_text_channel(
        channel_name,
        overwrites=overwrites,
        category=category_obj,
        topic=f"Ticket Kategorie: {category}"
    )

    active_tickets.add(ch.id)
    # Füge das neue Ticket zur Liste des Users hinzu
    user_ticket_map.setdefault(uid, []).append(ch.id)
    save_active_tickets()  # Speichere Änderungen

    # Bereite die Willkommensnachricht für den Ticket-Kanal vor
    ticket_embed = discord.Embed(
        title=f"Ticket: {category}",
        description=f"**📋 Kategorie:** {category}\n{CATEGORY_DESCRIPTIONS.get(category, 'Keine Beschreibung verfügbar.')}\n\n" +
                   f"Willkommen {interaction.user.mention}! 👋\n",
        color=discord.Color.blue()
    )

    # Füge Teammitglieder-Erwähnungen hinzu
    if category == "Administration":
        admin_role = guild.get_role(ADMIN_ROLE_ID)
        owner_role = guild.get_role(OWNER_ROLE_ID)
        mentions = []
        if owner_role:
            mentions.append(owner_role.mention)
        if admin_role:
            mentions.append(admin_role.mention)
        ticket_embed.add_field(name="Status", value=f"**Administration-Ticket erstellt!** {' '.join(mentions)} bitte bearbeiten.", inline=False)
    elif cat_role:
        ticket_embed.add_field(name="Status", value=f"**{category}-Ticket erstellt!** {cat_role.mention}, bitte übernehmen!", inline=False)
    else:
        ticket_embed.add_field(name="Status", value=f"**{category}-Ticket erstellt!** (Kategorie-Rolle fehlt ⚠️)", inline=False)

    ticket_embed.set_thumbnail(url=LOGO_URL)
    ticket_embed.set_image(url=BANNER_URL)
    ticket_embed.set_footer(text="Support System v3.6")

    # Sende die Willkommensnachricht in den Ticket-Kanal
    await ch.send(embed=ticket_embed, view=TicketManagementView(category, claimed=False))

    # Sende einen Link zum Ticket-Kanal als ephemeral Antwort mit Button
    ticket_link = f"Hier ist dein Ticket: {ch.mention}"
    await followup.send(content=ticket_link, view=TicketLinkView(ch), ephemeral=True)

# -------------- Buttons & Views --------------
class CloseTicketButton(Button):
    def __init__(self):
        super().__init__(label="🔒 Ticket schließen", style=discord.ButtonStyle.danger, custom_id="close_ticket")

    async def callback(self, interaction: discord.Interaction):
        ch = interaction.channel
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("🔒 Ticket wird in 5 Sekunden geschlossen...", ephemeral=True)
        await asyncio.sleep(5)

        logs = message_cache.pop(ch.id, [])
        transcript_file = f"ticket_transcript_{ch.id}.txt"
        # Falls Cache leer ist, lade aus Datei
        if not logs and os.path.exists(transcript_file):
            with open(transcript_file, "r", encoding="utf-8") as f:
                logs = [line.rstrip() for line in f]
        log_ch = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if logs and log_ch:
            await log_ch.send(f"📋 Transkript von {ch.name}")
            # Sende die Logs in Blöcken von max. 2000 Zeichen
            block = ""
            for line in logs:
                # Prüfe, ob Hinzufügen der Zeile den Block zu lang machen würde
                if len(block) + len(line) + 1 > 1994:  # 1994 wegen 6 Zeichen für die Backticks
                    await log_ch.send(f"```{block}```")
                    block = ""
                block += line + "\n"
            if block:
                await log_ch.send(f"```{block}```")
        # Lösche die Transkriptdatei
        if os.path.exists(transcript_file):
            os.remove(transcript_file)

        # --- Ticket aus user_ticket_map entfernen (auch bei mehreren Tickets pro User) ---
        for user_id, channels in list(user_ticket_map.items()):
            if ch.id in channels:
                user_ticket_map[user_id] = [cid for cid in channels if cid != ch.id]
        active_tickets.discard(ch.id)
        save_active_tickets()  # Speichere Änderungen
        await ch.delete()


class ClaimTicketButton(Button):
    def __init__(self, category: str):
        super().__init__(label="🏷️ Ticket beanspruchen", style=discord.ButtonStyle.success, custom_id=f"claim_{category}")
        self.category = category

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        guild = interaction.guild
        req_role = guild.get_role(ROLE_ID_MAP.get(self.category))
        if req_role and req_role in user.roles:
            await interaction.response.defer(ephemeral=True)
            await interaction.followup.send(f"✅ Das Ticket wurde erfolgreich beansprucht!", ephemeral=True)
            await interaction.channel.send(embed=discord.Embed(
                title="🏷️ Ticket beansprucht",
                description=f"{user.mention} bearbeitet dieses Ticket.",
                color=discord.Color.green()
            ))
            await interaction.message.edit(view=TicketManagementView(self.category, claimed=True))
        else:
            await interaction.response.defer(ephemeral=True)
            await interaction.followup.send("❌ Du hast keine Berechtigung dafür.", ephemeral=True)


class UnclaimTicketButton(Button):
    def __init__(self, category: str):
        super().__init__(label="❌ Ticket freigeben", style=discord.ButtonStyle.secondary, custom_id=f"unclaim_{category}")
        self.category = category

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("✅ Ticket wurde freigegeben.", ephemeral=True)
        await interaction.channel.send(embed=discord.Embed(
            title="❌ Ticket freigegeben",
            description=f"{user.mention} bearbeitet dieses Ticket nicht mehr.",
            color=discord.Color.red()
        ))
        await interaction.message.edit(view=TicketManagementView(self.category, claimed=False))


class TicketManagementView(View):
    def __init__(self, category: str, claimed=False):
        super().__init__(timeout=None)
        self.add_item(CloseTicketButton())
        if claimed:
            self.add_item(UnclaimTicketButton(category))
        else:
            self.add_item(ClaimTicketButton(category))


class TicketDropdown(Select):
    def __init__(self):
        opts = [
            discord.SelectOption(
                label="Support",
                description="Stelle allgemeine Support-Fragen an unser Team",
                emoji="🛠️"
            ),
            discord.SelectOption(
                label="Report",
                description="Melde Spieler, die gegen unsere Regeln verstoßen haben",
                emoji="🚨"
            ),
            discord.SelectOption(
                label="Unban",
                description="Stelle einen Entbannungsantrag und erkläre deine Situation",
                emoji="🔓"
            ),
            discord.SelectOption(
                label="Bewerbung",
                description="Bewirb dich für eine Position in unserem Team",
                emoji="📋"
            ),
            discord.SelectOption(
                label="Administration",
                description="Kontaktiere die Projektleitung bei wichtigen Anliegen",
                emoji="⚖️"
            ),
        ]
        super().__init__(placeholder="Wähle eine Kategorie", min_values=1, max_values=1, options=opts, custom_id="ticket_dropdown")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        category = self.values[0]
        await create_ticket(interaction, category, interaction.followup)


class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())


class TicketLinkButton(Button):
    def __init__(self, channel):
        super().__init__(label="Zum Ticket", style=discord.ButtonStyle.link, url=f"https://discord.com/channels/{channel.guild.id}/{channel.id}")


class TicketLinkView(View):
    def __init__(self, channel):
        super().__init__(timeout=None)
        self.add_item(TicketLinkButton(channel))

# -------------- Slash Command --------------
@bot.tree.command(name="ticket", description="Erstelle ein Ticket")
async def ticket_slash(inter: discord.Interaction):
    em = discord.Embed(
        title="🎫 Ticket Support System",
        description="Wähle eine Kategorie für dein Ticket:\n\n📋 Verfügbare Kategorien:\n• 🛠️ Support - Allgemeine Fragen\n• 🚨 Report - Spieler melden\n• 🔓 Unban - Entbannung beantragen\n• 📋 Bewerbung - Team-Bewerbung\n• ⚖️ Administration - Projektleitung",
        color=discord.Color.blue()
    )
    em.set_thumbnail(url=LOGO_URL)
    em.set_image(url=BANNER_URL)
    await inter.response.send_message(embed=em, view=TicketView())  # Korrigiert: send statt send_message

# --- NEU: User zu Ticket hinzufügen ---
@bot.tree.command(name="ticket_add", description="Füge einen User zu diesem Ticket hinzu")
@discord.app_commands.describe(user="Der User, der hinzugefügt werden soll")
async def ticket_add(inter: discord.Interaction, user: discord.Member):
    await inter.response.defer(ephemeral=True)

    if inter.channel.id not in active_tickets:
        await inter.followup.send("❌ Dieser Befehl kann nur in einem Ticket-Kanal verwendet werden.", ephemeral=True)
        return
    # Berechtigung hinzufügen
    await inter.channel.set_permissions(user, read_messages=True, send_messages=True, view_channel=True)
    await inter.followup.send(f"✅ {user.mention} wurde zum Ticket hinzugefügt!", ephemeral=True)
    await inter.channel.send(f"{user.mention} wurde zum Ticket hinzugefügt.")

# --- NEU: User aus Ticket entfernen ---
@bot.tree.command(name="ticket_remove", description="Entferne einen User aus diesem Ticket")
@discord.app_commands.describe(user="Der User, der entfernt werden soll")
async def ticket_remove(inter: discord.Interaction, user: discord.Member):
    await inter.response.defer(ephemeral=True)

    if inter.channel.id not in active_tickets:
        await inter.followup.send("❌ Dieser Befehl kann nur in einem Ticket-Kanal verwendet werden.", ephemeral=True)
        return
    # Berechtigung entfernen
    await inter.channel.set_permissions(user, overwrite=None)
    await inter.followup.send(f"✅ {user.mention} wurde aus dem Ticket entfernt!", ephemeral=True)
    await inter.channel.send(f"{user.mention} wurde aus dem Ticket entfernt.")

# --- User für Ticket-Erstellung blockieren ---
@bot.tree.command(name="ticket_block", description="Blockiere einen User für die Ticket-Erstellung")
@discord.app_commands.describe(user="Der User, der blockiert werden soll")
async def ticket_block(inter: discord.Interaction, user: discord.Member):
    # Nur Admins/Owner dürfen blockieren
    admin_role = inter.guild.get_role(ADMIN_ROLE_ID)
    owner_role = inter.guild.get_role(OWNER_ROLE_ID)
    if admin_role not in inter.user.roles and owner_role not in inter.user.roles:
        await inter.response.send_message("❌ Du hast keine Berechtigung für diesen Befehl.", ephemeral=True)
        return
    blocked_users.add(user.id)
    save_active_tickets()
    await inter.response.send_message(f"🚫 {user.mention} wurde für die Ticket-Erstellung blockiert!", ephemeral=True)

# --- User für Ticket-Erstellung entblocken ---
@bot.tree.command(name="ticket_unblock", description="Entblockiere einen User für die Ticket-Erstellung")
@discord.app_commands.describe(user="Der User, der entblockt werden soll")
async def ticket_unblock(inter: discord.Interaction, user: discord.Member):
    admin_role = inter.guild.get_role(ADMIN_ROLE_ID)
    owner_role = inter.guild.get_role(OWNER_ROLE_ID)
    if admin_role not in inter.user.roles and owner_role not in inter.user.roles:
        await inter.response.send_message("❌ Du hast keine Berechtigung für diesen Befehl.", ephemeral=True)
        return
    blocked_users.discard(user.id)
    save_active_tickets()
    await inter.response.send_message(f"✅ {user.mention} kann wieder Tickets erstellen!", ephemeral=True)

# -------------- Keep Alive --------------
async def keep_alive():
    while True:
        await asyncio.sleep(300)  # Alle 5 Minuten
        logging.info("Keep-alive ping")

# -------------- on_ready --------------
@bot.event
async def on_ready():
    print(f"🤖 {bot.user} ist online!")
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} Slash Commands synchronisiert.")
    except Exception as e:
        print(f"❌ Fehler beim Synchronisieren: {e}")

    bot.add_view(TicketView())
    for cat in CATEGORY_ID_MAP.keys():
        bot.add_view(TicketManagementView(cat, claimed=False))
        bot.add_view(TicketManagementView(cat, claimed=True))

    asyncio.create_task(keep_alive())
    logging.info("Bot ist vollständig gestartet und bereit!")

# Lade die Daten beim Start des Bots
load_active_tickets()

@bot.event
async def on_message(message):
    # Nachrichten nur in aktiven Ticket-Kanälen cachen und persistent speichern
    if message.channel.id in active_tickets and not message.author.bot:
        logs = message_cache.setdefault(message.channel.id, [])
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message.author.display_name}: {message.content}"
        logs.append(log_entry)
        # Schreibe die Nachricht persistent in eine Datei
        transcript_file = f"ticket_transcript_{message.channel.id}.txt"
        with open(transcript_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    await bot.process_commands(message)

# -------------- Start Bot --------------
bot.run(BOT_TOKEN)
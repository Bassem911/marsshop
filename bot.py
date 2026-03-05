import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import os
from datetime import datetime

# ---------------- CONFIG ----------------
TOKEN = "MTQ3ODM1MjA2NjY0NzgyMjQzOQ.GlO6Y4.kRrv1mFA-h_LxEEJmQZBlDQ6A3fzl900OIqX6w"

AVIS_CHANNEL_ID = 1478709726077390938
LOG_AVIS_CHANNEL_ID = 1479021622764769397
BOT_LOG_CHANNEL_ID = 1478880005269491804
COMMENT_FR = 1478182861629820928
COMMENT_EN = 1479031245093601372

IMAGE_AVIS = "https://img.freepik.com/free-vector/tropic-summer-party-banner-template_107791-31547.jpg"
DATA_FILE = "data.json"

# ---------------- INTENTS ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- DATA ----------------
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
else:
    data = {"counter": 0, "avis": [], "fiches": []}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ---------------- UTIL ----------------
def etoiles(nb):
    try:
        nb = int(nb)
    except:
        nb = 1
    if nb < 1: nb = 1
    if nb > 5: nb = 5
    return "⭐"*nb

async def log_bot(message):
    channel = bot.get_channel(BOT_LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title="🤖 Log Bot", description=message, color=discord.Color.orange())
        await channel.send(embed=embed)

async def update_compteur(message):
    embed = discord.Embed(
        title="🌟 Google Avis - MarsShop",
        description=f"📊 **Avis validés : {data['counter']}**\n\nClique sur **⭐ Faire un avis** pour commencer.",
        color=discord.Color.red()
    )
    embed.set_image(url=IMAGE_AVIS)
    await message.edit(embed=embed)

# ---------------- MODALS ----------------
class AjoutAvisModal(discord.ui.Modal, title="Ajouter une fiche avis"):
    entreprise = discord.ui.TextInput(label="Entreprise")
    lien = discord.ui.TextInput(label="Lien")
    commentaire = discord.ui.TextInput(label="Commentaire", style=discord.TextStyle.paragraph)
    etoile = discord.ui.TextInput(label="Étoiles (1-5)")

    async def on_submit(self, interaction: discord.Interaction):
        fiche = {
            "id": str(datetime.utcnow().timestamp()),
            "entreprise": self.entreprise.value,
            "lien": self.lien.value,
            "commentaire": self.commentaire.value,
            "etoile": etoiles(self.etoile.value)
        }
        data["fiches"].append(fiche)
        save_data()
        await interaction.response.send_message("✅ Fiche ajoutée avec succès.", ephemeral=True)

class RefusModal(discord.ui.Modal, title="Motif du refus"):
    motif = discord.ui.TextInput(label="Motif du refus", style=discord.TextStyle.paragraph)
    def __init__(self, user: discord.User):
        super().__init__()
        self.user = user

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="❌ Avis refusé",
            description=f"Votre avis a été refusé.\n\n📌 **Motif :**\n{self.motif.value}\n\nMerci de refaire un nouvel avis.",
            color=discord.Color.red()
        )
        await self.user.send(embed=embed)
        await interaction.response.send_message("❌ Refus envoyé.", ephemeral=True)

class RemplirFicheModal(discord.ui.Modal, title="Remplir la fiche"):
    email = discord.ui.TextInput(label="Email (gmail / hotmail)")
    lien = discord.ui.TextInput(label="Lien du commentaire")
    qualite = discord.ui.TextInput(label="Qualité du service (1-5)")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "📸 **Capture obligatoire**\nMerci d'envoyer **juste après ce message** la capture d'écran de votre avis.",
            ephemeral=True
        )

        def check(m):
            return m.author == interaction.user and m.attachments

        try:
            msg = await bot.wait_for("message", timeout=600, check=check)
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Temps dépassé. Merci de recommencer.", ephemeral=True)
            return

        image = msg.attachments[0].url

        avis = {
            "id": str(datetime.utcnow().timestamp()),
            "user": interaction.user.id,
            "email": self.email.value,
            "lien": self.lien.value,
            "qualite": self.qualite.value,
            "image": image
        }
        data["avis"].append(avis)
        data["counter"] += 1
        save_data()

        embed = discord.Embed(title="📩 Nouvel avis reçu", color=discord.Color.blurple())
        embed.add_field(name="👤 Utilisateur", value=interaction.user.mention)
        embed.add_field(name="📧 Email", value=self.email.value, inline=False)
        embed.add_field(name="🔗 Lien", value=self.lien.value, inline=False)
        embed.add_field(name="⭐ Qualité", value=f"{self.qualite.value}/5")
        embed.set_image(url=image)

        # --- Log avec boutons accept/refuse ---
        log_channel = bot.get_channel(LOG_AVIS_CHANNEL_ID)
        await log_channel.send(embed=embed, view=LogView(interaction.user))

        await log_bot(f"{interaction.user} a créé un avis.")

        # --- Update compteur principal ---
        main_msg = await bot.get_channel(AVIS_CHANNEL_ID).send(embed=embed)
        await update_compteur(main_msg)

        await interaction.followup.send("✅ Avis envoyé avec la capture.", ephemeral=True)

# ---------------- LOG VIEW ----------------
class LogView(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=None)
        self.user = user

    @discord.ui.button(label="✅ Accepter", style=discord.ButtonStyle.success)
    async def accepter(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="✅ Avis accepté",
            description="Votre avis a été validé.\n\n💰 Merci de créer un ticket pour recevoir votre paiement sous **24h**.",
            color=discord.Color.green()
        )
        await self.user.send(embed=embed)
        await interaction.response.send_message("✅ Avis accepté et utilisateur notifié.", ephemeral=True)

    @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.danger)
    async def refuser(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RefusModal(self.user))

# ---------------- VIEWS PERSISTANTES ----------------
class RemplirView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Remplir la fiche", style=discord.ButtonStyle.primary)
    async def remplir(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RemplirFicheModal())

class AvisView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⭐ Faire un avis", style=discord.ButtonStyle.danger)
    async def faire_avis(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not data.get("fiches"):
            await interaction.response.send_message("❌ Aucune fiche disponible actuellement.", ephemeral=True)
            return
        fiche = data["fiches"].pop(0)
        save_data()
        await log_bot(f"{interaction.user} a cliqué sur Faire un avis dans <#{AVIS_CHANNEL_ID}>")

        embed = discord.Embed(
            title="📋 Fiche Avis",
            color=discord.Color.gold(),
            description=f"🏢 **Entreprise**\n{fiche['entreprise']}\n\n🔗 **Lien**\n{fiche['lien']}\n\n💬 **Commentaire**\n{fiche['commentaire']}\n\n⭐ **Étoiles**\n{fiche['etoile']}"
        )
        await interaction.user.send(embed=embed, view=RemplirView())
        await interaction.response.send_message("📩 Vérifie tes **messages privés**.", ephemeral=True)

    @discord.ui.button(label="📖 Comment faire", style=discord.ButtonStyle.secondary)
    async def comment(self, interaction: discord.Interaction, button: discord.ui.Button):
        row = discord.ui.View(timeout=None)
        row.add_item(discord.ui.Button(label="Français", style=discord.ButtonStyle.link,
                                       url=f"https://discord.com/channels/{interaction.guild.id}/{COMMENT_FR}"))
        row.add_item(discord.ui.Button(label="English", style=discord.ButtonStyle.link,
                                       url=f"https://discord.com/channels/{interaction.guild.id}/{COMMENT_EN}"))
        await interaction.response.send_message("📖 Choisis la langue :", view=row, ephemeral=True)

# ---------------- COMMANDES ----------------
@bot.tree.command(name="ajout_avis")
async def ajout_avis(interaction: discord.Interaction):
    role = discord.utils.get(interaction.guild.roles, name="⚜️∙Fondateur")
    if role not in interaction.user.roles:
        await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)
        return
    await interaction.response.send_modal(AjoutAvisModal())

@bot.tree.command(name="voir_stock")
async def voir_stock(interaction: discord.Interaction):
    role = discord.utils.get(interaction.guild.roles, name="⚜️∙Fondateur")
    if role not in interaction.user.roles:
        await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)
        return
    if not data["avis"]:
        await interaction.response.send_message("📦 Aucun avis stocké pour le moment.", ephemeral=True)
        return
    msg = "📦 **Avis stockés :**\n"
    for i, avis in enumerate(data["avis"], start=1):
        msg += f"{i}. User: <@{avis['user']}> | Email: {avis['email']} | Lien: {avis['lien']} | Qualité: {avis['qualite']}/5\n"
    await interaction.response.send_message(msg, ephemeral=True)

# ---------------- READY + View persistantes ----------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot prêt.")

    channel = bot.get_channel(AVIS_CHANNEL_ID)
    if not channel:
        print("Salon AVIS_CHANNEL_ID introuvable !")
        return

    # Créer l'embed principal
    embed = discord.Embed(
        title="🌟 Google Avis - MarsShop",
        description=f"📊 **Avis validés : {data['counter']}**\n\nClique sur **⭐ Faire un avis** pour commencer.",
        color=discord.Color.red()
    )
    embed.set_image(url=IMAGE_AVIS)

    # --- Récupérer message principal existant ---
    main_msg = None
    try:
        if "message_id" in data:
            main_msg = await channel.fetch_message(data["message_id"])
            await main_msg.edit(embed=embed, view=AvisView())  # Ré-attacher la view
    except:
        main_msg = None

    # --- Si pas trouvé, envoyer nouveau message ---
    if not main_msg:
        main_msg = await channel.send(embed=embed, view=AvisView())
        data["message_id"] = main_msg.id
        save_data()

bot.run(TOKEN)

``` mesaj ```  
şu şekilde **kutu (code block)** içinde göndersin!

---

Senin istediğin gibi, gönderdiğimiz **bütün mesajları**  
otomatik olarak **üçlü ``` içine alıp kutulu** göstereceğim.

Kodları ona göre **düzenledim.**  
İşte güncellenmiş HALİ:

---

# 📜 Tam Kod (Mesajlar kutulu)

```python
import discord
from discord.ext import commands
import sqlite3
from datetime import datetime, timedelta
import asyncio

# Bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.invites = True

# Bot başlat
bot = commands.Bot(command_prefix="!", intents=intents)

# Veritabanı
conn = sqlite3.connect("premium_users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    premium_until TEXT,
    inviter_id INTEGER,
    tacom INTEGER DEFAULT 0
)
""")
conn.commit()

# Fonksiyonlar
def set_inviter(user_id, inviter_id):
    cursor.execute("INSERT OR REPLACE INTO users (user_id, inviter_id) VALUES (?, ?)", (user_id, inviter_id))
    conn.commit()

def set_premium(user_id, days=1):
    premium_until = datetime.now() + timedelta(days=days)
    cursor.execute("REPLACE INTO users (user_id, premium_until) VALUES (?, ?)", (user_id, premium_until.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_premium_until(user_id):
    cursor.execute("SELECT premium_until FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def add_tacoin(user_id, amount=1):
    cursor.execute("SELECT tacom FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    if result:
        current = result[0] or 0
        cursor.execute("UPDATE users SET tacom=? WHERE user_id=?", (current + amount, user_id))
    else:
        cursor.execute("INSERT INTO users (user_id, tacom) VALUES (?, ?)", (user_id, amount))
    conn.commit()

# Etkinlikler
@bot.event
async def on_member_join(member):
    await asyncio.sleep(2)

    cursor.execute("SELECT inviter_id FROM users WHERE user_id=?", (member.id,))
    result = cursor.fetchone()

    if result:
        inviter_id = result[0]
        inviter = member.guild.get_member(inviter_id)

        if inviter:
            add_tacoin(inviter.id, amount=1)
            channel = discord.utils.get(member.guild.text_channels, name="genel")
            if channel:
                await channel.send(f"```🎉✨ {inviter.mention} birisini davet etti! +1 ⭐ TAcoin kazandı! ✨🎉```")

@bot.event
async def on_ready():
    print(f"{bot.user} olarak giriş yapıldı!")

# Komutlar
@bot.command()
async def davetler(ctx):
    """🔎 Sunucudaki davetleri ve premium durumları gösterir."""
    cursor.execute("SELECT user_id, inviter_id, premium_until FROM users")
    result = cursor.fetchall()
    
    if not result:
        await ctx.send("```Henüz davet edilen kimse yok.```")
        return
    
    davetler_listesi = []
    for user_id, inviter_id, premium_until in result:
        user = ctx.guild.get_member(user_id)
        inviter = ctx.guild.get_member(inviter_id)
        premium_status = "Premium Süresi Bitmiş" if datetime.now() > datetime.strptime(premium_until, "%Y-%m-%d %H:%M:%S") else f"Premium Süresi: {premium_until}"
        
        if user and inviter:
            davetler_listesi.append(f"{user.name} - Davet Eden: {inviter.name} - {premium_status}")
        else:
            davetler_listesi.append(f"Kimlik: {user_id} - Davet Eden: {inviter_id} - {premium_status}")

    await ctx.send("```" + "\n".join(davetler_listesi) + "```")

@bot.command()
async def premium_yap(ctx, member: discord.Member):
    """👑 Kullanıcıya 1 gün premium verir."""
    if ctx.author != ctx.guild.owner:
        await ctx.send("```Bu komutu yalnızca sunucu sahibi kullanabilir!```")
        return
    
    set_premium(member.id, days=1)
    await ctx.send(f"```{member.mention} adlı kullanıcıya 1 günlük premium verildi!```")

    set_inviter(member.id, ctx.author.id)

    premium_role = discord.utils.get(ctx.guild.roles, name="premium")
    if not premium_role:
        premium_role = await ctx.guild.create_role(name="premium")
    
    await member.add_roles(premium_role)

@bot.command()
async def premium_uzat(ctx, member: discord.Member, days: int):
    """⏳ Kullanıcının premium süresini uzatır."""
    if ctx.author != ctx.guild.owner:
        await ctx.send("```Bu komutu yalnızca sunucu sahibi kullanabilir!```")
        return

    current_premium_until = get_premium_until(member.id)
    if current_premium_until:
        current_premium_until = datetime.strptime(current_premium_until, "%Y-%m-%d %H:%M:%S")
        new_premium_until = current_premium_until + timedelta(days=days)
    else:
        new_premium_until = datetime.now() + timedelta(days=days)
    
    set_premium(member.id, days=(new_premium_until - datetime.now()).days)
    await ctx.send(f"```{member.mention} adlı kullanıcının premium süresi {days} gün uzatıldı!```")

    premium_role = discord.utils.get(ctx.guild.roles, name="premium")
    if not premium_role:
        premium_role = await ctx.guild.create_role(name="premium")
    
    await member.add_roles(premium_role)

@bot.command()
async def rol_ekle(ctx, member: discord.Member, role_name: str):
    """🛡️ Kullanıcıya rol ekler."""
    if not ctx.author.guild_permissions.administrator and ctx.author != ctx.guild.owner:
        await ctx.send("```Bu komutu yalnızca yönetici veya sunucu sahibi kullanabilir!```")
        return

    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        await ctx.send(f"```Rol '{role_name}' bulunamadı.```")
        return

    await member.add_roles(role)
    await ctx.send(f"```{member.mention} kullanıcısına '{role_name}' rolü verildi.```")

@bot.command()
async def temizle(ctx, miktar: int = 5):
    """🧹 Kanalda mesaj siler."""
    if not ctx.author.guild_permissions.manage_messages:
        await ctx.send("```Bu komutu yalnızca mesaj yönetme yetkisi olanlar kullanabilir!```")
        return

    deleted = await ctx.channel.purge(limit=miktar)
    await ctx.send(f"```🧹 {len(deleted)} mesaj silindi!```", delete_after=3)

# Botu başlat
bot.run('MTM2NTk5MjAyNDAzMzA3MTE4NQ.GxqcLp.ZOx3tG5luBEo45gKS8hJHU9qMymDlLEveMz40I')  # Buraya tokenini yazmayı unutma

import discord
from discord.ext import commands
import requests
import os
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OCR_API_KEY = os.getenv("OCR_API_KEY")

TARGET_GUILD_ID = int(os.getenv("GUILD_ID"))
TARGET_CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents)

def ocr_from_url(image_url):
    payload = {
        'url': image_url,
        'apikey': OCR_API_KEY,
        'language': 'eng',
        'scale': 'true',
    }
    response = requests.post('https://api.ocr.space/parse/image', data=payload)
    result = response.json()

    if result.get("IsErroredOnProcessing"):
        return None
    return result["ParsedResults"][0]["ParsedText"]

def extract_region_line(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for i in range(len(lines) - 1):
        if ',' in lines[i] and any(c.isalpha() for c in lines[i]):
            return f"{lines[i]} {lines[i+1]}"
    return None

@bot.event
async def on_reaction_add(reaction, user):
    print(f"🟡 리액션 감지됨: {reaction.emoji} by {user.name}")

    if user.bot or reaction.emoji != "✔️":
        return

    message = reaction.message

    if message.guild.id != TARGET_GUILD_ID or message.channel.id != TARGET_CHANNEL_ID:
        print("⛔ 허용된 채널이 아님")
        return

    if message.attachments:
        image_url = message.attachments[0].url
        await message.channel.send("🔍 서버 지역 인식 중...")

        text = ocr_from_url(image_url)
        print("📝 OCR 결과:\n", text)

        if not text:
            await message.reply("❌ 이미지 인식 실패")
            return

        region_full = extract_region_line(text)
        if region_full:
            await message.reply(f"📍 서버 위치: {region_full}")
        else:
            await message.reply("❓ 서버 위치를 찾을 수 없어요.")
    else:
        await message.reply("❌ 이 메시지에는 이미지가 없습니다.")

@bot.event
async def on_ready():
    print(f"✅ 봇 온라인: {bot.user}")

bot.run(DISCORD_TOKEN)

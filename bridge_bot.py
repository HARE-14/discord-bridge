"""Discord 멀티 서버 채널 브릿지 봇 - 여러 채널의 메시지를 웹훅으로 미러링."""

import os
import sys
import logging
from typing import Dict

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

BRIDGE_CHANNEL_IDS = [
    int(cid.strip())
    for cid in os.getenv("BRIDGE_CHANNEL_IDS", "").split(",")
    if cid.strip()
]

log_handlers = [logging.FileHandler("bridge.log", encoding="utf-8")]
if sys.stdout is not None:
    log_handlers.append(logging.StreamHandler())

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=log_handlers,
)
logger = logging.getLogger("bridge")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!bridge ", intents=intents)

webhooks: Dict[int, discord.Webhook] = {}

WEBHOOK_NAME = "MultiServerBridge"


async def get_or_create_webhook(channel: discord.TextChannel) -> discord.Webhook:
    """채널에 브릿지용 웹훅이 이미 있으면 재사용, 없으면 새로 생성"""
    existing = await channel.webhooks()
    for wh in existing:
        if wh.name == WEBHOOK_NAME:
            return wh
    return await channel.create_webhook(name=WEBHOOK_NAME)


@bot.event
async def on_ready():
    logger.info("로그인 완료: %s (id=%s)", bot.user, bot.user.id)

    logger.info("현재 봇이 들어가있는 서버 목록 (%d개):", len(bot.guilds))
    for g in bot.guilds:
        logger.info("  - %s (id=%s, 멤버수=%s)", g.name, g.id, g.member_count)

    if len(BRIDGE_CHANNEL_IDS) < 2:
        logger.warning("BRIDGE_CHANNEL_IDS에 채널이 2개 미만입니다. .env를 확인하세요.")

    for cid in BRIDGE_CHANNEL_IDS:
        channel = bot.get_channel(cid)
        if channel is None:
            logger.warning("채널 %s를 찾을 수 없음 (봇 초대 안 됨 / ID 오류 가능)", cid)
            continue
        try:
            webhooks[cid] = await get_or_create_webhook(channel)
            logger.info("웹훅 준비 완료: [%s] #%s", channel.guild.name, channel.name)
        except discord.Forbidden:
            logger.error(
                "권한 부족: [%s] #%s 에 웹훅 생성 불가 (Manage Webhooks 권한 필요)",
                channel.guild.name, channel.name,
            )


@bot.event
async def on_message(message: discord.Message):
    # 웹훅/봇 자신의 메시지는 무시 -> 무한루프 방지
    if message.webhook_id is not None:
        return
    if message.author == bot.user:
        return

    if message.channel.id not in BRIDGE_CHANNEL_IDS:
        await bot.process_commands(message)
        return

    content = message.content or ""
    username = f"{message.author.display_name} ({message.guild.name})"[:80]
    avatar_url = message.author.display_avatar.url

    for target_id, webhook in webhooks.items():
        if target_id == message.channel.id:
            continue

        # discord.File 객체는 1회용이라 대상마다 새로 생성해야 함
        files = [await a.to_file() for a in message.attachments] if message.attachments else []

        try:
            await webhook.send(
                content=content if content else None,
                username=username,
                avatar_url=avatar_url,
                files=files,
                allowed_mentions=discord.AllowedMentions.none(),  # 다른 서버 멘션 오작동 방지
            )
        except discord.HTTPException as e:
            logger.error("채널 %s로 전달 실패: %s", target_id, e)

    await bot.process_commands(message)


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("DISCORD_BOT_TOKEN이 .env에 설정되어 있지 않습니다.")
    bot.run(TOKEN)

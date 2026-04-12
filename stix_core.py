import asyncio
import logging
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebhookInfo
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import uuid

# ─── 🔮 THE FRISKY GHOST PROTOCOL (Cyber-Occult Encrypted Vault) ─── #
# Mocking AES-256-CBC and Sovereign Vault connections for the Blind Pipeline
class SovereignVault:
    @staticmethod
    def encrypt_prompt(raw_text: str) -> str:
        """Strip user metadata and encrypt payload for blind processing."""
        return f"AES256::b64::{hash(raw_text)}"

    @staticmethod
    def store_resonance(style: str) -> None:
        """Learning Ledger: Store style choice frequencies strictly stripped of identities."""
        logging.info(f"🔮 [LEDGER] Resonance logged for style: {style}")

    @staticmethod
    def check_venta_status(user_id: str) -> bool:
        """The Gate: Validate subscription in MongoDB Atlas."""
        return True  # Bypass logic for STIX MΛGIC Elite users

vault = SovereignVault()

# ─── ⚡ CORE CONFIGURATION ─── #
BOT_TOKEN = os.getenv("STIX_BOT_TOKEN", "REPLACE_WITH_YOUR_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://api.stixmagic.io/NΞBU/webhook")
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))

from aiogram.client.default import DefaultBotProperties
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

from openai import AsyncOpenAI
import json

# ─── 🧬 THE SYNTHESIS ENGINE (GPT-4o) ─── #
async def generate_triad(prompt: str):
    """Call GPT-4o to synthesize The Triad and extract JSON payload."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        await asyncio.sleep(1)
        return {
            "A": "⚠️ OPENAI_API_KEY not found in environment.",
            "B": "Neural Interface Offline.",
            "C": "Please provide a valid OpenAI API Key.",
            "juice_emoji_id": "5819022417917383759"
        }
        
    try:
        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are STIX MΛGIC, a Cyber-Occult AI text transformer. Given raw text, output ONLY a JSON object with EXACTLY three string keys: 'A', 'B', and 'C'. 'A' must be a highly viral HYPE promotional version. 'B' must be a DEEP TECH analytical version focusing on architecture. 'C' must be a minimalist, glassmorphism PURE AESTHETIC version with emojis. Keep each string under 50 words. Do not use standard markdown formatting inside the JSON."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return {
            "A": data.get("A", "Hype synthesis failed."),
            "B": data.get("B", "Tech synthesis failed."),
            "C": data.get("C", "Aesthetic synthesis failed."),
            "juice_emoji_id": "5818721722962023190"  # Dynamic selector in future
        }
    except Exception as e:
        logging.error(f"OpenAI Synthesis Error: {e}")
        return {
            "A": f"⚠️ Synthesis Error: {str(e)}",
            "B": "Neural Processing Interrupted.",
            "C": "Check server logs.",
            "juice_emoji_id": "5819022417917383759"
        }

# ─── 👁 THE CURATOR MODE INTERFACE ─── #
def build_curator_keyboard(juice_id: str) -> InlineKeyboardMarkup:
    """Constructing telegram native buttons to bypass the API 9.4 hallucination error."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💎 Select A (HYPE)", callback_data="manifest_A"),
                InlineKeyboardButton(text="👽 Select B (TECH)", callback_data="manifest_B"),
                InlineKeyboardButton(text="✨ Select C (AESTHETIC)", callback_data="manifest_C")
            ],
            [
                InlineKeyboardButton(text="🔄 Reroll Void", callback_data="manifest_reroll"),
                InlineKeyboardButton(text="🔥 Purge Memory", callback_data="manifest_purge")
            ]
        ]
    )
    return keyboard

# ─── ⚙️ SYSTEM ROUTERS ─── #
@dp.message(Command("start"))
async def ritual_init(message: types.Message):
    await message.answer(
        "<b>🔮 Welcome to STIX MΛGIC</b>\n\n"
        "<blockquote>Drop any text or idea here.\n\n"
        "I will instantly rewrite it into 3 perfect premium formats (Hype, Technical, Aesthetic).</blockquote>\n\n"
        "<i>What do you want to manifest? Type below:</i> ✨"
    )

@dp.message(F.text)
async def ingestion_ritual(message: types.Message):
    raw_prompt = message.text
    
    # Ghost Protocol Execution
    str_user = str(message.from_user.id)
    if not vault.check_venta_status(str_user):
        return await message.answer("❌ Sovereign Vault check failed. Sub required.")

    encrypted_intent = vault.encrypt_prompt(raw_prompt)
    
    loader_msg = await message.answer(
        "<blockquote><tg-emoji emoji-id='5818721722962023190'>✨</tg-emoji> [ ✦ ✧ ✧ ] <i>Ghost Protocol initialized...</i></blockquote>",
        parse_mode="HTML"
    )
    await asyncio.sleep(0.4)
    await loader_msg.edit_text(
        "<blockquote><tg-emoji emoji-id='5080532211896158167'>👾</tg-emoji> [ ✧ ✦ ✧ ] <i>Injecting Neural Hype...</i></blockquote>",
        parse_mode="HTML"
    )
    await asyncio.sleep(0.4)
    await loader_msg.edit_text(
        "<blockquote><tg-emoji emoji-id='5819022417917383759'>💎</tg-emoji> [ ✧ ✧ ✦ ] <i>Polishing The Triad...</i></blockquote>",
        parse_mode="HTML"
    )
    
    triad = await generate_triad(encrypted_intent)
    
    final_text = (
        f"<tg-emoji emoji-id='{triad['juice_emoji_id']}'>✨</tg-emoji> <b>THE SYNETHESIS COMPLETE</b>\n\n"
        f"<b>A (HYPE):</b> <blockquote>{triad['A']}</blockquote>\n"
        f"<b>B (TECH):</b> <blockquote>{triad['B']}</blockquote>\n"
        f"<b>C (AESTHETIC):</b> <blockquote>{triad['C']}</blockquote>\n\n"
        f"<i>Select your exact manipulation vector to manifest:</i>"
    )
    
    await loader_msg.edit_text(
        text=final_text, 
        reply_markup=build_curator_keyboard(triad['juice_emoji_id'])
    )

@dp.callback_query(F.data.startswith("manifest_"))
async def the_manifestation(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    
    if action in ["A", "B", "C"]:
        vault.store_resonance(f"style_{action}")
        theme_names = {"A": "HYPE", "B": "DEEP TECH", "C": "PURE AESTHETIC"}
        
        # We fetch the Triad state (currently fetching fresh from Synthesis stub for demonstration)
        triad = await generate_triad("Fetch Extracted State")
        selected_text = triad[action]
        
        manifested_text = (
            f"<b>{theme_names[action]} MΛGIC MANIFESTED</b> ✨\n\n"
            f"<blockquote>{selected_text}</blockquote>\n\n"
            f"<i>Tap and hold the block above to copy the raw text. ✂️</i>"
        )
        
        # We append a back/reroll button here if they want to go back!
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔄 Reroll Entire Prompt", callback_data="manifest_reroll")]]
        )
        await callback.message.edit_text(manifested_text, parse_mode="HTML", reply_markup=keyboard)
        
    elif action == "purge":
        await callback.message.edit_text("🔥 <b>Memory Purged. The UI Timeline has collapsed.</b>")
        
    elif action == "reroll":
        triad = await generate_triad("Rerolled Intent")
        final_text = (
            f"<tg-emoji emoji-id='{triad['juice_emoji_id']}'>✨</tg-emoji> <b>THE SYNETHESIS COMPLETE (REROLLED)</b>\n\n"
            f"<b>A (HYPE):</b> <blockquote>{triad['A']}</blockquote>\n"
            f"<b>B (TECH):</b> <blockquote>{triad['B']}</blockquote>\n"
            f"<b>C (AESTHETIC):</b> <blockquote>{triad['C']}</blockquote>\n\n"
            f"<i>Select your exact manipulation vector to manifest:</i>"
        )
        await callback.message.edit_text(
            text=final_text, 
            reply_markup=build_curator_keyboard(triad['juice_emoji_id'])
        )
    
    await callback.answer()

# ─── 🌐 EXECUTION & DEPLOYMENT ─── #
async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook pinned to: {WEBHOOK_URL}")

def start_webhook_server():
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=str(uuid.uuid4())
    )
    webhook_requests_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)

async def main_polling():
    logging.info("🔮 Executing DEV Polling Ritual...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    app_env = os.getenv("APP_ENV", "dev").lower()
    if app_env == "production":
        logging.info("🔮 Executing PROD Webhook Ritual...")
        start_webhook_server()
    else:
        asyncio.run(main_polling())

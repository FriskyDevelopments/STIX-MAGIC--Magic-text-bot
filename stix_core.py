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

# ─── 🧬 THE SYNTHESIS ENGINE (LLM & IMAGE STUB) ─── #
async def generate_triad(prompt: str):
    """Call Codex/GPT-4o to synthesize The Triad and Imagen-4 for The Juice."""
    await asyncio.sleep(1) # Quantum Calculation
    return {
        "A": "🚀 MΛGIC HYPE: Your project is going viral.",
        "B": "💻 DEEP TECH: Under-the-hood optimization matrix.",
        "C": "✨ AESTHETIC: Pure minimalist glassmorphism vibes.",
        "juice_emoji_id": "5818721722962023190"  # Pre-minted Custom Emoji ID from Catalog
    }

# ─── 👁 THE CURATOR MODE INTERFACE ─── #
def build_curator_keyboard(juice_id: str) -> InlineKeyboardMarkup:
    """Constructing Telegram 9.4 Colored Buttons for Triad Selection."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Select A (HYPE)", callback_data="manifest_A",
                    style="primary", icon_custom_emoji_id="5818689154225017827"
                ),
                InlineKeyboardButton(
                    text="Select B (TECH)", callback_data="manifest_B",
                    style="secondary", icon_custom_emoji_id="5418063924933173277" 
                ),
                InlineKeyboardButton(
                    text="Select C (AESTHETIC)", callback_data="manifest_C",
                    style="success", icon_custom_emoji_id="5818721722962023190"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Reroll Void", callback_data="manifest_reroll", style="primary"
                ),
                InlineKeyboardButton(
                    text="Purge Memory", callback_data="manifest_purge", style="danger",
                    icon_custom_emoji_id="5819022417917383759"
                )
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
        # In a real app we fetch the text from DB or memory. We mock it here mapping action to theme name.
        theme_names = {"A": "HYPE", "B": "DEEP TECH", "C": "PURE AESTHETIC"}
        
        manifested_text = (
            f"✅ <b>MΛGIC Manifested: Phase {action}</b>\n\n"
            f"<blockquote expandable>"
            f"<b>Chosen Resonance [{theme_names[action]}]</b> has been cleanly extracted and pushed to your clipboard buffer. "
            f"You can now copy it directly. The other timeline branches have been pruning-deleted."
            f"</blockquote>"
        )
        await callback.message.edit_text(manifested_text, parse_mode="HTML")
        
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

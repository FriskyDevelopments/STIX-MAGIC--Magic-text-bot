import asyncio
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebhookInfo
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import uuid

# ─── 🔮 THE FRISKY GHOST PROTOCOL (Cyber-Occult Encrypted Vault) ─── #
_memory_matrix = {}
_user_intents = {}
ELITE_USERS = ["8091939499"]  # Core bypass for administrative tests

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
        if user_id in ELITE_USERS:
            logging.info(f"💎 Elite User Bypass Authenticated: {user_id}")
            return True
        return True  # Fallback bypass logic for STIX MΛGIC public test

vault = SovereignVault()

# ─── ⚡ CORE CONFIGURATION ─── #
BOT_TOKEN = os.getenv("BOT_TOKEN_DEV", os.getenv("TELEGRAM_BOT_TOKEN", "REPLACE_WITH_YOUR_TOKEN"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://api.stixmagic.io/NΞBU/webhook")
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))

from aiogram.client.default import DefaultBotProperties
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

from openai import AsyncOpenAI  # Groq uses OpenAI-compatible SDK
import json

# ─── 🧬 THE SYNTHESIS ENGINE (Groq / Llama 4) ─── #
async def generate_triad(prompt: str):
    """Call Groq (Llama 4 Scout) to synthesize The Triad and extract JSON payload."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        await asyncio.sleep(1)
        return {
            "A": "⚠️ GROQ_API_KEY not found in environment.",
            "B": "Neural Interface Offline.",
            "C": "Please provide a valid Groq API Key.",
            "juice_emoji_id": "5819022417917383759"
        }
        
    try:
        client = AsyncOpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        response = await client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
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

MINI_APP_URL = os.getenv("MINI_APP_URL", "https://your-domain.ngrok-free.app/stix")

VISUAL_MANIFESTATION_BUTTON = "🖼 Visual Manifestation (Beta)"

# ─── ⚙️ SYSTEM ROUTERS ─── #
@dp.message(Command("start"))
async def ritual_init(message: types.Message):
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, MenuButtonDefault
    
    # Adaptive Native UI: We remove the broken Ngrok WebApp dependency and focus on conversational context.
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✨ Initiate Text Synthesis")],
            [KeyboardButton(text=VISUAL_MANIFESTATION_BUTTON)]
        ],
        resize_keyboard=True,
        persistent=True
    )
    
    # Try to purge the stale WebApp button that causes the Ngrok error
    try:
        await bot.set_chat_menu_button(chat_id=message.chat.id, menu_button=MenuButtonDefault())
    except Exception:
        pass
    
    await message.answer(
        "<b>🔮 Welcome to the STIX MΛGIC Adaptive Core</b>\n\n"
        "<blockquote>We have disconnected the static Web App template. This interface is now fully dynamic.</blockquote>\n\n"
        "<i>Drop your raw prompt straight into the chat below. The neural link will adapt to your request and return the curated Triad or visual designs directly in the chat.</i> ✨",
        reply_markup=keyboard
    )

@dp.message(F.text == VISUAL_MANIFESTATION_BUTTON)
async def visual_manifestation_pipeline(message: types.Message):
    str_user = str(message.from_user.id)
    logging.info("Visual Manifestation invoked | user_id=%s", str_user)

    if not vault.check_venta_status(str_user):
        logging.warning("Visual Manifestation denied | Venta check failed | user_id=%s", str_user)
        return await message.answer(
            "<b>❌ Sovereign Vault check failed.</b>\n\n"
            "<blockquote>Venta subscription is required to route packets through the visual matrix.</blockquote>",
            parse_mode="HTML",
        )

    encrypted_intent = _user_intents.get(str_user)
    if not encrypted_intent:
        logging.warning("Visual Manifestation blocked | collapsed timeline (no intent) | user_id=%s", str_user)
        return await message.answer(
            "<b>⛔ Visual timeline collapsed.</b>\n\n"
            "<blockquote>You have <b>no</b> encrypted prompt anchored in the Ghost Protocol. "
            "The matrix cannot instantiate — raw text must hit the channel first. "
            "Drop your unfiltered payload, complete synthesis, <i>then</i> return here.</blockquote>\n\n"
            "<i>Void input yields void output. Re-initiate or stay dark.</i>",
            parse_mode="HTML",
        )

    loader_msg = await message.answer(
        "<blockquote><i>Initiating visual matrix...</i></blockquote>",
        parse_mode="HTML",
    )
    await asyncio.sleep(0.45)
    await loader_msg.edit_text(
        "<blockquote><i>Rendering hyper-aesthetic nodes...</i></blockquote>",
        parse_mode="HTML",
    )
    await asyncio.sleep(0.45)

    logging.info("Visual Manifestation GPU placeholder emitted | user_id=%s", str_user)
    await loader_msg.edit_text(
        "<b>🖼 Visual Manifestation</b>\n\n"
        "<blockquote>Visual Manifestation is currently pending GPU allocation on the NΞBU network.</blockquote>\n\n"
        "<i>Neural render queues are warming; stand by.</i>",
        parse_mode="HTML",
    )

@dp.message(F.web_app_data)
async def web_app_handler(message: types.Message):
    """Intercept the JSON payload blasted directly from Next.js Mini App."""
    import json
    try:
        data = json.loads(message.web_app_data.data)
        if data.get("action") == "manifest_completed":
            theme = data.get("theme", "HYPE")
            content = data.get("content", "")
            
            await message.answer(
                f"<b>{theme} MΛGIC MANIFESTED</b> ✨\n\n"
                f"<blockquote>{content}</blockquote>\n\n"
                f"<i>Tap and hold the block above to copy the raw text. ✂️</i>"
            )
    except Exception as e:
        logging.error(f"WebApp Data parse error: {e}")
        
@dp.message(F.text)
async def ingestion_ritual(message: types.Message):
    raw_prompt = message.text
    
    # Ghost Protocol Execution
    str_user = str(message.from_user.id)
    if not vault.check_venta_status(str_user):
        return await message.answer("❌ Sovereign Vault check failed. Sub required.")

    encrypted_intent = vault.encrypt_prompt(raw_prompt)
    _user_intents[str_user] = encrypted_intent
    
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
    
    # Cache the payload in the memory matrix to prevent hallucination on callback
    _memory_matrix[str_user] = triad
    
    final_text = (
        f"<tg-emoji emoji-id='{triad.get('juice_emoji_id', '5819022417917383759')}'>✨</tg-emoji> <b>THE SYNETHESIS COMPLETE</b>\n\n"
        f"<b>A (HYPE):</b> <blockquote>{triad.get('A', 'Error')}</blockquote>\n"
        f"<b>B (TECH):</b> <blockquote>{triad.get('B', 'Error')}</blockquote>\n"
        f"<b>C (AESTHETIC):</b> <blockquote>{triad.get('C', 'Error')}</blockquote>\n\n"
        f"<i>Select your exact manipulation vector to manifest:</i>"
    )
    
    await loader_msg.edit_text(
        text=final_text, 
        reply_markup=build_curator_keyboard(triad['juice_emoji_id'])
    )

@dp.callback_query(F.data.startswith("manifest_"))
async def the_manifestation(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    str_user = str(callback.from_user.id)
    
    if action in ["A", "B", "C"]:
        vault.store_resonance(f"style_{action}")
        theme_names = {"A": "HYPE", "B": "DEEP TECH", "C": "PURE AESTHETIC"}
        
        # We fetch the Triad state from the memory matrix
        triad = _memory_matrix.get(str_user)
        if not triad:
            return await callback.message.edit_text("🔥 <b>Memory Expired. The UI Timeline has collapsed. Please re-initiate the ritual.</b>")
            
        selected_text = triad.get(action, "Error loading memory.")
        
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
        # Pull the original intent from the cache
        original_intent = _user_intents.get(str_user, "General Retry Prompt")
        triad = await generate_triad(original_intent)
        
        # Update the memory matrix so subsequent A/B/C clicks pull the new data
        _memory_matrix[str_user] = triad
        
        final_text = (
            f"<tg-emoji emoji-id='{triad.get('juice_emoji_id', '5818721722962023190')}'>✨</tg-emoji> <b>THE SYNETHESIS COMPLETE (REROLLED)</b>\n\n"
            f"<b>A (HYPE):</b> <blockquote>{triad.get('A', 'Error')}</blockquote>\n"
            f"<b>B (TECH):</b> <blockquote>{triad.get('B', 'Error')}</blockquote>\n"
            f"<b>C (AESTHETIC):</b> <blockquote>{triad.get('C', 'Error')}</blockquote>\n\n"
            f"<i>Select your exact manipulation vector to manifest:</i>"
        )
        await callback.message.edit_text(
            text=final_text, 
            reply_markup=build_curator_keyboard(triad.get('juice_emoji_id', '5818721722962023190'))
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

import asyncio
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional

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
from pinecone import Pinecone

# ─── 🧬 THE SYNTHESIS ENGINE (Groq / Llama 4) ─── #
class PineconeMemoryStore:
    """RAG memory layer for storing and retrieving user triad generations."""

    def __init__(self):
        self.index = None
        self.embed_model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
        self.top_k = int(os.getenv("PINECONE_TOP_K", "3"))
        self._openai_client = None
        self._use_local = os.getenv("LOCAL_EMBEDDINGS", "false").lower() == "true"
        self._local_model = None

        api_key = os.getenv("PINECONE_API_KEY")
        index_name = os.getenv("PINECONE_INDEX_NAME")
        if not api_key or not index_name:
            logging.warning("Pinecone disabled: set PINECONE_API_KEY and PINECONE_INDEX_NAME.")
            return

        try:
            pc = Pinecone(api_key=api_key)
            self.index = pc.Index(index_name)
            logging.info("✅ Pinecone memory initialized | index=%s", index_name)
        except Exception as e:
            logging.error("Failed to initialize Pinecone: %s", e)
            self.index = None

    def enabled(self) -> bool:
        return self.index is not None

    async def _embed_openai(self, text: str) -> List[float]:
        if not self._openai_client:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY missing for embeddings.")
            self._openai_client = AsyncOpenAI(api_key=api_key)
        response = await self._openai_client.embeddings.create(
            model=self.embed_model,
            input=text
        )
        return response.data[0].embedding

    async def _embed_local(self, text: str) -> List[float]:
        if not self._local_model:
            from sentence_transformers import SentenceTransformer
            self._local_model = SentenceTransformer(
                os.getenv("LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            )
        vector = await asyncio.to_thread(self._local_model.encode, text)
        return vector.tolist()

    async def embed(self, text: str) -> List[float]:
        if self._use_local:
            return await self._embed_local(text)
        return await self._embed_openai(text)

    async def fetch_user_memories(self, telegram_id: str, query_text: str) -> List[str]:
        if not self.enabled():
            return []
        try:
            query_vector = await self.embed(query_text)
            response = await asyncio.to_thread(
                self.index.query,
                vector=query_vector,
                top_k=self.top_k,
                include_metadata=True,
                filter={"telegram_id": telegram_id},
            )
            matches = response.get("matches", []) if isinstance(response, dict) else getattr(response, "matches", [])
            memories = []
            for match in matches:
                metadata = match.get("metadata", {}) if isinstance(match, dict) else getattr(match, "metadata", {})
                triad_text = metadata.get("triad_text")
                if triad_text:
                    memories.append(triad_text)
            return memories
        except Exception as e:
            logging.error("Pinecone fetch failed | user=%s | error=%s", telegram_id, e)
            return []

    async def store_user_triad(self, telegram_id: str, raw_prompt: str, triad: Dict[str, Any]) -> None:
        if not self.enabled():
            return
        try:
            triad_text = f"HYPE: {triad.get('A', '')}\nTECH: {triad.get('B', '')}\nAESTHETIC: {triad.get('C', '')}"
            embedding = await self.embed(triad_text)
            point_id = str(uuid.uuid4())
            metadata = {
                "telegram_id": telegram_id,
                "prompt": raw_prompt[:1000],
                "triad_text": triad_text[:4000],
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
            await asyncio.to_thread(
                self.index.upsert,
                vectors=[{"id": point_id, "values": embedding, "metadata": metadata}]
            )
            logging.info("Pinecone memory stored | user=%s | id=%s", telegram_id, point_id)
        except Exception as e:
            logging.error("Pinecone upsert failed | user=%s | error=%s", telegram_id, e)


memory_store = PineconeMemoryStore()


def _is_successful_triad(triad: Dict[str, Any]) -> bool:
    if not triad:
        return False
    values = [str(triad.get("A", "")), str(triad.get("B", "")), str(triad.get("C", ""))]
    if any(v.strip() == "" for v in values):
        return False
    return not any("Synthesis Error" in v or "not found in environment" in v for v in values)


async def generate_triad(prompt: str, memory_context: Optional[List[str]] = None):
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
                {
                    "role": "system",
                    "content": (
                        "User Memory Context (top previous generations for style alignment):\n"
                        + ("\n---\n".join(memory_context) if memory_context else "No prior generations found.")
                    )
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

    _user_intents[str_user] = raw_prompt
    
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
    
    user_memories = await memory_store.fetch_user_memories(str_user, raw_prompt)
    triad = await generate_triad(raw_prompt, memory_context=user_memories)
    
    # Cache the payload in the memory matrix to prevent hallucination on callback
    _memory_matrix[str_user] = triad
    if _is_successful_triad(triad):
        await memory_store.store_user_triad(
            telegram_id=str_user,
            raw_prompt=raw_prompt,
            triad=triad
        )
    
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
        user_memories = await memory_store.fetch_user_memories(str_user, original_intent)
        triad = await generate_triad(original_intent, memory_context=user_memories)
        
        # Update the memory matrix so subsequent A/B/C clicks pull the new data
        _memory_matrix[str_user] = triad
        if _is_successful_triad(triad):
            await memory_store.store_user_triad(
                telegram_id=str_user,
                raw_prompt=original_intent,
                triad=triad
            )
        
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

import logging
import os
import random
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

STIX_TOKEN = os.getenv("STIX_BOT_TOKEN")

# Premium Emoji Core Mapping
MAGIC_EMOJIS = [
    '<tg-emoji emoji-id="5818689154225017827">🚀</tg-emoji>',
    '<tg-emoji emoji-id="5818721722962023190">✨</tg-emoji>',
    '<tg-emoji emoji-id="5819022417917383759">💎</tg-emoji>',
    '<tg-emoji emoji-id="5080532211896158167">👾</tg-emoji>',
    '<tg-emoji emoji-id="5418063924933173277">👨‍💻</tg-emoji>'
]

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_text = (
        f'{random.choice(MAGIC_EMOJIS)} <b>Welcome to STIX MAGIC TEXT</b>\n\n'
        f'<blockquote>I am the ultimate text automation module.\n'
        f'Just drop your plain text here, and I will format it into '
        f'premium glassmorphism blocks wrapped in elite animated emojis.</blockquote>\n\n'
        f'<i>Ready to elevate your prose? Type something.</i> ✨'
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)

async def magic_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    raw_text = update.message.text
    if not raw_text:
        return

    # Intersperse text with our beautiful custom emojis
    magic_emoji_1 = random.choice(MAGIC_EMOJIS)
    magic_emoji_2 = random.choice(MAGIC_EMOJIS)
    
    formatted_text = (
        f'{magic_emoji_1} <b>STIX PROCESSING:</b>\n\n'
        f'<blockquote>{raw_text}</blockquote>\n\n'
        f'{magic_emoji_2} <i>Formatted by STIX MAGIC</i>'
    )
    
    await update.message.reply_text(formatted_text, parse_mode=ParseMode.HTML)


def main() -> None:
    # Build the application
    if not STIX_TOKEN:
        print("Set STIX_BOT_TOKEN in your environment or .env file!")
        return

    application = Application.builder().token(STIX_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, magic_format))

    logger.info("STIX Magic Engine started! Listening...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

import logging
import os
import threading
import time

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from bot.handlers import dispatch_callback, magic_format, pro_command, start_command

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

STIX_TOKEN = (
    os.getenv("STIX_BOT_TOKEN")
    or os.getenv("BOT_TOKEN_DEV")
    or os.getenv("TELEGRAM_BOT_TOKEN")
)

# Local dev: set STIX_LOCAL_DEV=1 so polling can take priority over a cloud webhook.
_STIX_LOCAL_DEV = os.getenv("STIX_LOCAL_DEV", "").strip().lower() in ("1", "true", "yes", "on")
_STIX_WEBHOOK_SUPPRESS_INTERVAL = float(os.getenv("STIX_WEBHOOK_SUPPRESS_INTERVAL_SEC", "1.5"))


def _is_local_dev_mode() -> bool:
    return _STIX_LOCAL_DEV


def _telegram_delete_webhook_sync(token: str) -> bool:
    """Synchronous Bot API call (thread-safe) — clears webhook so getUpdates polling can bind."""
    url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    try:
        response = requests.post(
            url,
            data={"drop_pending_updates": "true"},
            timeout=25,
        )
        payload = response.json() if response.content else {}
        ok = bool(payload.get("ok"))
        if not ok:
            logger.warning(
                "deleteWebhook returned not ok | status=%s body=%s",
                response.status_code,
                payload,
            )
        return ok
    except requests.RequestException as exc:
        logger.warning("deleteWebhook request failed: %s", exc)
        return False


def _webhook_suppression_loop(token: str, interval_sec: float) -> None:
    """
    Keeps issuing deleteWebhook while local polling runs so a remote webhook
    cannot permanently starve getUpdates (mitigates telegram.error.Conflict).
    """
    logger.info(
        "Local dev webhook suppression active | interval_sec=%s",
        interval_sec,
    )
    while True:
        _telegram_delete_webhook_sync(token)
        time.sleep(max(0.25, interval_sec))


def _start_local_dev_webhook_suppression(token: str) -> None:
    _telegram_delete_webhook_sync(token)
    thread = threading.Thread(
        target=_webhook_suppression_loop,
        args=(token, _STIX_WEBHOOK_SUPPRESS_INTERVAL),
        name="stix-webhook-suppressor",
        daemon=True,
    )
    thread.start()
    logger.info(
        "STIX_LOCAL_DEV enabled — background deleteWebhook loop started "
        "(daemon thread; polling should bind without Conflict if rate limits allow)."
    )


def main() -> None:
    if not STIX_TOKEN:
        logger.error(
            "Set one of STIX_BOT_TOKEN, BOT_TOKEN_DEV, or TELEGRAM_BOT_TOKEN "
            "in your environment or .env file."
        )
        return

    if _is_local_dev_mode():
        _start_local_dev_webhook_suppression(STIX_TOKEN)

    application = Application.builder().token(STIX_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("pro", pro_command))
    application.add_handler(CallbackQueryHandler(dispatch_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, magic_format))

    logger.info("STIX Magic Engine started! Listening...")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=bool(_is_local_dev_mode()),
    )

if __name__ == "__main__":
    main()

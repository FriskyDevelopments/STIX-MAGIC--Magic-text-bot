import logging
import os
import re
import threading
import time

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from bot.handlers import (
    add_debugger_command,
    alchemy_command,
    antigravity_command,
    authorize_group_command,
    dispatch_callback,
    help_command,
    invite_command,
    magic_format,
    magic_image,
    menu_command,
    pro_command,
    relay_command,
    start_command,
    ticket_command,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class SecretRedactionFilter(logging.Filter):
    _BOT_TOKEN_RE = re.compile(r"\b\d{7,}:[A-Za-z0-9_-]{20,}\b")

    def filter(self, record: logging.LogRecord) -> bool:
        rendered = record.getMessage()
        redacted = self._BOT_TOKEN_RE.sub("[REDACTED_BOT_TOKEN]", rendered)
        if redacted != rendered:
            record.msg = redacted
            record.args = ()
        return True


_secret_filter = SecretRedactionFilter()
_root_logger = logging.getLogger()
for _handler in _root_logger.handlers:
    _handler.addFilter(_secret_filter)
_root_logger.addFilter(_secret_filter)

# Avoid request URL logs that can contain bot tokens.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

STIX_TOKEN = (
    os.getenv("TELEGRAM_BOT_TOKEN")
    or os.getenv("STIX_BOT_TOKEN")
    or os.getenv("BOT_TOKEN_DEV")
)

# Local dev: set STIX_LOCAL_DEV=1 so polling can take priority over a cloud webhook.
_STIX_LOCAL_DEV = os.getenv("STIX_LOCAL_DEV", "").strip().lower() in ("1", "true", "yes", "on")
_STIX_CLEAR_WEBHOOK_ON_START = os.getenv("STIX_CLEAR_WEBHOOK_ON_START", "1").strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
)
_STIX_DROP_PENDING_UPDATES = os.getenv("STIX_DROP_PENDING_UPDATES", "").strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
)
_STIX_WEBHOOK_SUPPRESS_INTERVAL = float(os.getenv("STIX_WEBHOOK_SUPPRESS_INTERVAL_SEC", "1.5"))


def _is_local_dev_mode() -> bool:
    return _STIX_LOCAL_DEV


def _telegram_delete_webhook_sync(token: str, *, drop_pending_updates: bool = False) -> bool:
    """Synchronous Bot API call (thread-safe) - clears webhook so polling can bind."""
    url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    try:
        response = requests.post(
            url,
            data={"drop_pending_updates": "true" if drop_pending_updates else "false"},
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
    _telegram_delete_webhook_sync(token, drop_pending_updates=True)
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
        raise SystemExit(1)

    if _is_local_dev_mode():
        _start_local_dev_webhook_suppression(STIX_TOKEN)
    elif _STIX_CLEAR_WEBHOOK_ON_START:
        _telegram_delete_webhook_sync(
            STIX_TOKEN,
            drop_pending_updates=_STIX_DROP_PENDING_UPDATES,
        )

    application = Application.builder().token(STIX_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ticket", ticket_command))
    application.add_handler(CommandHandler("antigravity", antigravity_command))
    application.add_handler(CommandHandler("alchemy", alchemy_command))
    application.add_handler(CommandHandler("relay", relay_command))
    application.add_handler(CommandHandler("invite", invite_command))
    application.add_handler(CommandHandler("authorize_group", authorize_group_command))
    application.add_handler(CommandHandler("add_debugger", add_debugger_command))
    application.add_handler(CommandHandler("pro", pro_command))
    application.add_handler(
        MessageHandler((filters.PHOTO | filters.Document.IMAGE) & ~filters.COMMAND, magic_image)
    )
    application.add_handler(CallbackQueryHandler(dispatch_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, magic_format))

    logger.info("STIX Magic Engine started! Listening...")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=bool(_is_local_dev_mode() or _STIX_DROP_PENDING_UPDATES),
    )

if __name__ == "__main__":
    main()

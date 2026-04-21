from __future__ import annotations

import logging
import random
import re
from typing import Awaitable, Callable, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# ─── Shared tone (aligned with main.py) ─── #
MAGIC_EMOJIS = [
    '<tg-emoji emoji-id="5818689154225017827">🚀</tg-emoji>',
    '<tg-emoji emoji-id="5818721722962023190">✨</tg-emoji>',
    '<tg-emoji emoji-id="5819022417917383759">💎</tg-emoji>',
    '<tg-emoji emoji-id="5080532211896158167">👾</tg-emoji>',
    '<tg-emoji emoji-id="5418063924933173277">👨‍💻</tg-emoji>',
]

# ─── /pro paginated “Features” deck (1-based copy for humans in-body) ─── #
_PRO_PAGES: tuple[dict[str, str], ...] = (
    {
        "slug": "features",
        "title": "Features",
        "body": (
            "<b>Glassmorphism blocks</b> with animated premium emojis.\n"
            "<b>Neural polish</b> for hype, deep-tech, and pure aesthetic lanes.\n"
            "<b>Ghost Protocol</b>-ready intents for downstream synthesis."
        ),
    },
    {
        "slug": "workflow",
        "title": "Workflow",
        "body": (
            "Drop raw text → STIX routes through the formatter → you get "
            "copy-ready HTML chunks.\n\n"
            "<i>Keyboard flows stay in-thread; pagination edits the same surface.</i>"
        ),
    },
    {
        "slug": "sovereign",
        "title": "Sovereign Layer",
        "body": (
            "Venta-gated routes, ledger-safe resonance logging, and NΞBU-adjacent "
            "render queues for visual lanes.\n\n"
            "<i>Tap below to open a nested branch without spawning a new block.</i>"
        ),
    },
)

# ─── Deep tree: leaf screens (same message, edited) ─── #
_TREE_SCREENS: dict[str, dict[str, str]] = {
    "vault": {
        "title": "Sovereign Vault",
        "body": (
            "Encrypted intent envelopes, blind processors, and subscription gates.\n\n"
            "<blockquote>Branches resolve through one callback router — add new slugs here.</blockquote>"
        ),
    },
    "api": {
        "title": "API Hooks",
        "body": (
            "Wire web-app payloads, Mini App JSON, or headless workers.\n\n"
            "<i>Pattern:</i> <code>namespace:action[:payload…]</code> — keep under 64B."
        ),
    },
}

CallbackFn = Callable[[Update, ContextTypes.DEFAULT_TYPE, str], Awaitable[None]]

_CALLBACK_REGISTRY: dict[str, CallbackFn] = {}


def register_callback(prefix: str, fn: CallbackFn) -> None:
    if prefix in _CALLBACK_REGISTRY:
        raise ValueError(f"Duplicate callback prefix: {prefix!r}")
    _CALLBACK_REGISTRY[prefix] = fn


def _split_payload(data: str) -> tuple[str, tuple[str, ...]]:
    parts = data.split(":")
    return parts[0], tuple(parts[1:])


async def dispatch_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
        return
    data = query.data
    prefix, _ = _split_payload(data)
    handler = _CALLBACK_REGISTRY.get(prefix)
    if handler is None:
        logger.warning("Unhandled callback prefix=%s data=%r", prefix, data)
        await query.answer()
        return
    await handler(update, context, data)


# ─── /pro HTML + keyboards ─── #
def _pro_page_html(page_index: int) -> str:
    total = len(_PRO_PAGES)
    page = _PRO_PAGES[page_index]
    badge = random.choice(MAGIC_EMOJIS)
    return (
        f"{badge} <b>STIX MΛGIC — Pro</b>\n\n"
        f"<b>Page {page_index + 1} of {total}</b> "
        f"<i>({page['title']})</i>\n\n"
        f"<blockquote>{page['body']}</blockquote>\n\n"
        f"<i>Use the arrows to slide the deck in place.</i>"
    )


def _pro_root_keyboard(page_index: int) -> InlineKeyboardMarkup:
    total = len(_PRO_PAGES)
    nav_row: list[InlineKeyboardButton] = []

    if page_index > 0:
        nav_row.append(
            InlineKeyboardButton("<", callback_data=f"pro:goto:{page_index - 1}")
        )
    else:
        nav_row.append(InlineKeyboardButton("<", callback_data="pro:noop"))

    nav_row.append(
        InlineKeyboardButton(
            f"{page_index + 1}/{total}", callback_data="pro:noop"
        )
    )

    if page_index < total - 1:
        nav_row.append(
            InlineKeyboardButton(">", callback_data=f"pro:goto:{page_index + 1}")
        )
    else:
        nav_row.append(InlineKeyboardButton(">", callback_data="pro:noop"))

    tree_row = [
        InlineKeyboardButton(
            "◎ Sovereign Vault",
            callback_data=f"tree:open:vault:{page_index}",
        ),
        InlineKeyboardButton(
            "⎘ API Hooks",
            callback_data=f"tree:open:api:{page_index}",
        ),
    ]

    return InlineKeyboardMarkup([nav_row, tree_row])


def _tree_keyboard(return_page: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "↩ Back", callback_data=f"tree:back:{return_page}"
                )
            ]
        ]
    )


def _tree_html(slug: str) -> str:
    meta = _TREE_SCREENS[slug]
    badge = random.choice(MAGIC_EMOJIS)
    return (
        f"{badge} <b>{meta['title']}</b>\n\n"
        f"<blockquote>{meta['body']}</blockquote>\n\n"
        f"<i>Nested route — same message surface.</i>"
    )


async def _edit_or_reply_pro(
    update: Update,
    *,
    page_index: int = 0,
    tree_slug: Optional[str] = None,
    return_page: int = 0,
) -> None:
    query = update.callback_query
    if tree_slug and tree_slug in _TREE_SCREENS:
        text = _tree_html(tree_slug)
        kb = _tree_keyboard(return_page)
    else:
        text = _pro_page_html(page_index)
        kb = _pro_root_keyboard(page_index)

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=kb,
            parse_mode=ParseMode.HTML,
        )
    elif update.message:
        await update.message.reply_text(
            text=text,
            reply_markup=kb,
            parse_mode=ParseMode.HTML,
        )


_GOTO_RE = re.compile(r"^pro:goto:(\d+)$")
_NOOP_RE = re.compile(r"^pro:noop$")
_TREE_OPEN_RE = re.compile(r"^tree:open:(vault|api):(\d+)$")
_TREE_BACK_RE = re.compile(r"^tree:back:(\d+)$")


async def _handle_pro_callbacks(
    update: Update, context: ContextTypes.DEFAULT_TYPE, data: str
) -> None:
    query = update.callback_query
    if not query:
        return

    m = _GOTO_RE.match(data)
    if m:
        idx = int(m.group(1))
        if 0 <= idx < len(_PRO_PAGES):
            await query.answer()
            await _edit_or_reply_pro(update, page_index=idx)
        else:
            logger.warning("pro:goto out of range idx=%s", idx)
            await query.answer()
        return

    if _NOOP_RE.match(data):
        await query.answer()
        return

    logger.warning("Unknown pro callback data=%r", data)
    await query.answer()


async def _handle_tree_callbacks(
    update: Update, context: ContextTypes.DEFAULT_TYPE, data: str
) -> None:
    query = update.callback_query
    if not query:
        return

    m = _TREE_OPEN_RE.match(data)
    if m:
        slug = m.group(1)
        return_page = int(m.group(2))
        return_page = max(0, min(return_page, len(_PRO_PAGES) - 1))
        await query.answer()
        await _edit_or_reply_pro(
            update,
            tree_slug=slug,
            return_page=return_page,
        )
        return

    m = _TREE_BACK_RE.match(data)
    if m:
        idx = int(m.group(1))
        idx = max(0, min(idx, len(_PRO_PAGES) - 1))
        await query.answer()
        await _edit_or_reply_pro(update, page_index=idx)
        return

    logger.warning("Unknown tree callback data=%r", data)
    await query.answer()


register_callback("pro", _handle_pro_callbacks)
register_callback("tree", _handle_tree_callbacks)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_text = (
        f"{random.choice(MAGIC_EMOJIS)} <b>Welcome to STIX MAGIC TEXT</b>\n\n"
        f"<blockquote>I am the ultimate text automation module.\n"
        f"Just drop your plain text here, and I will format it into "
        f"premium glassmorphism blocks wrapped in elite animated emojis.</blockquote>\n\n"
        f"<i>Ready to elevate your prose? Type something.</i> ✨"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)


async def pro_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _edit_or_reply_pro(update, page_index=0)
    logger.info("/pro deck opened chat_id=%s", update.effective_chat.id if update.effective_chat else None)


async def magic_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    raw_text = update.message.text
    if not raw_text:
        return

    magic_emoji_1 = random.choice(MAGIC_EMOJIS)
    magic_emoji_2 = random.choice(MAGIC_EMOJIS)

    formatted_text = (
        f"{magic_emoji_1} <b>STIX PROCESSING:</b>\n\n"
        f"<blockquote>{raw_text}</blockquote>\n\n"
        f"{magic_emoji_2} <i>Formatted by STIX MAGIC</i>"
    )

    await update.message.reply_text(formatted_text, parse_mode=ParseMode.HTML)

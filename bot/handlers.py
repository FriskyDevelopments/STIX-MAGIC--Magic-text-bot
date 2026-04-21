from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import re
from uuid import uuid4
from html import escape
from typing import Awaitable, Callable, Optional

import requests
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
_USER_PERSONA: dict[int, str] = {}
_PENDING_RELAYS: dict[str, dict[str, object]] = {}
_DEBUGGER_IDS: set[int] = set()
_AUTHORIZED_GROUPS: set[int] = set()

_PUPSONA_SYSTEM_PROMPTS: dict[str, str] = {
    "alchemy": (
        "You are Alchemy Curator, an admin-first creative assistant for Pupbot. "
        "Tone is fun but serious: confident, polished, and focused on outcomes. "
        "Convert rough input into high-clarity copy that can be used immediately. "
        "Keep replies concise unless complexity demands more detail. "
        "Plain text only, no markdown."
    ),
    "antigravity": (
        "You are Antigravity Developer Core, an admin operations copilot. "
        "Tone is fun but serious: clear, tactical, zero fluff. "
        "Return operational guidance with intent, risk, and action that can be executed now. "
        "Keep simple things short and complex things precise. "
        "Plain text only, no markdown."
    ),
}


def _parse_group_id_list(raw: str) -> set[int]:
    group_ids: set[int] = set()
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            group_ids.add(int(chunk))
        except ValueError:
            logger.warning("Skipping invalid group id in env: %r", chunk)
    return group_ids


def _load_linked_main_groups() -> set[int]:
    linked = _parse_group_id_list(os.getenv("MAIN_GROUP_IDS", ""))
    primary = os.getenv("MAIN_GROUP_ID", "").strip()
    if primary:
        try:
            linked.add(int(primary))
        except ValueError:
            logger.warning("Invalid MAIN_GROUP_ID=%r ignored", primary)
    return linked


def _admin_lounge_id() -> Optional[int]:
    raw = os.getenv("ADMIN_LOUNGE_ID", "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        logger.warning("Invalid ADMIN_LOUNGE_ID=%r ignored", raw)
        return None


_LINKED_MAIN_GROUPS: set[int] = _load_linked_main_groups()


def _relay_confirm_keyboard(relay_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton("✅ Send to Main Groups", callback_data=f"relaybox:send:{relay_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"relaybox:cancel:{relay_id}"),
            ]
        ]
    )


async def _resolve_group_meta(
    context: ContextTypes.DEFAULT_TYPE, group_id: int
) -> tuple[str, Optional[str]]:
    """Return display title and best-effort open URL for a linked group."""
    title = str(group_id)
    url: Optional[str] = None
    try:
        chat = await context.bot.get_chat(group_id)
        title = chat.title or chat.full_name or str(group_id)
        if chat.username:
            url = f"https://t.me/{chat.username}"
        else:
            try:
                invite = await context.bot.create_chat_invite_link(chat_id=group_id, creates_join_request=False)
                url = invite.invite_link
            except Exception:
                url = None
    except Exception as exc:
        logger.warning("Failed to resolve linked group metadata group_id=%s err=%s", group_id, exc)
    return title, url


async def _queue_relay_confirmation(
    *,
    message,
    payload: str,
    actor_user_id: int,
    actor_name: str,
    origin_chat_id: int,
) -> None:
    relay_id = uuid4().hex[:10]
    targets = sorted(_LINKED_MAIN_GROUPS)
    _PENDING_RELAYS[relay_id] = {
        "payload": payload,
        "from_user_id": actor_user_id,
        "from_name": actor_name,
        "origin_chat_id": origin_chat_id,
        "target_group_ids": targets,
    }
    target_preview = ", ".join(str(gid) for gid in targets)
    await message.reply_text(
        "📡 <b>Relay staged.</b>\n\n"
        f"<b>Targets:</b> <code>{target_preview}</code>\n"
        f"<blockquote>{escape(payload, quote=False)}</blockquote>\n\n"
        "Confirm send?",
        reply_markup=_relay_confirm_keyboard(relay_id),
        parse_mode=ParseMode.HTML,
    )


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


async def _handle_relaybox_callbacks(
    update: Update, context: ContextTypes.DEFAULT_TYPE, data: str
) -> None:
    query = update.callback_query
    if not query:
        return

    parts = data.split(":")
    if len(parts) != 3:
        await query.answer("Invalid relay action.")
        return
    _, action, relay_id = parts
    pending = _PENDING_RELAYS.get(relay_id)
    if not pending:
        await query.answer("Relay request expired.")
        return

    from_user_id = int(pending["from_user_id"])
    if query.from_user.id != from_user_id:
        await query.answer("Only the initiating admin can confirm this relay.")
        return

    if action == "cancel":
        _PENDING_RELAYS.pop(relay_id, None)
        await query.edit_message_text("❌ <b>Relay canceled.</b>", parse_mode=ParseMode.HTML)
        await query.answer()
        return

    if action != "send":
        await query.answer("Unknown relay action.")
        return

    payload = str(pending["payload"])
    actor_name = str(pending["from_name"])
    origin_chat_id = int(pending["origin_chat_id"])
    target_group_ids = [int(gid) for gid in pending["target_group_ids"]]
    _PENDING_RELAYS.pop(relay_id, None)

    envelope = (
        "📡 <b>Admin Relay</b>\n\n"
        f"<b>From:</b> {escape(actor_name)} (<code>{from_user_id}</code>)\n"
        f"<b>Origin Chat:</b> <code>{origin_chat_id}</code>\n\n"
        f"<blockquote>{escape(payload, quote=False)}</blockquote>"
    )
    sent = 0
    failed: list[int] = []
    for group_id in target_group_ids:
        try:
            await context.bot.send_message(
                chat_id=group_id,
                text=envelope,
                parse_mode=ParseMode.HTML,
            )
            sent += 1
        except Exception as exc:
            logger.warning("Relay send failed group_id=%s err=%s", group_id, exc)
            failed.append(group_id)

    status = f"✅ <b>Relay sent.</b> {sent}/{len(target_group_ids)} target(s) delivered."
    if failed:
        status += "\n⚠️ Failed: " + ", ".join(str(g) for g in failed)
    await query.edit_message_text(status, parse_mode=ParseMode.HTML)
    await query.answer("Relay processed.")


register_callback("relaybox", _handle_relaybox_callbacks)


async def _handle_grouppeek_callbacks(
    update: Update, context: ContextTypes.DEFAULT_TYPE, data: str
) -> None:
    query = update.callback_query
    if not query:
        return
    parts = data.split(":")
    if len(parts) != 2:
        await query.answer("Invalid group action.")
        return
    group_id = parts[1]
    await query.answer(f"Group ID: {group_id}", show_alert=True)


register_callback("grouppeek", _handle_grouppeek_callbacks)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_text = (
        "🐾 <b>PUPBOT COMMAND CENTER</b> 🐾\n\n"
        "<b>🎭 Personas &amp; Modes</b>\n"
        "• /alchemy - Summon the Λlchemy Curator Wizard\n"
        "• /antigravity - Summon the Antigravity Developer Core\n\n"
        "<blockquote><b>Admin Pupsona:</b> fun tone, serious execution, task-first responses.</blockquote>\n\n"
        "<b>🛠️ System &amp; Debugging</b>\n"
        "• /ticket - Open the Jules Bug Reporter\n"
        "• /ping - Quick feedback &amp; Help Menu\n"
        "• /ping &lt;msg&gt; - Send instant feedback\n\n"
        "<b>🔐 Alpha / Admin Only</b>\n"
        "• /authorize_group - Allow Pupbot to speak\n"
        "• /add_debugger &lt;id&gt; - Grant Reporter access\n"
        "• /link_group &lt;chat_id&gt; - Link a main target group\n"
        "• /unlink_group &lt;chat_id&gt; - Remove a linked group\n"
        "• /groups - Show linked groups\n\n"
        "<b>🖼️ Image Support</b>\n"
        "• Send a photo + caption when you want analysis\n"
        "• If no caption, Pupbot waits for your instruction\n\n"
        "<i>Tip: typing 'promo' in the Admin Lounge triggers Omni-Channel Broadcast.</i>"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start_command(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start_command(update, context)


async def ticket_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "<b>Ticket mode online.</b>\n"
        "Send: issue, expected behavior, current behavior.",
        parse_mode=ParseMode.HTML,
    )


async def _is_operator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if not user:
        return False

    owner_ids: set[int] = set()
    for key in ("PUPBOT_OWNER_IDS", "ALPHA_USER_IDS", "OWNER_USER_IDS"):
        raw = os.getenv(key, "")
        if raw.strip():
            owner_ids.update(
                int(chunk.strip())
                for chunk in raw.split(",")
                if chunk.strip().isdigit()
            )
    if owner_ids and user.id in owner_ids:
        return True

    # Fallback: group creator/admin can trigger operator routes.
    if chat and chat.type in ("group", "supergroup"):
        try:
            member = await context.bot.get_chat_member(chat.id, user.id)
            if member.status in ("administrator", "creator"):
                return True
        except Exception as exc:
            logger.warning("Operator check failed for user_id=%s: %s", user.id, exc)

    return False


async def _persona_llm_response(raw_text: str, persona: str) -> str:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        if persona == "alchemy":
            return (
                "Transmute this into cinematic copy with elevated cadence.\n"
                f"Core spark: {raw_text}"
            )
        return (
            f"Intent: {raw_text}\n"
            "Risk: context not fully scoped\n"
            "Next action: provide target system + desired admin outcome."
        )

    prompt = _PUPSONA_SYSTEM_PROMPTS.get(persona, _PUPSONA_SYSTEM_PROMPTS["antigravity"])

    def _call_groq() -> str:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": raw_text},
                ],
                "temperature": 0.8 if persona == "alchemy" else 0.35,
            },
            timeout=25,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
        return str(content).strip()

    try:
        return await asyncio.to_thread(_call_groq)
    except Exception as exc:
        logger.warning("Persona LLM fallback triggered persona=%s err=%s", persona, exc)
        if persona == "alchemy":
            return (
                "High-aesthetic pulse generated in fallback mode.\n"
                f"Seed line: {raw_text}"
            )
        return (
            f"Intent: {raw_text}\n"
            "Risk: inference backend unavailable\n"
            "Next action: retry command with stabilized backend."
        )


async def antigravity_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    user = update.effective_user
    if not message or not user:
        return
    if not await _is_operator(update, context):
        await message.reply_text(
            "⛔ <b>Operator-only command.</b>\n\n"
            "<blockquote>Antigravity is restricted to Alpha/admin lanes.</blockquote>",
            parse_mode=ParseMode.HTML,
        )
        return
    _USER_PERSONA[user.id] = "antigravity"
    await message.reply_text(
        "<b>Antigravity enabled.</b>\n"
        "Replies now use clean admin-debug format.",
        parse_mode=ParseMode.HTML,
    )


async def alchemy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    user = update.effective_user
    if not message or not user:
        return
    if not await _is_operator(update, context):
        await message.reply_text(
            "⛔ <b>Operator-only command.</b>\n\n"
            "<blockquote>Alchemy Curator is restricted to Alpha/admin lanes.</blockquote>",
            parse_mode=ParseMode.HTML,
        )
        return
    current = _USER_PERSONA.get(user.id, "pupbot")
    if current == "alchemy":
        _USER_PERSONA[user.id] = "pupbot"
        await message.reply_text(
            "<b>Alchemy disabled.</b>\nReturning to default mode.",
            parse_mode=ParseMode.HTML,
        )
        return
    _USER_PERSONA[user.id] = "alchemy"
    await message.reply_text(
        "<b>Alchemy enabled.</b>\n"
        "Replies now use concise curator output.",
        parse_mode=ParseMode.HTML,
    )


async def relay_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    user = update.effective_user
    chat = update.effective_chat
    if not message or not user or not chat:
        return

    if not await _is_operator(update, context):
        await message.reply_text(
            "⛔ <b>Operator-only command.</b>\n\n"
            "<blockquote>Relay is restricted to Alpha/admin lanes.</blockquote>",
            parse_mode=ParseMode.HTML,
        )
        return

    relay_payload = " ".join(context.args or []).strip()
    if not relay_payload and message.reply_to_message:
        relay_payload = (
            message.reply_to_message.text
            or message.reply_to_message.caption
            or ""
        ).strip()
    if not relay_payload:
        await message.reply_text(
            "📡 <b>Relay usage:</b> <code>/relay your message</code>\n\n"
            "<blockquote>You can also reply to a message and run <code>/relay</code>.</blockquote>",
            parse_mode=ParseMode.HTML,
        )
        return

    if not _LINKED_MAIN_GROUPS:
        await message.reply_text(
            "⚠️ <b>Relay unavailable:</b> no linked main groups.\n"
            "Use <code>/link_group &lt;chat_id&gt;</code> first.",
            parse_mode=ParseMode.HTML,
        )
        return

    await _queue_relay_confirmation(
        message=message,
        payload=relay_payload,
        actor_user_id=user.id,
        actor_name=user.full_name,
        origin_chat_id=chat.id,
    )


async def link_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message:
        return
    if not await _is_operator(update, context):
        await message.reply_text("⛔ <b>Operator-only command.</b>", parse_mode=ParseMode.HTML)
        return

    group_id: Optional[int] = None
    if context.args and context.args[0].strip():
        try:
            group_id = int(context.args[0].strip())
        except ValueError:
            await message.reply_text("⚠️ Invalid group id.", parse_mode=ParseMode.HTML)
            return
    elif update.effective_chat:
        group_id = update.effective_chat.id

    if group_id is None:
        await message.reply_text(
            "Usage: <code>/link_group &lt;chat_id&gt;</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    _LINKED_MAIN_GROUPS.add(group_id)
    title, url = await _resolve_group_meta(context, group_id)
    extra = f"\n🔗 {url}" if url else ""
    await message.reply_text(
        f"✅ Linked group: <b>{escape(title)}</b> (<code>{group_id}</code>).\n"
        f"Total linked groups: <b>{len(_LINKED_MAIN_GROUPS)}</b>.",
        parse_mode=ParseMode.HTML,
    )
    if extra:
        await message.reply_text(
            f"<b>Open group:</b>\n{escape(extra)}",
        parse_mode=ParseMode.HTML,
    )


async def unlink_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message:
        return
    if not await _is_operator(update, context):
        await message.reply_text("⛔ <b>Operator-only command.</b>", parse_mode=ParseMode.HTML)
        return

    group_id: Optional[int] = None
    if context.args and context.args[0].strip():
        try:
            group_id = int(context.args[0].strip())
        except ValueError:
            await message.reply_text("⚠️ Invalid group id.", parse_mode=ParseMode.HTML)
            return
    elif update.effective_chat:
        group_id = update.effective_chat.id

    if group_id is None:
        await message.reply_text(
            "Usage: <code>/unlink_group &lt;chat_id&gt;</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    if group_id in _LINKED_MAIN_GROUPS:
        _LINKED_MAIN_GROUPS.remove(group_id)
        await message.reply_text(
            f"🧹 Unlinked group <code>{group_id}</code>.",
            parse_mode=ParseMode.HTML,
        )
    else:
        await message.reply_text(
            f"⚠️ Group <code>{group_id}</code> was not linked.",
            parse_mode=ParseMode.HTML,
        )


async def groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message:
        return
    if not await _is_operator(update, context):
        await message.reply_text("⛔ <b>Operator-only command.</b>", parse_mode=ParseMode.HTML)
        return

    if not _LINKED_MAIN_GROUPS:
        await message.reply_text(
            "No linked main groups.\nUse <code>/link_group &lt;chat_id&gt;</code>.",
            parse_mode=ParseMode.HTML,
        )
        return

    lines: list[str] = []
    inline_rows: list[list[InlineKeyboardButton]] = []
    for gid in sorted(_LINKED_MAIN_GROUPS):
        title, url = await _resolve_group_meta(context, gid)
        lines.append(f"• <b>{escape(title)}</b> (<code>{gid}</code>)")
        if url:
            inline_rows.append([InlineKeyboardButton(f"Open: {title[:28]}", url=url)])
        else:
            inline_rows.append([InlineKeyboardButton(f"Group ID: {gid}", callback_data=f"grouppeek:{gid}")])
    await message.reply_text(
        "<b>Linked main groups:</b>\n" + "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_rows) if inline_rows else None,
        parse_mode=ParseMode.HTML,
    )


async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _is_operator(update, context):
        await update.message.reply_text(
            "⛔ <b>Operator-only command.</b>\n\n"
            "<blockquote>Invite generation is restricted to Alpha/admin lanes.</blockquote>",
            parse_mode=ParseMode.HTML,
        )
        return
    await update.message.reply_text(
        "🔗 <b>Invite command received.</b>\n\n"
        "<blockquote>One-use invite generation is restricted to authorized operators.</blockquote>",
        parse_mode=ParseMode.HTML,
    )


async def authorize_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    chat = update.effective_chat
    if not message or not chat:
        return
    if not await _is_operator(update, context):
        await message.reply_text(
            "⛔ <b>Operator-only command.</b>\n\n"
            "<blockquote>Group authorization is restricted to Alpha/admin lanes.</blockquote>",
            parse_mode=ParseMode.HTML,
        )
        return

    _AUTHORIZED_GROUPS.add(chat.id)
    title = chat.title or str(chat.id)
    await message.reply_text(
        "✅ <b>Group authorized.</b>\n\n"
        f"<blockquote>{escape(title)} (<code>{chat.id}</code>) is now approved for Pupbot operator workflows.</blockquote>",
        parse_mode=ParseMode.HTML,
    )


async def add_debugger_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message:
        return
    if not await _is_operator(update, context):
        await message.reply_text(
            "⛔ <b>Operator-only command.</b>\n\n"
            "<blockquote>Debugger enrollment is restricted to Alpha/admin lanes.</blockquote>",
            parse_mode=ParseMode.HTML,
        )
        return

    if not context.args or not context.args[0].strip().lstrip("-").isdigit():
        await message.reply_text(
            "Usage: <code>/add_debugger &lt;user_id&gt;</code>",
            parse_mode=ParseMode.HTML,
        )
        return
    debugger_id = int(context.args[0].strip())
    _DEBUGGER_IDS.add(debugger_id)
    await message.reply_text(
        "🛠 <b>Debugger added.</b>\n\n"
        f"<blockquote>User <code>{debugger_id}</code> now has debugger access.</blockquote>",
        parse_mode=ParseMode.HTML,
    )


async def pro_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _edit_or_reply_pro(update, page_index=0)
    logger.info("/pro deck opened chat_id=%s", update.effective_chat.id if update.effective_chat else None)


async def _handle_text_payload(
    update: Update, context: ContextTypes.DEFAULT_TYPE, raw_text: str
) -> None:
    safe_text = escape(raw_text, quote=False)
    user = update.effective_user
    persona = _USER_PERSONA.get(user.id, "pupbot") if user else "pupbot"
    chat = update.effective_chat

    # Admin Lounge quick trigger: "promo" stages a relay confirmation box.
    admin_lounge_id = _admin_lounge_id()
    lowered = raw_text.strip().lower()
    if (
        chat
        and user
        and admin_lounge_id is not None
        and chat.id == admin_lounge_id
        and lowered.startswith("promo")
        and await _is_operator(update, context)
    ):
        payload = ""
        if lowered == "promo" and update.message.reply_to_message:
            payload = (
                update.message.reply_to_message.text
                or update.message.reply_to_message.caption
                or ""
            ).strip()
        elif lowered.startswith("promo "):
            payload = raw_text.strip()[6:].strip()
        elif lowered.startswith("promo:"):
            payload = raw_text.strip()[6:].strip()

        if not payload:
            await update.message.reply_text(
                "<b>Promo trigger ready.</b>\n"
                "Use <code>promo your message</code> or reply to a message with <code>promo</code>.",
                parse_mode=ParseMode.HTML,
            )
            return

        if not _LINKED_MAIN_GROUPS:
            await update.message.reply_text(
                "⚠️ No linked main groups.\nUse <code>/link_group &lt;chat_id&gt;</code> first.",
                parse_mode=ParseMode.HTML,
            )
            return

        await _queue_relay_confirmation(
            message=update.message,
            payload=payload,
            actor_user_id=user.id,
            actor_name=user.full_name,
            origin_chat_id=chat.id,
        )
        return

    if persona == "alchemy":
        generated = await _persona_llm_response(raw_text, "alchemy")
        formatted_text = f"<b>Alchemy</b>\n{escape(generated, quote=False)}"
        await update.message.reply_text(formatted_text, parse_mode=ParseMode.HTML)
        return

    if persona == "antigravity":
        generated = await _persona_llm_response(raw_text, "antigravity")
        lines = [ln.strip() for ln in generated.splitlines() if ln.strip()]
        if len(lines) >= 3:
            normalized = "\n".join(lines[:3])
        else:
            normalized = (
                f"Intent: {raw_text}\n"
                "Risk: unclear scope\n"
                "Action: provide target system and expected result."
            )
        formatted_text = f"<b>Antigravity</b>\n{escape(normalized, quote=False)}"
        await update.message.reply_text(formatted_text, parse_mode=ParseMode.HTML)
        return

    formatted_text = f"<b>Pupbot</b>\n{safe_text}"

    await update.message.reply_text(formatted_text, parse_mode=ParseMode.HTML)


async def magic_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    await _handle_text_payload(update, context, update.message.text)


async def magic_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message:
        return

    caption = (message.caption or "").strip()
    if not caption:
        await message.reply_text(
            "<b>Image received.</b>\n"
            "Send a caption/instruction only if you want image analysis.",
            parse_mode=ParseMode.HTML,
        )
        return

    intent_hint = caption.lower()
    wants_analysis = any(
        key in intent_hint
        for key in (
            "analyze",
            "analyse",
            "describe",
            "caption",
            "extract",
            "ocr",
            "read",
            "what",
            "summarize",
            "summarise",
            "help",
            "fix",
            "debug",
        )
    )

    if not wants_analysis:
        await message.reply_text(
            "<b>Image noted.</b>\n"
            "I will process it when you explicitly ask (e.g. 'analyze this image').",
            parse_mode=ParseMode.HTML,
        )
        return

    await _handle_text_payload(update, context, f"[Image Request] {caption}")

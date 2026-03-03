#!/usr/bin/env python3
"""
🦇 BRUCE | Digital Agency — Admin Bot (Alfred)
Receives all orders from Bruce bot and lets you manage them.
Run alongside bot.py — shares orders.json.
"""

import os
import json
import logging
import functools
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes
)

# ─── CONFIG ────────────────────────────────────────────────────────────────────
# ─── CONFIG ────────────────────────────────────────────────────────────────────
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
ADMIN_CHAT_ID   = int(os.getenv("ADMIN_CHAT_ID", "0"))

ORDERS_FILE     = "orders.json"  # shared with bot.py

logging.basicConfig(
    format="%(asctime)s | ALFRED | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

STATUSES = ["new", "progress", "done", "cancelled"]
STATUS_EMOJI = {
    "new":       "🔵",
    "progress":  "⚡",
    "done":      "✅",
    "cancelled": "❌",
}

# ─── ADMIN GUARD ───────────────────────────────────────────────────────────────
def admin_only(func):
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or update.effective_user.id != ADMIN_CHAT_ID:
            if update.message:
                await update.message.reply_text("🚫 Access denied. This is the Batcave.")
            return
        return await func(update, context)
    return wrapper

# ─── HELPERS ───────────────────────────────────────────────────────────────────
def load_orders():
    try:
        with open(ORDERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_orders(orders):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=2, ensure_ascii=False)

def get_order(order_id: int):
    return next((o for o in load_orders() if o.get("id") == order_id), None)

def update_order_status(order_id: int, new_status: str) -> bool:
    orders = load_orders()
    for o in orders:
        if o.get("id") == order_id:
            o["status"] = new_status
            save_orders(orders)
            return True
    return False

def fmt_order_card(o, full=False) -> str:
    sid = str(o["id"]).zfill(3)
    st  = STATUS_EMOJI.get(o.get("status", "new"), "❓")
    ts  = o.get("timestamp", "")[:16].replace("T", " ")

    if not full:
        return (
            f"{st} *Order #{sid}* — {o.get('service_name','—')}\n"
            f"👤 {o.get('user_name','—')} ({o.get('username','—')})\n"
            f"💰 {o.get('budget','—')} | 🕐 {ts}\n"
        )
    return (
        f"🦇 *ORDER #{sid}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Client:* {o.get('user_name','—')}\n"
        f"🔗 *Handle:* {o.get('username','—')}\n"
        f"🆔 *User ID:* `{o.get('user_id','—')}`\n"
        f"🌐 *Language:* {o.get('lang','en').upper()}\n"
        f"⚡ *Service:* {o.get('service_name','—')}\n"
        f"📝 *Details:* {o.get('details','—')}\n"
        f"💰 *Budget:* {o.get('budget','—')}\n"
        f"📬 *Contact:* {o.get('contact','—')}\n"
        f"🕐 *Time:* {ts}\n"
        f"📊 *Status:* {STATUS_EMOJI.get(o.get('status','new'),'❓')} {o.get('status','new').upper()}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )

def order_action_keyboard(order_id: int, status: str):
    buttons = []
    if status != "progress":
        buttons.append(InlineKeyboardButton("⚡ In Progress", callback_data=f"st_{order_id}_progress"))
    if status != "done":
        buttons.append(InlineKeyboardButton("✅ Done",        callback_data=f"st_{order_id}_done"))
    if status != "cancelled":
        buttons.append(InlineKeyboardButton("❌ Cancel",      callback_data=f"st_{order_id}_cancelled"))
    if status != "new":
        buttons.append(InlineKeyboardButton("🔵 New",         callback_data=f"st_{order_id}_new"))
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton("🗑 Delete Order", callback_data=f"del_{order_id}")])
    return InlineKeyboardMarkup(rows)

# ─── COMMANDS ──────────────────────────────────────────────────────────────────
@admin_only
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*🦇 Alfred reporting for duty.*\n\n"
        "I'll relay every order from Bruce Agency directly to you, Master.\n\n"
        "*Available commands:*\n"
        "/orders — view all orders\n"
        "/new — new orders only\n"
        "/stats — mission statistics\n"
        "/order 3 — view order \\#3\n"
        "/done 3 — mark order \\#3 as done\n"
        "/progress 3 — mark as in progress\n"
        "/cancel 3 — cancel order \\#3\n"
        "/delete 3 — delete order \\#3\n\n"
        "_The night shift has begun\\._",
        parse_mode="MarkdownV2"
    )

@admin_only
async def cmd_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orders = load_orders()
    if not orders:
        await update.message.reply_text("🦇 Gotham is quiet. No orders yet.")
        return

    filter_status = context.args[0].lower() if context.args else None
    if filter_status:
        orders = [o for o in orders if o.get("status") == filter_status]

    orders = list(reversed(orders))[:20]

    if not orders:
        await update.message.reply_text(f"No orders with status: {filter_status}")
        return

    label = filter_status.upper() if filter_status else "ALL"
    text = f"🦇 *{label} ORDERS* ({len(orders)} shown)\n\n"
    keyboard = []
    for o in orders:
        text += fmt_order_card(o) + "\n"
        sid = str(o["id"]).zfill(3)
        keyboard.append([InlineKeyboardButton(
            f"{STATUS_EMOJI.get(o.get('status','new'),'❓')} #{sid} — {o.get('user_name','—')}",
            callback_data=f"view_{o['id']}"
        )])

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@admin_only
async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.args = ["new"]
    await cmd_orders(update, context)

@admin_only
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orders = load_orders()
    total     = len(orders)
    new_c     = sum(1 for o in orders if o.get("status") == "new")
    progress  = sum(1 for o in orders if o.get("status") == "progress")
    done      = sum(1 for o in orders if o.get("status") == "done")
    cancelled = sum(1 for o in orders if o.get("status") == "cancelled")

    services = {}
    for o in orders:
        sn = o.get("service_name", "Unknown")
        services[sn] = services.get(sn, 0) + 1
    top = sorted(services.items(), key=lambda x: -x[1])[:3]
    top_text = "\n".join(f"  {s}: {c}" for s, c in top) or "  —"

    await update.message.reply_text(
        f"*🦇 BATCOMPUTER STATISTICS*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📥 Total:        *{total}*\n"
        f"🔵 New:          *{new_c}*\n"
        f"⚡ In progress:  *{progress}*\n"
        f"✅ Done:         *{done}*\n"
        f"❌ Cancelled:    *{cancelled}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"*Top services:*\n{top_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_Alfred has spoken._",
        parse_mode="Markdown"
    )

@admin_only
async def cmd_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /order 3")
        return
    try:
        oid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid order ID. Example: /order 3")
        return
    o = get_order(oid)
    if not o:
        await update.message.reply_text(f"🦇 Order #{oid} not found in the Batcomputer.")
        return
    await update.message.reply_text(
        fmt_order_card(o, full=True),
        parse_mode="Markdown",
        reply_markup=order_action_keyboard(oid, o.get("status", "new"))
    )

async def _set_status(update: Update, context: ContextTypes.DEFAULT_TYPE, new_status: str):
    if not context.args:
        await update.message.reply_text(f"Usage: /{new_status} 3")
        return
    try:
        oid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid ID. Example: /done 3")
        return
    if update_order_status(oid, new_status):
        await update.message.reply_text(
            f"{STATUS_EMOJI[new_status]} Order *#{str(oid).zfill(3)}* → *{new_status.upper()}*",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(f"🦇 Order #{oid} not found.")

@admin_only
async def cmd_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _set_status(update, context, "done")

@admin_only
async def cmd_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _set_status(update, context, "progress")

@admin_only
async def cmd_cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _set_status(update, context, "cancelled")

@admin_only
async def cmd_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /delete 3")
        return
    try:
        oid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid ID.")
        return
    orders = load_orders()
    new_orders = [o for o in orders if o.get("id") != oid]
    if len(new_orders) == len(orders):
        await update.message.reply_text(f"🦇 Order #{oid} not found.")
    else:
        save_orders(new_orders)
        await update.message.reply_text(
            f"🗑 Order *#{str(oid).zfill(3)}* erased from the Batcomputer.",
            parse_mode="Markdown"
        )

# ─── CALLBACKS ─────────────────────────────────────────────────────────────────
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not update.effective_user or update.effective_user.id != ADMIN_CHAT_ID:
        await query.answer("🚫 Access denied.")
        return
    await query.answer()
    data = query.data

    if data.startswith("view_"):
        oid = int(data.split("_")[1])
        o = get_order(oid)
        if not o:
            await query.edit_message_text("Order not found.")
            return
        await query.edit_message_text(
            fmt_order_card(o, full=True),
            parse_mode="Markdown",
            reply_markup=order_action_keyboard(oid, o.get("status", "new"))
        )

    elif data.startswith("st_"):
        parts = data.split("_", 2)
        oid = int(parts[1])
        new_status = parts[2]
        update_order_status(oid, new_status)
        o = get_order(oid)
        await query.edit_message_text(
            fmt_order_card(o, full=True),
            parse_mode="Markdown",
            reply_markup=order_action_keyboard(oid, new_status)
        )

    elif data.startswith("del_"):
        oid = int(data.split("_")[1])
        orders = load_orders()
        save_orders([o for o in orders if o.get("id") != oid])
        await query.edit_message_text(
            f"🗑 Order *#{str(oid).zfill(3)}* deleted from the Batcomputer.",
            parse_mode="Markdown"
        )

# ─── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    if ADMIN_CHAT_ID == 0:
        logger.error("ADMIN_CHAT_ID is not set! Export it before running.")
        return

    app = Application.builder().token(ADMIN_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("orders",   cmd_orders))
    app.add_handler(CommandHandler("new",      cmd_new))
    app.add_handler(CommandHandler("stats",    cmd_stats))
    app.add_handler(CommandHandler("order",    cmd_order))
    app.add_handler(CommandHandler("done",     cmd_done))
    app.add_handler(CommandHandler("progress", cmd_progress))
    app.add_handler(CommandHandler("cancel",   cmd_cancel_order))
    app.add_handler(CommandHandler("delete",   cmd_delete))
    app.add_handler(CallbackQueryHandler(callback_handler))

    logger.info(f"🦇 Alfred is online. Serving admin ID: {ADMIN_CHAT_ID}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TOKEN")  # Support both BOT_TOKEN and TOKEN
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
DATA_FILE = "data.json"

# Parse admin IDs
ADMIN_IDS = []
if ADMIN_IDS_STR:
    try:
        ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(",") if admin_id.strip()]
    except ValueError:
        print("Warning: Invalid ADMIN_IDS format. Should be comma-separated integers.")
        ADMIN_IDS = []


def load_data() -> Dict:
    """Load data from JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"events": {}, "entries": {}}


def save_data(data: Dict):
    """Save data to JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    return user_id in ADMIN_IDS


def is_private_chat(update: Update) -> bool:
    """Check if message is from a private chat."""
    return update.effective_chat.type == "private"


def is_bot_mentioned(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the bot is mentioned in a group message."""
    if not update.message or update.effective_chat.type == "private":
        return False
    
    try:
        bot_username = context.bot.username.lower()
    except:
        return False
    
    # Check if bot is mentioned via @username in entities
    if update.message.entities:
        for entity in update.message.entities:
            if entity.type == "mention":
                mentioned_text = update.message.text[entity.offset:entity.offset + entity.length].lower()
                if mentioned_text == f"@{bot_username}":
                    return True
    
    # Also check if bot is mentioned in the message text (fallback)
    message_text = (update.message.text or "").lower()
    if f"@{bot_username}" in message_text:
        return True
    
    return False


def can_interact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user can interact with bot (private chat or bot mentioned in group)."""
    return is_private_chat(update) or is_bot_mentioned(update, context)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    if not can_interact(update, context):
        return

    user_id = update.effective_user.id
    is_user_admin = is_admin(user_id)

    welcome_text = "Welcome to Whip Bestell Bot! 🎉\n\n"
    
    if is_user_admin:
        welcome_text += "You are an admin. You can:\n"
        welcome_text += "/events - Manage events\n"
        welcome_text += "/view_sums - View only sums (no personal details)\n"
    else:
        welcome_text += "You can:\n"
        welcome_text += "/list_events - View available events\n"
        welcome_text += "/enter_amount - Enter your money spent\n"

    await update.message.reply_text(welcome_text)


async def list_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all available events."""
    if not can_interact(update, context):
        return

    data = load_data()
    events = data.get("events", {})

    if not events:
        await update.message.reply_text("No events available yet.")
        return

    text = "📅 Available Events:\n\n"
    for event_id, event_data in events.items():
        text += f"• {event_data['name']}\n"
        text += f"  ID: {event_id}\n"
        text += f"  Created: {event_data.get('created_at', 'N/A')}\n\n"

    await update.message.reply_text(text)


async def enter_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the process of entering an amount."""
    if not can_interact(update, context):
        return

    data = load_data()
    events = data.get("events", {})

    if not events:
        await update.message.reply_text("No events available yet. Please ask an admin to create one.")
        return

    # Create inline keyboard with events
    keyboard = []
    for event_id, event_data in events.items():
        keyboard.append([InlineKeyboardButton(
            event_data['name'],
            callback_data=f"select_event_{event_id}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Select an event to enter your amount:",
        reply_markup=reply_markup
    )


async def handle_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle amount input from user."""
    # Only allow amount input in private chats for security
    if not is_private_chat(update):
        return

    # Check if user is in the process of entering an amount
    if "waiting_for_amount" not in context.user_data:
        return

    try:
        amount = float(update.message.text.replace(",", "."))
        if amount < 0:
            raise ValueError("Amount must be positive")

        event_id = context.user_data["waiting_for_amount"]
        user_id = update.effective_user.id
        username = update.effective_user.username or f"User_{user_id}"

        # Save entry
        data = load_data()
        if "entries" not in data:
            data["entries"] = {}

        entry_id = f"{event_id}_{user_id}_{datetime.now().timestamp()}"
        data["entries"][entry_id] = {
            "event_id": event_id,
            "user_id": user_id,
            "username": username,
            "amount": amount,
            "timestamp": datetime.now().isoformat()
        }

        save_data(data)

        # Notify user
        event_name = data["events"][event_id]["name"]
        await update.message.reply_text(
            f"✅ Successfully entered {amount:.2f} € for event: {event_name}"
        )

        # Notify admin (only amount, no personal details)
        admin_text = f"💰 New entry: {amount:.2f} €"
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_text
                )
            except Exception as e:
                print(f"Failed to notify admin {admin_id}: {e}")

        # Clear waiting state
        del context.user_data["waiting_for_amount"]

    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount. Please enter a valid number (e.g., 15.50 or 20)."
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()

    if query.data.startswith("select_event_"):
        event_id = query.data.replace("select_event_", "")
        context.user_data["waiting_for_amount"] = event_id
        await query.edit_message_text(
            f"Please enter the amount you spent (e.g., 15.50 or 20):"
        )


async def create_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a new event (admin only)."""
    if not can_interact(update, context):
        return

    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ This command is only available for admins.")
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /create_event <event_name>\n"
            "Example: /create_event New Year Party"
        )
        return

    event_name = " ".join(context.args)
    data = load_data()

    if "events" not in data:
        data["events"] = {}

    # Generate event ID
    event_id = f"event_{int(datetime.now().timestamp())}"

    data["events"][event_id] = {
        "name": event_name,
        "created_at": datetime.now().isoformat(),
        "created_by": user_id
    }

    save_data(data)

    await update.message.reply_text(
        f"✅ Event created successfully!\n"
        f"Name: {event_name}\n"
        f"ID: {event_id}"
    )


async def view_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all events with details (admin only)."""
    if not can_interact(update, context):
        return

    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ This command is only available for admins.")
        return

    data = load_data()
    events = data.get("events", {})

    if not events:
        await update.message.reply_text("No events created yet.")
        return

    text = "📅 All Events:\n\n"
    for event_id, event_data in events.items():
        # Count entries for this event
        entries = data.get("entries", {})
        event_entries = [e for e in entries.values() if e.get("event_id") == event_id]
        total = sum(e.get("amount", 0) for e in event_entries)

        text += f"• {event_data['name']}\n"
        text += f"  ID: {event_id}\n"
        text += f"  Total entries: {len(event_entries)}\n"
        text += f"  Total sum: {total:.2f} €\n"
        text += f"  Created: {event_data.get('created_at', 'N/A')}\n\n"

    await update.message.reply_text(text)


async def view_sums(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View only sums without personal details (admin only)."""
    if not can_interact(update, context):
        return

    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ This command is only available for admins.")
        return

    data = load_data()
    entries = data.get("entries", {})
    events = data.get("events", {})

    if not entries:
        await update.message.reply_text("No entries yet.")
        return

    # Group by event
    totals_by_event = {}

    for entry_id, entry_data in entries.items():
        event_id = entry_data.get("event_id")
        event_name = events.get(event_id, {}).get("name", "Unknown Event")
        amount = entry_data.get("amount", 0)

        if event_id not in totals_by_event:
            totals_by_event[event_id] = {"name": event_name, "total": 0, "count": 0}

        totals_by_event[event_id]["total"] += amount
        totals_by_event[event_id]["count"] += 1

    # Display only sums
    text = "💰 Sums by Event (No Personal Details):\n\n"
    for event_id, event_info in totals_by_event.items():
        text += f"📅 {event_info['name']}\n"
        text += f"   Total: {event_info['total']:.2f} €\n"
        text += f"   Entries: {event_info['count']}\n\n"

    # Overall total
    overall_total = sum(event_info["total"] for event_info in totals_by_event.values())
    text += f"💰 Overall Total: {overall_total:.2f} €"

    await update.message.reply_text(text)


async def handle_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when bot is mentioned in a group without a command."""
    # Only handle group mentions, not private chats
    if not update.message or is_private_chat(update):
        return
    
    # Only respond if bot is actually mentioned
    if not is_bot_mentioned(update, context):
        return
    
    # Check if it's already a command (handled by CommandHandler)
    if update.message.text and update.message.text.startswith("/"):
        return
    
    # Don't interfere with amount input (handled separately)
    if "waiting_for_amount" in context.user_data:
        return
    
    # Provide helpful information
    user_id = update.effective_user.id
    is_user_admin = is_admin(user_id)
    
    help_text = "👋 Hi! I'm the Whip Bestell Bot!\n\n"
    help_text += "You can use commands like:\n"
    
    if is_user_admin:
        help_text += "• /list_events - View available events\n"
        help_text += "• /enter_amount - Enter your money spent\n"
        help_text += "• /create_event <name> - Create a new event (admin)\n"
        help_text += "• /events - View all events (admin)\n"
        help_text += "• /view_sums - View sums (admin)\n"
    else:
        help_text += "• /list_events - View available events\n"
        help_text += "• /enter_amount - Enter your money spent\n"
    
    help_text += "\n💡 Tip: For entering amounts, please message me privately for security."
    
    await update.message.reply_text(help_text)


def main():
    """Start the bot."""
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN not found in .env file")
        return

    if not ADMIN_IDS:
        print("Warning: No ADMIN_IDS configured. Admin features will not work.")
        print("Add ADMIN_IDS to your .env file: ADMIN_IDS=your_telegram_user_id")
        print("To find your Telegram user ID, message @userinfobot on Telegram")

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list_events", list_events))
    application.add_handler(CommandHandler("enter_amount", enter_amount))
    application.add_handler(CommandHandler("create_event", create_event))
    application.add_handler(CommandHandler("events", view_events))
    application.add_handler(CommandHandler("view_sums", view_sums))
    application.add_handler(CallbackQueryHandler(button_callback))
    # Handle amount input (only in private chats)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount_input))
    # Handle mentions in groups (after amount input to avoid conflicts)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mention))

    # Start bot
    print("=" * 50)
    print("🤖 Whip Bestell Bot is starting...")
    print(f"✅ Bot token loaded: {BOT_TOKEN[:10]}...")
    print(f"👑 Admin IDs: {ADMIN_IDS if ADMIN_IDS else 'None configured'}")
    print("=" * 50)
    print("Bot is now running and ready to receive messages!")
    print("Press Ctrl+C to stop the bot.")
    print("=" * 50)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()


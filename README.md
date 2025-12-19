# Whip Bestell Bot

A Telegram bot for managing event expenses and bookings.

## Features

### For All Users
- View available events
- Enter money spent for events
- Interact with the bot in groups by mentioning it (@botname)

### For Admins
- Create events
- View only sums (without personal details)
- Receive notifications when users enter amounts

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure the bot:
   - Ensure your `.env` file contains:
     ```
     BOT_TOKEN=your_bot_token_here
     ADMIN_IDS=your_telegram_user_id,another_admin_id
     ```
   - To find your Telegram user ID, message [@userinfobot](https://t.me/userinfobot) on Telegram

3. Run the bot:
```bash
python bot.py
```

## Commands

### For All Users
- `/start` - Start the bot and see available commands
- `/list_events` - View all available events
- `/enter_amount` - Enter your money spent for an event

### For Admins
- `/create_event <event_name>` - Create a new event
- `/events` - View all events with statistics
- `/view_sums` - View only sums without personal details

## Data Storage

All data is stored in `data.json` file. This includes:
- Events (name, creation date, creator)
- Entries (event ID, user ID, username, amount, timestamp)

## Privacy & Usage

- The bot works in **private messages** and in **groups when mentioned** (@botname)
- Commands can be used in groups by mentioning the bot: `/list_events@botname`
- For entering amounts, users should message the bot privately for security
- When users enter amounts, admins receive notifications with only the amount (no personal details)
- Admins can only view sums without personal details using `/view_sums` command



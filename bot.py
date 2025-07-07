import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from urllib.parse import urlparse
from time import time
from datetime import datetime
import pytz  # Added for timezone support

# Replace with your Telegram Bot Token
TOKEN = "YOUR_BOT_TOKEN_HERE"

# Directory to store downloaded files
DOWNLOAD_DIR = "downloads"

# Ensure download directory exists
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Function to get IST time using pytz
def get_ist_time():
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist).strftime("%I:%M %p IST on %B %d, %Y")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    ist_time = get_ist_time()
    welcome_message = (
        f"👋 *Welcome to the File Upload Bot!* \n"
        f"Created by my master, *Raunak Singh*.\n\n"
        f"📅 Current time: {ist_time}\n"
        f"📤 Send me a direct file URL to download and upload it to Telegram.\n"
        f"ℹ️ Use /help for more information."
    )
    await update.message.reply_text(welcome_message, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command."""
    help_message = (
        "📚 *Help - File Upload Bot*\n"
        "Crafted by my master, *Raunak Singh*.\n\n"
        "🔧 *How to Use*:\n"
        "- Send a direct file URL (e.g., https://example.com/file.pdf).\n"
        "- I'll download and upload it to Telegram with progress updates.\n"
        "📋 *Commands*:\n"
        "- /start: Show welcome message.\n"
        "- /help: Show this help message.\n"
        "⚠️ *Notes*:\n"
        "- Files must be under 50MB (Telegram Bot API limit).\n"
        "- Ensure the URL is a direct link to a file."
    )
    await update.message.reply_text(help_message, parse_mode="Markdown")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle URLs sent by the user."""
    url = update.message.text
    user_id = update.effective_user.id
    status_message = await update.message.reply_text(
        "⏳ *Processing URL...*\n"
        "🔗 Link received. Starting download...",
        parse_mode="Markdown"
    )

    try:
        # Get file size for progress calculation
        response = requests.head(url, allow_redirects=True)
        file_size = int(response.headers.get("content-length", 0))
        filename = os.path.basename(urlparse(url).path) or f"file_{int(time())}.bin"
        file_path = os.path.join(DOWNLOAD_DIR, filename)

        # Download the file with progress updates
        downloaded_size = 0
        chunk_size = 8192
        last_update = 0

        with requests.get(url, stream=True) as response:
            if response.status_code != 200:
                await status_message.edit_text(
                    "❌ *Error*: Failed to download the file. Invalid URL or server error.",
                    parse_mode="Markdown"
                )
                return

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if file_size > 0:
                            progress = (downloaded_size / file_size) * 100
                            if time() - last_update >= 2:  # Update every 2 seconds
                                await status_message.edit_text(
                                    f"⏳ *Downloading...*\n"
                                    f"📥 Progress: {progress:.1f}%\n"
                                    f"📦 File: {filename}",
                                    parse_mode="Markdown"
                                )
                                last_update = time()

        # Check file size (Telegram bot API limit: 50MB)
        if os.path.getsize(file_path) > 50 * 1024 * 1024:
            await status_message.edit_text(
                "❌ *Error*: File is too large (over 50MB). Telegram Bot API does not support this size.",
                parse_mode="Markdown"
            )
            os.remove(file_path)
            return

        # Upload file to Telegram
        await status_message.edit_text(
            f"✅ *Download Complete!*\n"
            f"📤 Uploading {filename} to Telegram...",
            parse_mode="Markdown"
        )

        with open(file_path, 'rb') as f:
            await context.bot.send_document(
                chat_id=user_id,
                document=f,
                caption=f"🎉 Uploaded by the bot created by my master, *Raunak Singh*.",
                parse_mode="Markdown"
            )

        ist_time = get_ist_time()
        await status_message.edit_text(
            f"✅ *Success!*\n"
            f"📦 File `{filename}` uploaded successfully!\n"
            f"📅 Time: {ist_time}",
            parse_mode="Markdown"
        )

        # Clean up
        os.remove(file_path)

    except Exception as e:
        await status_message.edit_text(
            f"❌ *Error*: An issue occurred: {str(e)}\n"
            "Please check the URL and try again.",
            parse_mode="Markdown"
        )

def main() -> None:
    """Run the bot."""
    app = Application.builder().token(TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    # Start the bot
    print("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

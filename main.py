from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    PollHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.error import Forbidden, TelegramError
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Enable logging for debugging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token (replace with your actual token)
TOKEN = "YOUR_BOT_TOKEN_HERE"

# Email configuration (replace with your details)
EMAIL_SENDER = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"  # Use App Password for Gmail
EMAIL_RECEIVER = "recipient_email@example.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Target user ID to monitor (replace with the specific user's Telegram ID)
TARGET_USER_ID = 123456789  # Replace with the actual user ID

# Function to send email
async def send_email(subject: str, body: str):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        logger.info("Email sent successfully")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

# Modified message handler to react and email specific user's messages
async def react_to_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    user = update.message.from_user

    # React to "hello" (keeping original functionality)
    if message_text.lower() in "hello":
        await update.message.reply_text("Hi there! Nice to see you say hello!")

    # Check if the message is from the target user
    if user.id == TARGET_USER_ID:
        subject = f"New Message from {user.full_name} in {update.message.chat.title}"
        body = f"User: {user.full_name} (ID: {user.id})\nChat: {update.message.chat.title}\nMessage: {message_text}\nTime: {update.message.date}"
        await send_email(subject, body)
        logger.info(f"Email sent for message from user ID {user.id}")

# Rest of the original code (omitted for brevity, include from previous response)
# Include all other handlers: start, help, ban, kick, mute, unmute, welcome_new_member, create_poll, handle_poll_answer, error_handler

def main():
    # Initialize the application
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ban", ban))
    application.add_handler(CommandHandler("kick", kick))
    application.add_handler(CommandHandler("mute", mute))
    application.add_handler(CommandHandler("unmute", unmute))
    application.add_handler(CommandHandler("poll", create_poll))

    # Add message handler for reacting to text and emailing specific user's messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, react_to_message))

    # Add handler for welcoming new members
    application.add_handler(ChatMemberHandler(welcome_new_member, ChatMemberHandler.CHAT_MEMBER))

    # Add handler for poll answers
    application.add_handler(PollHandler(handle_poll_answer))

    # Add error handler
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
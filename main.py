import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    PollHandler,
    filters,
    ContextTypes,
)
from telegram.error import Forbidden
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ===== Load Environment =====
load_dotenv()  # Take environment variables from .env

# ===== Configuration =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    EMAIL_SENDER = os.getenv("EMAIL_SENDER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
    TARGET_USER_ID = int(os.getenv("TARGET_USER_ID"))  # Convert to integer

    @classmethod
    def validate(cls):
        """Check all required environment variables exist"""
        required_vars = [
            'BOT_TOKEN', 'EMAIL_SENDER',
            'EMAIL_PASSWORD', 'EMAIL_RECEIVER',
            'TARGET_USER_ID'
        ]
        missing = [var for var in required_vars if not getattr(cls, var)]
        if missing:
            raise EnvironmentError(f"Missing env vars: {', '.join(missing)}")

# Validate on startup
Config.validate()

# ===== Email Service =====
class EmailNotifier:
    @staticmethod
    async def send_alert(subject: str, body: str):
        """Thread-safe email sender"""
        try:
            msg = MIMEMultipart()
            msg['From'] = Config.EMAIL_SENDER
            msg['To'] = Config.EMAIL_RECEIVER
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(Config.EMAIL_SENDER, Config.EMAIL_PASSWORD)
                server.send_message(msg)
            logger.info("Email alert sent")
        except Exception as e:
            logger.error(f"Email failed: {str(e)}")

# ===== Bot Handlers =====
async def track_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Monitor specific user activity"""
    user = update.message.from_user
    if user.id == Config.TARGET_USER_ID:
        alert_msg = (
            f"🚨 Activity detected\n"
            f"User: {user.full_name} (ID: {user.id})\n"
            f"Chat: {update.effective_chat.title}\n"
            f"Message: {update.message.text}"
        )
        await EmailNotifier.send_alert("Telegram Alert", alert_msg)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Secure start handler"""
    await update.message.reply_text(
        "🔒 Monitoring bot active\n"
        f"Tracking user ID: {Config.TARGET_USER_ID}"
    )

# ===== Main Application =====
def setup_application() -> Application:
    """Factory for bot application"""
    app = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        track_target_user
    ))
    
    # Error handling
    app.add_error_handler(lambda u, c: logger.error(f"Error: {c.error}"))
    
    return app

if __name__ == "__main__":
    try:
        app = setup_application()
        logger.info("Starting bot in polling mode...")
        app.run_polling()
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
        raise
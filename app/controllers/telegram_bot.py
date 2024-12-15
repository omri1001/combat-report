# telegram_bot_main.py

import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from app.controllers.grades import collect_grades_telegram

# Import handlers and constants
from handlers import (
    start,
    input_text,
    collect_manager_name,
    collect_force_name,
    collect_location,
    collect_youtube_link,
    collect_poll_link,
    generate_report,
    cancel
)

from telegram_constants import (
    INPUT_TEXT,
    COLLECT_MANAGER_NAME,
    COLLECT_FORCE_NAME,
    COLLECT_LOCATION,
    COLLECT_GRADES,
    COLLECT_YOUTUBE_LINK,
    COLLECT_POLL_LINK,
    GENERATE_REPORT
)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    load_dotenv()
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables.")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            INPUT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_text)],
            COLLECT_MANAGER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_manager_name)],
            COLLECT_FORCE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_force_name)],
            COLLECT_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_location)],
            COLLECT_GRADES: [MessageHandler(filters.ALL & ~filters.COMMAND, collect_grades_telegram)],
            COLLECT_YOUTUBE_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_youtube_link)],
            COLLECT_POLL_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_poll_link)],
            GENERATE_REPORT: [MessageHandler(filters.ALL & ~filters.COMMAND, generate_report)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()

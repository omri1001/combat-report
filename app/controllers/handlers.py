# handlers.py

import json
import logging
import re
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from mongodb_utils import db
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

from app.controllers.gpt_integration import improve_text, parse_to_sections
from app.controllers.grades import collect_grades_telegram
from app.controllers.document_generator import generate_word_document

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ברוך הבא למייצר דוחות אימון של חברת DCA.\n אנא הכניסו טקסט בתבנית הבא:\n"
        "תקציר התרגיל הראשון בנקודות\n"
        "מה היה טוב בתרגיל הראשון\n"
        "איפה הכוח צריך להשתפר\n"
        "תקציר התרגיל השני בנקודות\n"
        "מה היה טוב בתרגיל השני\n"
        "איפה הכוח צריך להשתפר\n"
    )
    return INPUT_TEXT

async def input_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['raw_text'] = update.message.text
    await update.message.reply_text('אנא הכנס שם מנהל תרגיל:')
    return COLLECT_MANAGER_NAME

async def collect_manager_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['manager_name'] = update.message.text
    await update.message.reply_text('אנא הכנס שם הכוח המתאמן:')
    return COLLECT_FORCE_NAME

async def collect_force_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['force_name'] = update.message.text
    await update.message.reply_text('אנא הכנס את מיקום האימון:')
    return COLLECT_LOCATION

async def collect_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['location'] = update.message.text
    await update.message.reply_text('אנא שלח "המשך" כדי לעבור לציונים')
    return COLLECT_GRADES

async def collect_youtube_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    youtube_link = update.message.text.strip()
    if youtube_link.lower() != 'לא':
        context.user_data['youtube_link'] = youtube_link
    else:
        context.user_data['youtube_link'] = None
    await update.message.reply_text('אנא הכנס קישור לסקרים (או הקלד "לא" אם אין):')
    return COLLECT_POLL_LINK

async def collect_poll_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    poll_link = update.message.text.strip()
    if poll_link.lower() != 'לא':
        context.user_data['poll_link'] = poll_link
    else:
        context.user_data['poll_link'] = None

    await update.message.reply_text('מייצר את הדוח, אנא מתין...')
    return await generate_report(update, context)

async def generate_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Collect user input and metadata
    raw_text = context.user_data['raw_text']
    grades_data = context.user_data['grades_data']
    now = datetime.now()
    date_str = now.strftime('%d/%m/%Y')
    time_str = now.strftime('%H:%M:%S')

    manager_name = context.user_data.get('manager_name', "Training Manager")
    force_name = context.user_data.get('force_name', "Training Force")
    location = context.user_data.get('location', "Training Location")
    youtube_link = context.user_data.get('youtube_link', None)
    poll_link = context.user_data.get('poll_link', None)

    try:
        # Format the force name for a valid primary key
        cleaned_force_name = re.sub(r'\s+', '_', force_name.strip())
        primary_key = f"{date_str}_{cleaned_force_name}"

        # Enhance text using GPT and parse into sections
        enhanced_text = improve_text(raw_text, date_str, manager_name, force_name, location)
        sections = parse_to_sections(enhanced_text)

        # Prepare JSON data
        json_data = {
            "primary_key": primary_key,
            "date": date_str,
            "time": time_str,
            "force_name": force_name,
            "gpt_output": {
                "scenario_1": sections.get("Exercise 1", ""),
                "scenario_2": sections.get("Exercise 2", "")
            },
            "grades": grades_data,
            "poll_link": poll_link or "NONE",
            "youtube_link": youtube_link or "NONE"
        }

        # Log JSON data to console
        logger.info(f"Generated JSON: {json.dumps(json_data, indent=4, ensure_ascii=False)}")

        # Insert JSON data into MongoDB
        try:
            result = db["reports"].insert_one(json_data)
            json_data["_id"] = str(result.inserted_id)  # Convert ObjectId to string

            logger.info(f"Document inserted into MongoDB with _id: {result.inserted_id}")
        except Exception as e:
            logger.error(f"Error inserting into MongoDB: {e}")

        # Save Word report locally
        doc_output_path = "../resources/combat_report.docx"
        generate_word_document(
            sections,
            output_path=doc_output_path,
            date=date_str,
            signature=manager_name,
            title="Training Report",
            grades_data=grades_data,
            youtube_link=youtube_link,
            poll_link=poll_link
        )

        # Send Word report to user
        with open(doc_output_path, 'rb') as doc:
            await update.message.reply_document(doc)

        # Save JSON to file and send to user
        json_file_path = "../resources/data.json"
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

        with open(json_file_path, 'rb') as json_file:
            await update.message.reply_document(document=json_file)

        await update.message.reply_text('The report was generated and sent successfully. Thank you!')
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        await update.message.reply_text('An error occurred while generating the report. Please try again later.')

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('הפעולה בוטלה.')
    return ConversationHandler.END

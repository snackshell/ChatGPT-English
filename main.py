import logging 
import json
from telegram.request import HTTPXRequest
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from g4f.client import Client

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Predefined keyboard markups
START_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("Channel🌴", url='https://t.me/banacodes'),
        InlineKeyboardButton("Group🪺", url='https://t.me/banacodeschat')
    ],
    [
        InlineKeyboardButton("Developer🦭", url="https://t.me/snackshell"),
        InlineKeyboardButton("Help📃", callback_data="help")
    ]
])

HELP_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("Back to Menu 🏠", callback_data="start")]
])

# Help message constant
HELP_MESSAGE = """
🤖 Help Center

Welcome to the Banacodes Bot! Here's what you can do:

*Features*
• Easy communication in English.
• New memory: Remembers your previous messages for context.
• Follow-up corrections: You can correct or clarify your questions at any time.
• Inappropriate queries: The bot rejects inappropriate content.

*Response Time*
• Responses may vary; expect 3 to 30 seconds depending on the complexity of your question.

*Common Queries*
• Fun question: Ask for birthday party ideas for a 10-year-old! 🎉
• Programming help: You can ask how to make HTTP requests in JavaScript or get C++ code examples.
"""

# ChatGPT API integration
def get_chatgpt_response(user_message):
    try:
        client = Client()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}],
        )

        if isinstance(response, str):
            try:
                parsed_response = json.loads(response)
                if 'choices' in parsed_response and len(parsed_response['choices']) > 0:
                    return parsed_response['choices'][0]['message']['content']
            except json.JSONDecodeError:
                logger.error("Failed to parse response as JSON")
        
        elif hasattr(response, 'choices') and len(response.choices) > 0:
            return response.choices[0].message.content

        return "Sorry, I couldn't process the response properly."

    except Exception as e:
        logger.error(f"Error while communicating with ChatGPT API: {e}")
        return "Sorry, something went wrong while fetching the response."

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome! I'm an English chat bot. How can I help you today?",
        reply_markup=START_KEYBOARD
    )

# Help command handler
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        HELP_MESSAGE,
        reply_markup=HELP_KEYBOARD,
        parse_mode='Markdown'
    )

# Callback query handler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "help":
        await query.edit_message_text(
            text=HELP_MESSAGE,
            reply_markup=HELP_KEYBOARD,
            parse_mode='Markdown'
        )
    
    elif query.data == "start":
        await query.edit_message_text(
            text="Welcome! I'm an English chat bot. How can I help you today?",
            reply_markup=START_KEYBOARD
        )

# Message handler to process user messages
async def handle_message(update: Update, context) -> None:
    user_message = update.message.text
    logger.info(f"Received message: {user_message}")

    try:
        bot_response = get_chatgpt_response(user_message)
        if not bot_response:
            await update.message.reply_text("Sorry, I couldn't generate a response at the moment. Please try again later.")
            return

        await update.message.reply_text(bot_response)

    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        await update.message.reply_text("Sorry, an error occurred. Please try again later.")

# Error handler
async def error_handler(update: Update, context) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

# Main function to run the bot
if __name__ == '__main__':
    TELEGRAM_BOT_TOKEN = '7838545272:AAE2ia9j0nDhO_GljMI9Yxm8_qAlQbskRFI'

    request = HTTPXRequest(read_timeout=60, connect_timeout=60)
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).request(request).build()

    # Add handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    # Start polling
    app.run_polling()

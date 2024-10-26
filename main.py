import logging 
import json
from telegram.request import HTTPXRequest
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
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
🤖 *Help Center*

Welcome to the Banacodes Bot! Here's what you can do:

*Features:*
• Easy communication in English.
• New memory: Remembers your previous messages for context.
• Follow-up corrections: You can correct or clarify your questions at any time.
• Inappropriate queries: The bot rejects inappropriate content.

*Response Time:*
• Responses may vary; expect 3 to 30 seconds depending on the complexity of your question.

*Common Queries:*
• Fun question: Ask for birthday party ideas for a 10-year-old! 🎉
• Programming help: You can ask how to make HTTP requests in JavaScript or get C++ code examples.
"""

# Dictionary to store chat history
chat_history = {}

# ChatGPT API integration with memory
def get_chatgpt_response(user_message, chat_id):
    try:
        # Retrieve the chat history for the current chat
        history = chat_history.get(chat_id, [])
        
        # Add system message to handle markdown
        system_message = {
            "role": "system",
            "content": "When formatting responses, use markdown syntax. For titles and important points, use *bold* (asterisks) instead of **bold**. For example: *Important Title* instead of **Important Title**."
        }
        
        # Add the new user message to the history
        history.append({"role": "user", "content": user_message})
        
        # Include system message in the API call
        messages = [system_message] + history
        
        client = Client()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
        )

        if isinstance(response, str):
            try:
                parsed_response = json.loads(response)
                if 'choices' in parsed_response and len(parsed_response['choices']) > 0:
                    bot_message = parsed_response['choices'][0]['message']['content']
                    # Add the bot's response to the history
                    history.append({"role": "assistant", "content": bot_message})
                    # Update the chat history
                    chat_history[chat_id] = history
                    return bot_message
            except json.JSONDecodeError:
                logger.error("Failed to parse response as JSON")
        
        elif hasattr(response, 'choices') and len(response.choices) > 0:
            bot_message = response.choices[0].message.content
            # Add the bot's response to the history
            history.append({"role": "assistant", "content": bot_message})
            # Update the chat history
            chat_history[chat_id] = history
            return bot_message

        return "Sorry, I couldn't process the response properly."

    except Exception as e:
        logger.error(f"Error while communicating with ChatGPT API: {e}")
        return "Sorry, something went wrong while fetching the response."

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_first_name = update.effective_user.first_name
    await update.message.reply_text(
        f"*Hello there!* {user_first_name} 👋 I'm an AI assistant bot, powered by GPT-4. I'm here to answer your questions, discuss complex topics, and assist you in any field of knowledge.",
        reply_markup=START_KEYBOARD,
        parse_mode=ParseMode.MARKDOWN
    )

# Help command handler
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        HELP_MESSAGE,
        reply_markup=HELP_KEYBOARD,
        parse_mode=ParseMode.MARKDOWN
    )

# Callback query handler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "help":
        await query.edit_message_text(
            text=HELP_MESSAGE,
            reply_markup=HELP_KEYBOARD,
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif query.data == "start":
        await query.edit_message_text(
            text="*Welcome!* I'm an English chat bot. How can I help you today?",
            reply_markup=START_KEYBOARD,
            parse_mode=ParseMode.MARKDOWN
        )

# Message handler to process user messages with memory
async def handle_message(update: Update, context) -> None:
    user_message = update.message.text
    chat_id = update.message.chat_id
    logger.info(f"Received message: {user_message} from chat_id: {chat_id}")

    try:
        bot_response = get_chatgpt_response(user_message, chat_id)
        if not bot_response:
            await update.message.reply_text(
                "Sorry, I couldn't generate a response at the moment. Please try again later."
            )
            return
        
        creator_keywords = ["who made you", "who created you", "who is your creator", "who build you", "who's your dad"]
        if any(keyword in user_message.lower() for keyword in creator_keywords):
           creator_response = '"Paradox" made me to assist users like you! Join his channel @banacodes. If you need any help, you can ask my boss @snackshell'
           
           await update.message.reply_text(
            creator_response,
            parse_mode=ParseMode.MARKDOWN
        )
        return

        # Send the bot response with markdown enabled
        await update.message.reply_text(
            bot_response,
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred. Please try again later."
        )

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

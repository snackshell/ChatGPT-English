import logging 
import json
from telegram.request import HTTPXRequest
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from g4f.client import Client
from datetime import datetime, timedelta
import warnings
import nest_asyncio
nest_asyncio.apply()
warnings.filterwarnings("ignore", message="Failed to check g4f version")

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
async def get_chatgpt_response(user_message, chat_id):
    try:
        history = chat_history.get(chat_id, [])
        
        system_message = {
            "role": "system",
            "content": """You are a knowledgeable and helpful assistant with expertise across many fields including science, mathematics, programming, and general knowledge. You should confidently provide accurate information in all these areas.

When formatting your responses:
1. Always use *asterisks* for bold text in:
   - All numbered or bulleted titles/headings (e.g., "*1. Introduction:*", "*• Key Points:*")
   - Section headers (e.g., "*Examples:*", "*Note:*", "*Important:*")
   - Category names (e.g., "*Basic Syntax:*", "*Method 1:*")

2. For any code blocks, use triple backticks (```) to enclose the code.

3. For ALL formulas (mathematics, physics, chemistry, etc.):
   - Present each formula on its own line between triple backticks
   - Use simple characters (×, π, ², ³, ÷, Δ, °, ±)
   - For subscripts, write them normally (e.g., "v final" instead of "v₍final₎")

Example format for physics formulas:
"*1. Newton's Second Law:*
```
F = m × a
```

*2. Kinetic Energy:*
```
KE = (1/2) × m × v²
```

Remember to:
- Provide comprehensive answers across all academic subjects
- Include clear explanations with formulas
- Format all mathematical and scientific formulas using triple backticks
- Be confident in sharing knowledge from physics, chemistry, mathematics, and other fields"""
        }
        
        history.append({"role": "user", "content": user_message})
        messages = [system_message] + history
        
        client = Client()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        
        if response and hasattr(response, 'choices') and len(response.choices) > 0:
            bot_message = response.choices[0].message.content
            history.append({"role": "assistant", "content": bot_message})
            chat_history[chat_id] = history
            return bot_message
            
        return "Sorry, I couldn't generate a response. Please try again."

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
        await update.message.chat.send_action(action="typing")
        
        bot_response = await get_chatgpt_response(user_message, chat_id)
        if not bot_response:
            await update.message.reply_text(
                "Sorry, I couldn't generate a response at the moment. Please try again later."
            )
            return

        # Split long messages if they exceed Telegram's limit
        if len(bot_response) > 4096:
            chunks = [bot_response[i:i+4096] for i in range(0, len(bot_response), 4096)]
            for chunk in chunks:
                try:
                    await update.message.reply_text(
                        chunk,
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception:
                    # If markdown parsing fails, send without parsing
                    await update.message.reply_text(chunk)
        else:
            try:
                await update.message.reply_text(
                    bot_response,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                # If markdown parsing fails, send without parsing
                await update.message.reply_text(bot_response)

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
    TELEGRAM_BOT_TOKEN = 'BOT_TOKEN_FOM_BOT_FATHER'

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

import logging
import json
from telegram.request import HTTPXRequest
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from g4f.client import Client
from deep_translator import GoogleTranslator

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for Amharic responses keyed by message ID
response_storage = {}

# Function to translate text using Google Translate
def translate_text(text, source, target):
    try:
        translator = GoogleTranslator(source=source, target=target)
        return translator.translate(text)
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return None

# ChatGPT API integration
def get_chatgpt_response(user_message):
    try:
        client = Client()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}],
        )

        # Log the raw response for debugging
        logger.info(f"Raw API response: {response}")

        # Check if the response is a string (which might be JSON)
        if isinstance(response, str):
            try:
                # Attempt to parse the string as JSON
                parsed_response = json.loads(response)
                if 'choices' in parsed_response and len(parsed_response['choices']) > 0:
                    return parsed_response['choices'][0]['message']['content']
            except json.JSONDecodeError:
                logger.error("Failed to parse response as JSON")
        
        # If response is an object with 'choices' attribute
        elif hasattr(response, 'choices') and len(response.choices) > 0:
            return response.choices[0].message.content

        # If we reach here, the response format is unexpected
        logger.error(f"Unexpected response format: {response}")
        return "Sorry, I couldn't process the response properly."

    except Exception as e:
        # Log the exception for debugging purposes
        logger.error(f"Error while communicating with ChatGPT API: {e}")
        return "Sorry, something went wrong while fetching the response."

# Start command handler
async def start(update: Update, context) -> None:
    """Send a welcome message when the /start command is issued."""
    greeting_amharic = "እንኳን ደህና መጡ! እኔ የአማርኛ ቻት ቦት ነኝ። እንዴት ልረዳዎት እችላሁ?"
    await update.message.reply_text(f"{greeting_amharic}")

# Message handler to process user messages
async def handle_message(update: Update, context) -> None:
    """Handle the incoming messages."""
    user_message_amharic = update.message.text

    # Log the incoming message for debugging
    logger.info(f"Received message: {user_message_amharic}")

    try:
        # Step 1: Translate the user's Amharic message to English
        user_message_english = translate_text(user_message_amharic, 'am', 'en')
        if not user_message_english:
            await update.message.reply_text("ይቅርታ፣ መልእክትዎን መተርጎም አልቻልንም። እባክዎ እንደገና ይሞክሩ።")
            return

        logger.info(f"Translated to English: {user_message_english}")

        # Step 2: Get ChatGPT response in English
        bot_response_english = get_chatgpt_response(user_message_english)
        if not bot_response_english:
            await update.message.reply_text("ይቅርታ፣ አሁን መልስ መስጠት አልቻልንም። እባክዎ ቆይተው ይሞክሩ።")
            return

        logger.info(f"ChatGPT response: {bot_response_english}")

        # Step 3: Translate the ChatGPT response back to Amharic
        bot_response_amharic = translate_text(bot_response_english, 'en', 'am')
        if not bot_response_amharic:
            await update.message.reply_text("ይቅርታ፣ መልሳችንን መተርጎም አልቻልንም። እባክዎ ቆይተው ይሞክሩ።")
            return

        logger.info(f"Translated to Amharic: {bot_response_amharic}")

        # Step 4: Store both Amharic and English responses in memory
        message_id = update.message.message_id
        response_storage[message_id] = {
            'amharic': bot_response_amharic,
            'english': bot_response_english
        }

        # Step 5: Send the Amharic response with an inline button to translate
        keyboard = [
            [InlineKeyboardButton("Translate to English", callback_data=f"translate:{message_id}:en")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(bot_response_amharic, reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        await update.message.reply_text("ይቅርታ፣ ስህተት ተፈጥሯል። እባክዎ ቆይተው ይሞክሩ።")

# Callback handler for translating between Amharic and English
async def toggle_translation(update: Update, context) -> None:
    """Handle the callback when the translation button is pressed."""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    # Get the message ID and target language from the callback data
    _, message_id, target_lang = query.data.split(':')
    message_id = int(message_id)

    # Retrieve the stored responses
    stored_response = response_storage.get(message_id)
    if not stored_response:
        await query.edit_message_text("Sorry, the original message could not be found.")
        return

    if target_lang == 'en':
        # Translate to English
        translated_text = stored_response['english']
        new_button_text = "Translate to Amharic"
        new_callback_data = f"translate:{message_id}:am"
    else:
        # Translate to Amharic
        translated_text = stored_response['amharic']
        new_button_text = "Translate to English"
        new_callback_data = f"translate:{message_id}:en"

    # Update the message with the translated text and the new button
    keyboard = [[InlineKeyboardButton(new_button_text, callback_data=new_callback_data)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=translated_text, reply_markup=reply_markup)

# Error handler
async def error_handler(update: Update, context) -> None:
    """Log errors caused by Updates."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

# Main function to run the bot
if __name__ == '__main__':
    # Telegram bot token
    TELEGRAM_BOT_TOKEN = '7978726850:AAGfAD3b8hn4T4rawbTUTosct8HXfsVy6xA'

    # Custom timeout settings
    request = HTTPXRequest(
        read_timeout=60,  # Read timeout in seconds
        connect_timeout=60  # Connect timeout in seconds
    )

    # Create the application with custom request settings
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).request(request).build()

    # Command handler for /start
    app.add_handler(CommandHandler('start', start))

    # Message handler for all text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Callback query handler for the translation button
    app.add_handler(CallbackQueryHandler(toggle_translation, pattern="^translate"))

    # Error handler
    app.add_error_handler(error_handler)

    # Start polling to receive messages
    app.run_polling()

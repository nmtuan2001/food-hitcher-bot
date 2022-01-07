from dotenv import load_dotenv
import os
import logging
import telegram
# import telebot
# from telebot.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)
from googlemaps import Client as GoogleMaps
import os

from db import DBHelper
db = DBHelper()

load_dotenv(encoding='utf16')

TOKEN = os.getenv("TOKEN")
GMAPSAPI = os.getenv("GMAPSAPI")

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Create order states = /start ->  ORDER -> LOCATION -> RESTAURANT -> CAPACITY -> TIME -> CONFIRMATION (A)
# Join order states = /start -> LIST -> DETAILS -> CONFIRMATION (B)

# Create order states
START, PROCESS, ORDER, LOCATION, RESTAURANT, CAPACITY, TIME, CONFIRMATION, LISTS = range(9)

# Find order state

'''
reply_keyboard = [['Confirm', 'Restart']]
markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
'''
bot = telegram.Bot(token=TOKEN)
#chat_id = 'YOURTELEGRAMCHANNEL'
gmaps = GoogleMaps(GMAPSAPI)

PORT = int(os.environ.get('PORT', 5000))

def facts_to_str(user_data):
    facts = list()

    for key, value in user_data.items():
        facts.append('{} - {}'.format(key, value))

    return "\n".join(facts).join(['\n', '\n'])


def start(update, context):
    new_keyboard = [['Create new order', 'Join other orders']]
    new_markup = ReplyKeyboardMarkup(new_keyboard, resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_text(
        "Hi! I am your food hitching assistant to help you find others to order food with. ", reply_markup=new_markup)
    return LISTS

    # Todo -> Do if-else -> if create order, return ORDER; if join order, return LIST
'''
def process(update, context):
    user_data = context.user_data
    user = update.message.from_user
    update.message.reply_text("Thank you!", reply_markup=ReplyKeyboardRemove())
'''
def db_list(update, context): # if join order, list out the nearby orders
    user_data = context.user_data
    user = update.message.from_user
    update.message.reply_text("Thank you!", reply_markup=ReplyKeyboardRemove())
    update.message.reply_text('You have succeeded in solving the bug!')
    return ConversationHandler.END



def order_menu(update, context): # -> LOCATION
    update.message.reply_text('You can create your own order. To start, please type the location you would like to deliver to.')

    return LOCATION

def location(update, context): # -> RESTAURANT
    user = update.message.from_user
    user_data = context.user_data
    category = 'Location'
    text = update.message.text
    user_data[category] = text
    logger.info("Location of %s: %s", user.first_name, update.message.text)

    update.message.reply_text('What is the restaurant you are ordering from?')
    return RESTAURANT

def restaurant(update, context): # -> CAPACITY
    user = update.message.from_user
    user_data = context.user_data
    category = 'Restaurant'
    text = update.message.text
    user_data[category] = text
    logger.info("Name of restaurant: %s", update.message.text)
    update.message.reply_text('What is the maximum number of people you want to order with?')

    return CAPACITY

def capacity(update, context): # -> TIME
    user = update.message.from_user
    user_data = context.user_data
    category = 'Number of People'
    text = update.message.text
    user_data[category] = text
    logger.info("Number of people: %s", update.message.text)
    update.message.reply_text('What time do you want the food to be ordered by?')

    return TIME
    
def time(update, context): # -> CONFIRMATION
    reply_keyboard = [['Confirm', 'Restart']]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    user = update.message.from_user
    user_data = context.user_data
    category = 'Cutoff Time'
    text = update.message.text
    user_data[category] = text
    logger.info("Time to join the order by: %s", update.message.text)
    update.message.reply_text("Thank you for ordering with us! Please check the information is correct:"
                                "{}".format(facts_to_str(user_data)), reply_markup=markup)

    return CONFIRMATION

def confirmation(update, context): # -> END
    user_data = context.user_data
    user = update.message.from_user
    

    update.message.reply_text("Thank you!", reply_markup=ReplyKeyboardRemove())

    """
    update.message.reply_text("Thank you! I will post the information on the channel @" + chat_id + "  now.", reply_markup=ReplyKeyboardRemove())
    if (user_data['Photo Provided'] == 'Yes'):
        del user_data['Photo Provided']
        bot.send_photo(chat_id=chat_id, photo=open('user_photo.jpg', 'rb'), 
		caption="<b>Food is Available!</b> Check the details below: \n {}".format(facts_to_str(user_data)) +
		"\n For more information, message the poster {}".format(user.name), parse_mode=telegram.ParseMode.HTML)
    else:
        del user_data['Photo Provided']
        bot.sendMessage(chat_id=chat_id, 
            text="<b>Food is Available!</b> Check the details below: \n {}".format(facts_to_str(user_data)) +
        "\n For more information, message the poster {}".format(user.name), parse_mode=telegram.ParseMode.HTML)
    """
############## NEW ITEM ##################################################################################################
    db.add_item(user_data['Location'], user_data['Restaurant'], user_data['Number of People'], user_data['Cutoff Time']) #
##########################################################################################################################
    
    geocode_result = gmaps.geocode(user_data['Location'])
    lat = geocode_result[0]['geometry']['location'] ['lat']
    lng = geocode_result[0]['geometry']['location']['lng']
    bot.send_location(chat_id=update.message.chat.id, latitude=lat, longitude=lng)

    return ConversationHandler.END

def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye! Hope to see you again next time.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(update, context):
    """Log errors caused by updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary

### New Item ##
    db.setup()#
###############
    
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Create order states = /start -> ORDER -> LOCATION -> RESTAURANT -> CAPACITY -> TIME -> CONFIRMATION
    # Join order states = /start -> LIST -> DETAILS -> CONFIRMATION 

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            START: [CommandHandler('start', start), MessageHandler(Filters.text, start)],

            PROCESS: [MessageHandler(Filters.regex('^Create new order$'),
                                      order_menu),
            MessageHandler(Filters.regex('^Join other orders$'),
                                      db_list)],
                                      

            LISTS: [MessageHandler(Filters.regex('^Join other orders$'), db_list),
                                      MessageHandler(Filters.regex('^Create new order$'),
                                      order_menu)
            ],

            ORDER: [CommandHandler('start', start), MessageHandler(Filters.text, order_menu)],

            LOCATION: [CommandHandler('start', start), MessageHandler(Filters.text, location)],

            RESTAURANT: [CommandHandler('start', start), MessageHandler(Filters.text, restaurant)],

            CAPACITY: [CommandHandler('start', start), MessageHandler(Filters.text, capacity)],

            TIME: [CommandHandler('start', start), MessageHandler(Filters.text, time)],

            CONFIRMATION: [MessageHandler(Filters.regex('^Confirm$'),
                                      confirmation),
            MessageHandler(Filters.regex('^Restart$'),
                                      start)
                       ]

        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    #updater.start_webhook(listen="0.0.0.0", port=int(PORT), url_path=TOKEN)
    #updater.bot.setWebhook('https://YOURHEROKUAPPNAME.herokuapp.com/' + TOKEN)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    #updater.idle()
    updater.start_polling()



if __name__ == '__main__':
    main()

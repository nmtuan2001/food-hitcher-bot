from dotenv import load_dotenv
import os
import logging
import telegram
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
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
START, JOIN, ORDER, LOCATION, RESTAURANT, CAPACITY, TIME, CONFIRMATION, LISTS, COMPLETE, DELETE = range(11)

# Find order state

bot = telegram.Bot(token=TOKEN)
gmaps = GoogleMaps(GMAPSAPI)

PORT = int(os.environ.get('PORT', 5000))

def facts_to_str(user, user_data):
    facts = list()
    facts.append('{} - {}'.format("Telegram Handle", "@" + str(user['username'])))
    for key, value in user_data.items():
        facts.append('{} - {}'.format(key, value))

    return "\n".join(facts).join(['\n', '\n'])


def start(update, context):
    new_keyboard = [['Create new order', 'Join other orders']]
    new_markup = ReplyKeyboardMarkup(new_keyboard, resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_text(
        "Hi! I am your food hitching assistant to help you find others to order food with. ", reply_markup=new_markup)
    return JOIN


def join(update, context): # if join order, list out the nearby orders
    update.message.reply_text("Can you give us your location?", reply_markup=ReplyKeyboardRemove())    
    return LISTS

def lists(update, context):
    geocode_result = gmaps.geocode(update.message.text)
    lat = geocode_result[0]['geometry']['location']['lat']
    lng = geocode_result[0]['geometry']['location']['lng']

    places = 'These are the orders that are closest to you. \n'
    
    time = update.message.date
    gmt_time = time.strftime("%H:%M")
    
    closest = db.closest_items(lat, lng, gmt_time)

    for dist, user_id, username, location, lng, lat, restaurant, time, curr, full in closest:
        facts = list()
        facts.append('{} - {}'.format("Telegram Handle", "@" + str(username)))
        facts.append('{} - {}'.format("Location ", location))
        facts.append('{} - {}'.format("Restaurant ", str(restaurant)))
        facts.append('{} - {}'.format("Time ", time))
        facts.append('{} - {}'.format("Distance ", "{:.2f}".format(dist) + " km"))

        places += "\n".join(facts).join(['\n', '\n'])
        places += "\n"

    update.message.reply_text(places)

    return ConversationHandler.END


def order(update, context): # -> LOCATION
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
    update.message.reply_text('What time do you want the food to be ordered by? Please input in HH:MM format (24 hours).')

    return TIME
    
def time(update, context): # -> CONFIRMATION
    reply_keyboard = [['Confirm', 'Restart']]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    user = update.message.from_user
    user_data = context.user_data
    category = 'Cutoff Time'
    text = update.message.text

    if len(text) != 5 or text[2] != ":":
        update.message.reply_text("Please input the time as instructed.")
        return TIME
    else:
        user_data[category] = text
        logger.info("Time to join the order by: %s", update.message.text)
        update.message.reply_text("Thank you for ordering with us! Please check the information is correct:"
                                    "{}".format(facts_to_str(user, user_data)), reply_markup=markup)
        return CONFIRMATION

def confirmation(update, context): # -> END
    user_data = context.user_data
    user = update.message.from_user
    
    geocode_result = gmaps.geocode(user_data['Location'])

    '''
    if db.search_user(user['id']):
        update.message.reply_text("ERROR. You have already started an order.", reply_markup=ReplyKeyboardRemove())
    '''

    if len(geocode_result) == 0:
        update.message.reply_text("Location not found. Please try again.", reply_markup=ReplyKeyboardRemove())
    else:
        lat = geocode_result[0]['geometry']['location']['lat']
        lng = geocode_result[0]['geometry']['location']['lng']
    
        db.add_item(user['id'], user['username'], user_data['Location'], lat, lng, user_data['Restaurant'], user_data['Cutoff Time'], 1, user_data['Number of People'])
        bot.send_location(chat_id=update.message.chat.id, latitude=lat, longitude=lng)
        update.message.reply_text("Thank you!", reply_markup=ReplyKeyboardRemove())
        
        final_keyboard = [['Order Completed', 'Delete Order']]
        final_markup = ReplyKeyboardMarkup(final_keyboard, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text(
            "Please update us once the food has been ordered. If you decide not to order, please delete your order. ", reply_markup=final_markup)

        return COMPLETE

def complete(update, context):
    user_data = context.user_data
    user = update.message.from_user
    db.delete_item(user['id'])
    update.message.reply_text("Thank you! Hope you have a good meal! :)", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def delete(update, context):
    user_data = context.user_data
    user = update.message.from_user
    db.delete_item(user['id'])
    update.message.reply_text("Type /start if you wish to restart the order. ", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s cancelled the conversation.", user.first_name)
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

    db.setup()
    
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

            JOIN: [MessageHandler(Filters.regex('^Join other orders$'), join),
                                      MessageHandler(Filters.regex('^Create new order$'),
                                      order)
            ],

            ORDER: [CommandHandler('start', start), MessageHandler(Filters.text, order)],

            LOCATION: [CommandHandler('start', start), MessageHandler(Filters.text, location)],

            RESTAURANT: [CommandHandler('start', start), MessageHandler(Filters.text, restaurant)],

            CAPACITY: [CommandHandler('start', start), MessageHandler(Filters.text, capacity)],

            TIME: [CommandHandler('start', start), MessageHandler(Filters.text, time)],

            CONFIRMATION: [MessageHandler(Filters.regex('^Confirm$'),
                                      confirmation),
            MessageHandler(Filters.regex('^Restart$'),
                                      start)
                       ],

            COMPLETE:[MessageHandler(Filters.regex('^Order Completed$'),
                                      complete),
            MessageHandler(Filters.regex('^Delete Order$'),
                                      delete)
                       ],

            DELETE: [CommandHandler('start', start), MessageHandler(Filters.text, delete)],
            
            LISTS: [CommandHandler('start', start), MessageHandler(Filters.text, lists)]

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
    updater.idle()

if __name__ == '__main__':
    main()
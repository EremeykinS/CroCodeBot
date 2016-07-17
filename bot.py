from config import *
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import telegram
import logging
import sqlite3

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger('Crocodebot.' + __name__)

# States are saved in a dict that maps chat_id -> state
state = dict()
# dict in dict
dd = dict()

# Keyboards
main_kbd = telegram.ReplyKeyboardMarkup([['Заказать бота', 'Мои заказы'], ['Статус заказа', 'INFO']])
zakaz_kbd = telegram.ReplyKeyboardMarkup([['О заказе', 'Изменить заказ'], ['Отменить заказ', 'Главное меню']])
yes_no_kbd = telegram.ReplyKeyboardMarkup([['Да'], ['Нет']])
change_kbd = telegram.ReplyKeyboardMarkup([['Все верно', 'Изменить имя'], ['Изменить описание', 'Изменить дату']])
empty_kbd = telegram.ReplyKeyboardHide()
glavnoe_kbd = telegram.ReplyKeyboardMarkup([['Главное меню']],resize_keyboard=True)

MAIN_MENU, MEETING, ZAKAZ, STATUS, BOT_NAME, IDEA, MY_ZAKAZ, CHOOSE, ABOUT, CHANGE, BOT_NAME_CHANGE, IDEA_CHANGE, DATE_CHANGE = range(13)

def db_transaction(db, q):
    cursor = db.cursor()
    cursor.execute(q)
    db.commit()
    result = cursor.fetchall()
    return result

def start(bot, update):
    user_id = update.message.from_user.id
    db = sqlite3.connect(db_name)
    sql_result = db_transaction(db, 'SELECT user_name FROM info WHERE uid=' + str(user_id))
    if user_id not in dd:
        dd[user_id] = dict()
    if not sql_result:
        text = "Приветствую Вас от лица компании Crocode! Я помогу Вам заказать бота, а также проверить статус уже сделанных заказов. Скажите, как я могу к Вам обращаться?"
        state[user_id] = MEETING
        bot.sendMessage(update.message.chat_id, text=text, parse_mode="HTML")
    else:
        user_name = sql_result[0][0]
        dd[user_id]['user_name'] = user_name
        text = dd[user_id]['user_name'] + ", сделайте новый заказ или посмотрите информацию об уже сделанных заказах"
        state[user_id] = MAIN_MENU
        bot.sendMessage(update.message.chat_id, text=text, reply_markup=main_kbd, parse_mode="HTML")
    
def helper(bot, update):
    bot.sendMessage(update.message.chat_id, text='Help!')


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def chat(bot, update):
    user_id = update.message.from_user.id
    answer = update.message.text
    chat_state = state.get(user_id)
    db = sqlite3.connect(db_name)
    if user_id not in dd:
        dd[user_id] = dict()
    if chat_state != MEETING:
        sql_result = db_transaction(db, 'SELECT user_name FROM info WHERE uid=' + str(user_id))
        user_name = sql_result[0]
        if 'user_name' not in dd[user_id]:
            dd[user_id]['user_name'] = user_name[0]
    
    if answer == 'Главное меню':
        state[user_id] = MAIN_MENU
        text = dd[user_id]['user_name'] + ", сделайте новый заказ или посмотрите информацию об уже сделанных заказах"
        bot.sendMessage(user_id, text=text, reply_markup=main_kbd, parse_mode="HTML")
        for key in ('bot_name', 'idea', 'date', 'status'):
            if key in dd[user_id]:
                del dd[user_id][key]
    elif answer == 'О заказе':
        sql_result = db_transaction(db, 'SELECT idea,date,status FROM zakaz WHERE (uid= "' + str(user_id) + '" AND bot_name = "' + dd[user_id]['bot_name'] + '")')
        dd[user_id]['idea'],dd[user_id]['date'],dd[user_id]['status'] = sql_result[0]
        state[user_id] = ABOUT
        text = telegram.Emoji.BOY + " <b>Название бота:</b> " + dd[user_id]['bot_name'] + "\n" + telegram.Emoji.ELECTRIC_LIGHT_BULB + " <b>Основная идея бота:</b> " + dd[user_id]['idea'] + "\n" + telegram.Emoji.CALENDAR + " <b>Дата запуска:</b> " + dd[user_id]['date'] + "\n" + telegram.Emoji.PUBLIC_ADDRESS_LOUDSPEAKER + " <b>Статус заказа:</b> " + dd[user_id]['status']    
        bot.sendMessage(user_id, text=text, reply_markup=zakaz_kbd, parse_mode="HTML")
    elif answer == 'Изменить заказ':
        sql_result = db_transaction(db, 'SELECT idea,date,status FROM zakaz WHERE (uid= "' + str(user_id) + '" AND bot_name = "' + dd[user_id]['bot_name'] + '")')
        dd[user_id]['idea'],dd[user_id]['date'],dd[user_id]['status'] = sql_result[0]
        db_transaction(db, 'DELETE FROM zakaz WHERE (uid= "' + str(user_id) + '" AND bot_name = "' + dd[user_id]['bot_name'] + '")')
        state[user_id] = CHANGE
        text = dd[user_id]['user_name'] + " ,на данный момент полученный нами заказ выглядит следующим образом \n\n" + telegram.Emoji.BOY + " <b>Название бота:</b> " + dd[user_id]['bot_name'] + "\n" + telegram.Emoji.ELECTRIC_LIGHT_BULB + " <b>Основная идея бота:</b> " + dd[user_id]['idea'] + "\n" + telegram.Emoji.CALENDAR + " <b>Дата запуска:</b> " + dd[user_id]['date'] + "\n" + telegram.Emoji.PUBLIC_ADDRESS_LOUDSPEAKER + " <b>Статус заказа:</b> " + dd[user_id]['status'] + "\n\nНужно ли что-нибудь изменить?"
        bot.sendMessage(user_id, text=text, reply_markup=change_kbd, parse_mode="HTML")
    elif answer == 'Отменить заказ':
        db_transaction(db, 'DELETE FROM zakaz WHERE (uid= "' + str(user_id) + '" AND bot_name = "' + dd[user_id]['bot_name'] + '")')
        state[user_id] = MAIN_MENU
        text = dd[user_id]['user_name'] + ", Ваш заказ был успешно отменен! Вы можете сделать новый заказ"
        bot.sendMessage(user_id, text=text, reply_markup=main_kbd, parse_mode="HTML")
        for key in ('bot_name', 'idea', 'date', 'status'):
            if key in dd[user_id]:
                del dd[user_id][key]
    elif answer == 'Заказать бота':
        state[user_id] = ZAKAZ
        text = dd[user_id]['user_name'] + ", придумайте название для Вашего бота"
        bot.sendMessage(user_id, text=text, reply_markup=glavnoe_kbd, parse_mode="HTML")
    elif answer == 'Мои заказы':
        zakazy = db_transaction(db, 'SELECT bot_name FROM zakaz WHERE uid=' + str(user_id))
        if zakazy:
            state[user_id] = MY_ZAKAZ
            text = dd[user_id]['user_name'] + ", пожалуйста, выберите заказ"
            status_kbd = telegram.ReplyKeyboardMarkup([[zakaz[0]] for zakaz in zakazy],resize_keyboard=True)
            bot.sendMessage(user_id, text=text, reply_markup=status_kbd, parse_mode="HTML")
        else:
            state[user_id] = MAIN_MENU
            text = dd[user_id]['user_name'] + ", Вы пока еще не делали заказов - это можно легко исправить, нажав кнопку <b>Заказать бота</b>"
            status_kbd = telegram.ReplyKeyboardMarkup([[zakaz[0]] for zakaz in zakazy],resize_keyboard=True)
            bot.sendMessage(user_id, text=text, reply_markup=status_kbd, parse_mode="HTML")
    elif answer == 'Статус заказа':
        zakazy = db_transaction(db, 'SELECT bot_name FROM zakaz WHERE uid=' + str(user_id))
        if zakazy:
            state[user_id] = STATUS
            text = dd[user_id]['user_name'] + ", пожалуйста, выберите заказ"
            status_kbd = telegram.ReplyKeyboardMarkup([[zakaz[0]] for zakaz in zakazy],resize_keyboard=True)
            bot.sendMessage(user_id, text=text, reply_markup=status_kbd, parse_mode="HTML")
        else:
            state[user_id] = MAIN_MENU
            text = dd[user_id]['user_name'] + ", Вы пока еще не делали заказов - это можно легко исправить, нажав кнопку <b>Заказать бота</b>"
            status_kbd = telegram.ReplyKeyboardMarkup([[zakaz[0]] for zakaz in zakazy],resize_keyboard=True)
            bot.sendMessage(user_id, text=text, reply_markup=status_kbd, parse_mode="HTML")
    elif answer == 'INFO':
        text = "Появление информации ожидается в скором времени"
        bot.sendMessage(user_id, text=text, reply_markup=main_kbd, parse_mode="HTML")
    elif chat_state == MEETING:
        text = "Отлично, " + answer + ", теперь Вы можете сделать заказ, нажав кнопку Заказать бота."
        state[user_id] = MAIN_MENU
        dd[user_id]['user_name'] = answer
        bot.sendMessage(update.message.chat_id, text=text, reply_markup=main_kbd, parse_mode="HTML")
    elif chat_state == STATUS:
        status = db_transaction(db, 'SELECT status FROM zakaz WHERE (uid= "' + str(user_id) + '" AND bot_name = "' + str(answer) + '")')
        text = dd[user_id]['user_name'] + ", статус Вашего заказа: \n" + "<b>"+ status[0][0] + "</b>"
        bot.sendMessage(user_id, text=text, reply_markup=main_kbd, parse_mode="HTML")
    elif chat_state == ZAKAZ:
        text = dd[user_id]['user_name'] + ", теперь в нескольких словах опишите идею Вашего бота"
        state[user_id] = BOT_NAME
        dd[user_id]['bot_name'] = answer
        bot.sendMessage(update.message.chat_id, text=text, reply_markup=glavnoe_kbd, parse_mode="HTML")
    elif chat_state == BOT_NAME:
        text = dd[user_id]['user_name'] + ", для завершения оформления заказа введите примерную дату запуска бота в формате <i>ДД.ММ.ГГГГ</i> (например, 26.10.2016)"
        state[user_id] = IDEA
        dd[user_id]['idea'] = answer
        bot.sendMessage(update.message.chat_id, text=text, reply_markup=glavnoe_kbd, parse_mode="HTML")
    elif chat_state == IDEA:
        dd[user_id]['date'] = answer
        dd[user_id]['status'] = "Заказ отправлен на рассмотрение"
        text = dd[user_id]['user_name'] + " ,пожалуйста, проверьте правильность составленного заказа \n\n" + telegram.Emoji.BOY + " <b>Название бота:</b> " + dd[user_id]['bot_name'] + "\n" + telegram.Emoji.ELECTRIC_LIGHT_BULB + " <b>Основная идея бота:</b> " + dd[user_id]['idea'] + "\n" + telegram.Emoji.CALENDAR + " <b>Дата запуска:</b> " + dd[user_id]['date'] + "\n" + telegram.Emoji.PUBLIC_ADDRESS_LOUDSPEAKER + " <b>Статус заказа:</b> " + dd[user_id]['status'] + "\n\nВсе верно?"
        state[user_id] = CHANGE
        bot.sendMessage(update.message.chat_id, text=text, reply_markup=change_kbd, parse_mode="HTML")
    elif chat_state == CHANGE:
        if answer == 'Все верно':
            text = dd[user_id]['user_name'] + ", мы получили Ваш заказ! В ближайшее время мы свяжемся с Вами!"
            state[user_id] = MAIN_MENU
            bot.sendMessage(user_id, text=text, reply_markup=main_kbd, parse_mode="HTML")
            db_transaction(db, 'INSERT INTO zakaz (uid, bot_name,idea,date,status) VALUES ("' + str(user_id) + '", "' + dd[user_id]['bot_name'] + '","' + dd[user_id]['idea'] + '","' + dd[user_id]['date'] + '","' + "Заказ отправлен на рассмотрение" + '")')
            del dd[user_id]
        elif answer == "Изменить имя":
            del dd[user_id]['bot_name']
            text = dd[user_id]['user_name'] + ', попробуйте ввести название бота еще раз.'
            state[user_id] = BOT_NAME_CHANGE
            bot.sendMessage(user_id, text=text, reply_markup=glavnoe_kbd, parse_mode="HTML")
        elif answer == "Изменить описание":
            del dd[user_id]['idea']
            text = dd[user_id]['user_name'] + ', попробуйте ввести описание бота еще раз.'
            state[user_id] = IDEA_CHANGE
            bot.sendMessage(user_id, text=text, reply_markup=glavnoe_kbd, parse_mode="HTML")
        elif answer == "Изменить дату":
            del dd[user_id]['date']
            text = dd[user_id]['user_name'] + ', попробуйте ввести дату еще раз в формате <i>ДД.ММ.ГГГГ</i> (например, 26.10.2016).'
            state[user_id] = DATE_CHANGE
            bot.sendMessage(user_id, text=text, reply_markup=glavnoe_kbd, parse_mode="HTML")
    elif chat_state == BOT_NAME_CHANGE:
        dd[user_id]['bot_name'] = answer
        text = dd[user_id]['user_name'] + " ,пожалуйста, проверьте правильность составленного заказа \n\n" + telegram.Emoji.BOY + " <b>Название бота:</b> " + dd[user_id]['bot_name'] + "\n" + telegram.Emoji.ELECTRIC_LIGHT_BULB + " <b>Основная идея бота:</b> " + dd[user_id]['idea'] + "\n" + telegram.Emoji.CALENDAR + " <b>Дата запуска:</b> " + dd[user_id]['date'] + "\n" + telegram.Emoji.PUBLIC_ADDRESS_LOUDSPEAKER + " <b>Статус заказа:</b> " + dd[user_id]['status'] + "\n\nВсе верно?"
        state[user_id] = CHANGE
        bot.sendMessage(update.message.chat_id, text=text, reply_markup=change_kbd, parse_mode="HTML")
    elif chat_state == IDEA_CHANGE:
        dd[user_id]['idea'] = answer
        text = dd[user_id]['user_name'] + " ,пожалуйста, проверьте правильность составленного заказа \n\n" + telegram.Emoji.BOY + " <b>Название бота:</b> " + dd[user_id]['bot_name'] + "\n" + telegram.Emoji.ELECTRIC_LIGHT_BULB + " <b>Основная идея бота:</b> " + dd[user_id]['idea'] + "\n" + telegram.Emoji.CALENDAR + " <b>Дата запуска:</b> " + dd[user_id]['date'] + "\n" + telegram.Emoji.PUBLIC_ADDRESS_LOUDSPEAKER + " <b>Статус заказа:</b> " + dd[user_id]['status'] + "\n\nВсе верно?"
        state[user_id] = CHANGE
        bot.sendMessage(update.message.chat_id, text=text, reply_markup=change_kbd, parse_mode="HTML")
    elif chat_state == DATE_CHANGE:
        dd[user_id]['date'] = answer
        text = dd[user_id]['user_name'] + " ,пожалуйста, проверьте правильность составленного заказа \n\n" + telegram.Emoji.BOY + " <b>Название бота:</b> " + dd[user_id]['bot_name'] + "\n" + telegram.Emoji.ELECTRIC_LIGHT_BULB + " <b>Основная идея бота:</b> " + dd[user_id]['idea'] + "\n" + telegram.Emoji.CALENDAR + " <b>Дата запуска:</b> " + dd[user_id]['date'] + "\n" + telegram.Emoji.PUBLIC_ADDRESS_LOUDSPEAKER + " <b>Статус заказа:</b> " + dd[user_id]['status'] + "\n\nВсе верно?"
        state[user_id] = CHANGE
        bot.sendMessage(update.message.chat_id, text=text, reply_markup=change_kbd, parse_mode="HTML")
    elif chat_state == MY_ZAKAZ:
        state[user_id] = CHOOSE
        dd[user_id]['bot_name'] = answer
        text = "Вы можете узнать детали вашего заказа, изменить заказ или отменить его"
        bot.sendMessage(user_id, text=text, reply_markup=zakaz_kbd, parse_mode="HTML")
   
        

def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(telegram_token)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helper))

    # on noncommand i.e message
    dp.add_handler(MessageHandler([Filters.text], chat))

    # inline keyboard handler
    #dp.add_handler(telegram.ext.CallbackQueryHandler(scroll))
    # TODO: update messages with time information

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_webhook(listen='95.163.114.6',
                      port=88,
                      url_path='CroCodeBot',
                      key='/home/user/cert/private.key',
                      cert='/home/user/cert/cert.pem',
                      webhook_url='https://95.163.114.6:88/CroCodeBot')
    updater.idle()


if __name__ == '__main__':
    main()
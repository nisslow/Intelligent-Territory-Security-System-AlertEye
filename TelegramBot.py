import telebot
#import AlertEye  is not necessary while using 'MultiCameras'!

bot = telebot.TeleBot(tg_bot_token)
is_running = True

def send_new_photos(photo):
    try:
        with open(photo, 'rb') as photo_file:
            bot.send_photo(chat_id=tg_bot_chatID_me, photo=photo_file)
    except Exception as e:
        print(f"Возникла ошибка при отправке фото: {e}")


def system_is_on_message():
    bot.send_message(chat_id=tg_bot_chatID_me, text='Система слежения включена', disable_notification=True)


def system_is_of_message():
    bot.send_message(chat_id=tg_bot_chatID_me, text='Система слежения отключена', disable_notification=True)


def start_telebot():
        from datetime import time
        try:
            bot.polling() 
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

# Thus function is not necessary while using 'MultiCameras'!
@bot.message_handler(commands=['stop'])
def stop_telebot_from_telegram():
    AlertEye.stop_processes()
    global is_running
    is_running = False
    bot.stop_polling()
    print('Система слежения выключена с Telegram')

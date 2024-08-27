import telebot

import AlertEye
# from AlertEye import stop_processes
from Config import tg_bot_token, tg_bot_chatID_me, tg_bot_chatID_group

bot = telebot.TeleBot(tg_bot_token)
is_running = True


#
# @bot.message_handler(func=lambda message: True)
# def echo_message(message):
#     bot.reply_to(message, message.text)


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
    # while True:
        from datetime import time
        try:
            bot.polling()  # Увеличиваем время ожидания до 60 секунд

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            # time.sleep(5)  # Ожидаем 5 секунд перед повторной попыткой


def stop_telebot():
    global is_running
    is_running = False
    bot.stop_polling()


@bot.message_handler(commands=['stop'])
def stop_telebot_from_telegram():
    AlertEye.stop_processes()
    global is_running
    is_running = False
    bot.stop_polling()
    print('Система слежения выключена с Telegram')


# @bot.message_handler(commands=['start'])
# def start_fromTG(message):
#     if not is_running:
#         vision_thread = Thread(target=Vision.vision, args=(
#             data.get("stream_url"), data.get("width"), data.get("height"),
#             data.get("model_path"), data.get("img_size"), data.get("photos_dir")
#             ,data.get("videos_dir"),data.get("app")), daemon=True)
#         vision_thread.start()
#
#         print('Система слежения включена с Telegram')
#     else:
#         print('Система слежения уже включена')


# if __name__ == "__main__":
#     start_telebot()

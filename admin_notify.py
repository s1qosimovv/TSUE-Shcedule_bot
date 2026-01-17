ADMIN_CHAT_ID = 7684282603  # O'Z TELEGRAM IDING

def notify(bot, text):
    try:
        bot.send_message(ADMIN_CHAT_ID, text)
    except:
        pass

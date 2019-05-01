from cbot import CBot


try:
    bot = CBot("chatterbot")

    while not bot.bot_quit():
        bot.get_input()
        bot.respond()

except Exception as e:
    print(str(e))

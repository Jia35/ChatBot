from cbot import ChatBot


try:
    bot = ChatBot("Chatterbot15")

    bot.signon()
    while not bot.bot_quit():
        bot.get_input()
        bot.respond()
    
    bot.save_unknown_input()

except Exception as e:
    print("Error: " + str(e))

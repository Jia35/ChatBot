from cbot import CBot


try:
    bot = CBot("Chatterbot15")

    bot.signon()
    while not bot.bot_quit():
        bot.get_input()
        bot.save_log("USER")
        bot.respond()
    
    bot.save_unknown_input()

except Exception as e:
    print("Error: " + str(e))

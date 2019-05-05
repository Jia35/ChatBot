from cbot import ChatBot


try:
    bot = ChatBot("Chatbot")

    bot.signon()
    while not bot.bot_quit():
        bot.get_input()
        bot.respond()
        if bot.action == "location":
            print(bot.subject.strip())
    
    bot.save_unknown_input()

except Exception as e:
    print("Error: " + str(e))

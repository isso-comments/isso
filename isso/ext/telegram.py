from telegram.ext import CommandHandler, Updater
import atexit

from isso import local

class TelegramBot:
    def __init__(self, conf):
        api_token = conf.get("telegram", "token")
        self.updater = Updater(token=api_token, use_context=True)
        self.subscribers = []

        self.setup_commands()

        atexit.register(lambda: self.teardown())
        self.updater.start_polling()

    def __iter__(self):
        yield "comments.new:finish", self._new_comment

    def _new_comment(self, thread, comment):
        template =\
"""New comment!
{} wrote:

{}

Link to comment: {}"""
        message = template.format(
                comment['author'] or "Anonymous",
                comment['text'],
                local("origin") + thread["uri"] + "#isso-%i" % comment["id"])
        for s in self.subscribers:
            self.updater.bot.send_message(s, text=message)

    def setup_commands(self):
        start_handler = CommandHandler('start', lambda update, context: self.handle_start(update, context))
        self.updater.dispatcher.add_handler(start_handler)
        stop_handler = CommandHandler('stop', lambda update, context: self.handle_stop(update, context))
        self.updater.dispatcher.add_handler(stop_handler)
        help_handler = CommandHandler('help', lambda update, context: self.handle__help(update, context))
        self.updater.dispatcher.add_handler(help_handler)

    def teardown(self):
        for s in self.subscribers:
            self.updater.bot.send_message(s, text="Warning! I'm going offline. Please try to '/start' me again later.")
        self.updater.stop()

    def handle_start(self, update, context):
        chat_id = update.message.chat_id
        if chat_id in self.subscribers:
            context.bot.send_message(chat_id, text="You are already subscribed.")
            return
        self.subscribers.append(chat_id)
        context.bot.send_message(chat_id, text="You are now subscribed to updates.")

    def handle_stop(self, update, context):
        chat_id = update.message.chat_id
        if chat_id not in self.subscribers:
            context.bot.send_message(chat_id, text="You are not subscribed.")
            return
        self.subscribers.remove(chat_id)
        context.bot.send_message(chat_id, text="I shall not bother you any longer.")

    def handle_help(self, update, context):
        context.bot.send_message(update.message.chat_id, text="I know the commands 'start', 'stop'.")

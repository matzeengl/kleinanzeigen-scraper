from telegram.ext import Updater, CommandHandler

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

import utils

class Item:
    def __init__(self, title, price, url, date, image):
        self.title = title
        self.price = price
        self.url = 'https://www.ebay-kleinanzeigen.de' + url
        self.date = date
        self.image = image

    def __repr__(self):
        return f'{self.title} - {self.price} - {self.date}'

    def __str__(self):
        result = f'{self.title} - {self.price}'
        result += f'\n{self.date}\n'
        result += self.url
        result += '\n'
        return result

def start(update, context):
    logger.info('Bot received start command')

    if len(context.args) == 2:
        url = context.args[0]
        if "https://www.ebay-kleinanzeigen.de/" in url:
            name = str(update.effective_chat.id) + '_' + context.args[1]
            logger.info('Added job ' + name)
            scheduler.add_job(get_items_per_url, trigger='interval', args=[str(url), update.effective_chat.id], minutes=1, id=name)
            update.message.reply_text('Job angelegt.')
        else:
            update.message.reply_text('URL muss von Ebay Kleinanzeigen sein.')
    else:
        update.message.reply_text('Bitte gib URL und Name für den Job an.')

def pause(update, context):
    logger.info('Bot received pause command')
    job = scheduler.get_job(str(update.effective_chat.id) + '_' + context.args[0])

    if job is not None:
        job.pause()
        update.message.reply_text('Job ' + context.args[0] + ' pausiert.')
    else:
        update.message.reply_text('Job nicht gefunden.')

def delete(update, context):
    logger.info('Bot received delete command')
    name = str(update.effective_chat.id) + '_' + context.args[0]
    job = scheduler.get_job(name)

    if job is not None:
        scheduler.remove_job(name)
        update.message.reply_text('Job ' + context.args[0] + ' geloescht.')
    else:
        update.message.reply_text('Job nicht gefunden.')

def get_items_per_url(url, chat_id):

    try:
        driver.get(url)
    except:
        startBrowser()
        driver.get(url)

    articles = driver.find_elements_by_class_name('aditem')
    empty = len(last_items) == 0

    logger.info('Found ' + str(len(articles)) + ' ads.')

    for article in articles:
        if len(article.find_elements_by_class_name('icon-feature-topad')) > 0:
            continue
        else:
            id = article.get_attribute('data-adid')
            title = article.find_element_by_class_name('ellipsis').text
            price = article.find_element_by_class_name('aditem-main--middle--price').text
            link = article.get_attribute('data-href')
            date = article.find_element_by_class_name('aditem-main--top--right').text.strip()
            images = article.find_element_by_class_name('srpimagebox').find_elements_by_css_selector('img')
            image = images[0].get_attribute('src') if len(images) > 0 else None

            ad = Item(title, price, link, date, image)
            item = {id: ad}

            if empty:
                last_items[id] = item
            elif id not in last_items and "heute" in date.lower():
                last_items[id] = item
                if ad.image is not None:
                    bot.send_photo(chat_id=chat_id, photo=ad.image)
                bot.send_message(chat_id=chat_id, text=str(ad))

def error(update, context):
    logger.error('Update %s caused error %s', update, context.error)

def startBrowser():
    logger.info('Starting browser')
    options = Options()
    options.headless = True
    global driver
    driver = webdriver.Firefox(options=options, executable_path=r'C:\geckodriver.exe')

def main():
    logger.info('Starting main()')
    updater = Updater(bot=bot, use_context=True)

    logger.info('Starting Callback Handlers')
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("pause", pause))
    dispatcher.add_handler(CommandHandler("delete", delete))

    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    global logger
    logger = utils.get_logger()
    logger.info('Started logger')

    global last_items
    last_items = {}

    logger.info('Starting telegram bot')
    global bot
    bot = utils.get_bot()

    startBrowser()

    logger.info('Starting scheduler')
    jobstores = {'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')}
    global scheduler
    scheduler= BackgroundScheduler(jobstores=jobstores)
    scheduler.start()

    main()
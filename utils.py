import logging
from telegram import Bot
from telegram.utils.request import Request

def get_logger():
    logging.basicConfig(filename='scraper.log',
                        filemode='w',
                        format='%(asctime)s [%(levelname)s] %(message)s',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)

    return logger


def get_bot():
    request = Request(con_pool_size=8)
    return Bot(token="1903731434:AAHkEP26USf3pxVW-STNAEvNQxQo1rDOWT0", request=request)

import config
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
import sqlite3
import asyncio
import re
import ast
from playhouse.migrate import *
import datetime


from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiohttp import web
from aiogram.dispatcher.webhook import get_new_configured_app, SendMessage
import ssl


WEBHOOK_HOST = config.server_host  # Domain name or IP addres which your bot is located.
WEBHOOK_PORT = 443  # Telegram Bot API allows only for usage next ports: 443, 80, 88 or 8443
WEBHOOK_URL_PATH = '/'  # Part of URL тут ну типо просто юрл бота сам придумал

# This options needed if you use self-signed SSL certificate
# Instructions: https://core.telegram.org/bots/self-signed
WEBHOOK_SSL_CERT = config.cert_path  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = config.key_path  # Path to the ssl private key

WEBHOOK_URL = f"https://{WEBHOOK_HOST}:{WEBHOOK_PORT}{WEBHOOK_URL_PATH}"
WEBAPP_HOST = config.server_ip
WEBAPP_PORT = 30002

check = True

loop = asyncio.get_event_loop()
bot = Bot(token=config.token_dis, loop=loop)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

db = SqliteDatabase('test_base.db')
migrator = SqliteMigrator(db)


#1-й этап регистрация в базе проверка наличия в базе
#2-й этап проверка изменений в базе отправка обновлений с инлайном

#4-й этап пррем заявки
#5-й этап отслеживание заявки

class Clients(Model):
    id = IntegerField(primary_key=True)
    chat_id = IntegerField()
    zakaz_id = IntegerField(default=0)
    source = TextField()
    Zayavka = TextField(default='none')
    reg_day = DateTimeField(default=datetime.datetime.now)
    date_1 = DateTimeField()
    date_2 = DateTimeField()
    adres = TextField(default='none')
    tel_number = TextField(default='none')
    status = TextField(default='waiting_tel')
    master = TextField(default='none')
    summ = IntegerField(default=0)
    ocenka_mastera = TextField(default='none')
    dop_comment = TextField(default='none')
    otziv_o_client = TextField()
    data_compl = DateTimeField()
    class Meta():
        database = db

class Masters(Model):
    id = IntegerField(primary_key=True)
    master_id = IntegerField()
    tel_number = IntegerField()
    status = TextField(default='work')
    class Meta():
        database = db




    #при первом старате программы записывает номер пользователя в базу
#@dp.message_handler(commands=['start'])
async def send_welcome(message):
    print(message.text, 'я хз вообще')
    #если в базе есть, пишет "Снова привет"
    check_master = Masters.select().where(Masters.status == 'work', Masters.master_id == message.chat.id).count()
    if check_master > 0:
        print("Снова привет")
        await bot.send_message(message.chat.id, "Снова привет")
    else:
        print(check_master, "ЧО бляяяя")
        replye_mark = types.ReplyKeyboardMarkup(True, False)
        button_phone = types.KeyboardButton(text='Отправить номер телефона', request_contact=True)
        replye_mark.add(button_phone)
        await bot.send_message(message.chat.id, "Добавляем в базу мастеров, нажмите на 'Отправить номер телефона'", reply_markup=replye_mark)
        print("Добавляемся")
        new_master = Masters(master_id=message.chat.id)
        new_master.save()


#@dp.message_handler(content_types=types.ContentType.CONTACT)
async def take_contact(message):
    master_tel = Masters.update(tel_number=message.contact.phone_number).where(Masters.master_id == message.chat.id)
    master_tel.execute()
    await bot.send_message(message.chat.id, 'Телефон добавлен, приступаем к работе')




@dp.async_task
async def base_updates():
    # апдейт бд, проверяет БД на наличие изменений
    while check:
        try:
        #чекаем базу на редмет вышедших работать
        # чекаем клиентосов
            all_mast = Masters.select().where(Masters.status == 'work')
            clients = Clients.select().where(Clients.status == 'open')
            #cursor.execute('SELECT status FROM clients WHERE status="open"')
            #anser = cursor.fetchall()

            for i in clients:
                print(i.chat_id)
                for f in all_mast:
                    print(f.master_id)
                    try:
                        keyboard = types.InlineKeyboardMarkup()
                        callback_button = types.InlineKeyboardButton(text="Принять", callback_data=f"прием {i.chat_id}")
                        keyboard.add(callback_button)
                        print(i.Zayavka, i.adres, 'tut?')
                        await bot.send_message(f.master_id, f'Заявка: {i.Zayavka} Адрес: {i.adres}', reply_markup=keyboard)

                    except:
                        print('Fail')
                        await asyncio.sleep(5)
                    await asyncio.sleep(1)
                await asyncio.sleep(60)
            await asyncio.sleep(1)
        except:
            print('Fail')
            await asyncio.sleep(5)



#@dp.callback_query_handler(func=lambda cq: cq.data.startswith('прием'))
async def my_handler(callback_query: types.CallbackQuery):
    #await bot.answer_callback_query(callback_query.id, "Clicked")
    print(callback_query.data, "да вот оно")
    result = re.findall(r'\d', callback_query.data)
    f_result = ''.join(result)
    user_id = callback_query.message.chat.id
    #извлекаем из БД номер телефона
    try:
        client_tel = Clients.select().where(Clients.chat_id == f_result, Clients.status == 'open').get()
        print(client_tel.tel_number)
        #извлекаем и меняеем статус
        check_cl = Clients.update(status='master_take', master=user_id).where(Clients.chat_id == f_result,
                                                                              Clients.status == 'open')
        check_cl.execute()
        print("Vasyaaaaa")
        user_markup = types.ReplyKeyboardMarkup(True, True)
        user_markup.row('Заявка выполнена')
        #пробегаемся по извелченным из бд данным
        await bot.send_message(user_id,
                                   f'Заявка выполняется, по окончанию, нажать на "Заявка выполнена",'
                                   f' номер телефона клиента: {client_tel.tel_number}', reply_markup=user_markup)
        print(user_id)
    except:
        await bot.send_message(user_id, 'Заявку принял другой мастер')
    #result = callback_query.message.text
    #eval_qwe = ast.literal_eval(result) #полезная штука

    #result = re.findall(r'^\w+', client_id)#извлекаем первое слово
    #print(user_id, eval_qwe, 'going on whaaat')
    #con = sqlite3.connect('test_base.db')
    #cursor = con.cursor() #там не доделано
    #cursor.execute('SELECT id FROM clients WHERE status="open"')
    #anser_to_ask = cursor.fetchall()



#@dp.message_handler(func=lambda message: message.text == 'Заявка выполнена')
async def my_complete(message):
    print(message.text)
    print('now start my_complete')
    new_status = Clients.update(status='input_bablo').where(Clients.status == 'in_work',
                                                            Clients.master == message.chat.id)
    new_status.execute()
    rem_key = types.ReplyKeyboardRemove()
    await bot.send_message(message.chat.id, "Введите сумму, цифрами без пробелов и других знаков, пример: 3250", reply_markup=rem_key)

@dp.message_handler(func=lambda message: Clients.select()
                    .where(Clients.master == message.chat.id, Clients.status == 'input_bablo').count() > 0)
async def bablo_input(message):
    new_status = Clients.update(status='work_complete', summ=message.text).where(Clients.status == 'input_bablo', Clients.master == message.chat.id)
    new_status.execute()
    await bot.send_message(message.chat.id, "Спасибо за работу")


"""


РЕШЕНИЕ!!!
[In reply to Denis Naumov]
@dp.callback_query_handler(func=lambda cq: cq.data = 'CLICK')
async def my_handler(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id, "Clicked")
    
    
отличное решение!
и в твоем случае лучше сделать так:
в кнопку callback_data=f"my_btn:{id_to_reply}"
в фильтре func=lambda cq: cq.data.startswith('my_btn:')
"""
"""
loop = asyncio.get_event_loop()
tasks = [
    asyncio.ensure_future(base_updates()),
]
loop.run_until_complete(asyncio.wait(tasks))
"""

#loop.create_task(print_wow())
loop.run_until_complete(base_updates())



async def on_startup(app):
    # Demonstrate one of the available methods for registering handlers
    # This command available only in main state (state=None)
    dp.register_message_handler(send_welcome, commands=['start'])

    # This handler is available in all states at any time.
    dp.register_message_handler(take_contact, content_types=['contact'])
    dp.register_message_handler(my_handler, func=lambda cq: cq.data.startswith('прием'))
    dp.register_message_handler(my_complete, func=lambda message: message.text == 'Заявка выполнена')
    dp.register_message_handler(bablo_input, func=lambda message: Clients.select()
                    .where(Clients.master == message.chat.id, Clients.status == 'input_bablo').count() > 0)


    # Get current webhook status
    webhook = await bot.get_webhook_info()

    # If URL is bad
    if webhook.url != WEBHOOK_URL:
        # If URL doesnt match current - remove webhook
        if not webhook.url:
            await bot.delete_webhook()

        # Set new URL for webhook
        await bot.set_webhook(WEBHOOK_URL, certificate=open(WEBHOOK_SSL_CERT, 'rb'))
        # If you want to use free certificate signed by LetsEncrypt you need to set only URL without sending certificate.


async def on_shutdown(app):
    """
    Graceful shutdown. This method is recommended by aiohttp docs.
    """
    # Remove webhook.
    await bot.delete_webhook()

    # Close Redis connection.
    await dp.storage.close()
    await dp.storage.wait_closed()

if __name__ == '__main__':
    # Get instance of :class:`aiohttp.web.Application` with configured router.
    app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_URL_PATH)

    # Setup event handlers.
    # прописываем тут все наши хендлеры
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Generate SSL context
    #context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    #context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)

    # Start web-application.
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
    # Note:
    #   If you start your bot using nginx or Apache web server, SSL context is not required.
    #   Otherwise you need to set `ssl_context` parameter.


import config
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from playhouse.migrate import *
#https://habrahabr.ru/post/207110/  по Peewee статья остановился на 132 строчке
import datetime
import asyncio
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiohttp import web
from aiogram.dispatcher.webhook import get_new_configured_app, SendMessage
import ssl


WEBHOOK_HOST = config.server_host # Domain name or IP addres which your bot is located.
WEBHOOK_PORT = 443  # Telegram Bot API allows only for usage next ports: 443, 80, 88 or 8443
WEBHOOK_URL_PATH = '/'  # Part of URL тут ну типо просто юрл бота сам придумал

# This options needed if you use self-signed SSL certificate
# Instructions: https://core.telegram.org/bots/self-signed
WEBHOOK_SSL_CERT = config.cert_path  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = config.key_path  # Path to the ssl private key

WEBHOOK_URL = f"https://{WEBHOOK_HOST}:{WEBHOOK_PORT}{WEBHOOK_URL_PATH}"
WEBAPP_HOST = config.server_ip
WEBAPP_PORT = 30001


loop = asyncio.get_event_loop()
bot = Bot(token=config.token, loop=loop)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

db = SqliteDatabase('test_base.db')


 #просто заебся каждый раз переписывать

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
'''
migrate(
    migrator.rename_column('clients', 'chat_id ', 'chat_id'),
)
'''
check = True

# запуск бота через команду старт, проверяет статус пользователя, в базе или первый раз
# если первы йрзх регистрация телефон и имя, а на кой нам имя? Просто телефон, по началу без смс оповещения
#@dp.message_handler(commands=['start'])
async def handle_start(message):
    ssil = message.text # а тут передаем параметр который нам нужен дял партнерки
    clear_mas_data = re.findall(r"\d", str(ssil))
    data = "".join(clear_mas_data)
    print(data)
    #подключаемся к БД и добавляем наш Юзер ид и сурс или не добавляет если чел в базе, вначале чекаем а в базе ли он вообще
    all_clients = Clients.select().where(Clients.chat_id == message.chat.id, Clients.tel_number != 'none').count()
    print(all_clients)
    if all_clients == 0:
        #добавляем нового юзера в БД, если новый то
        new_user = Clients(chat_id=message.chat.id, source=data, status='waiting_tel')
        new_user.save()
        replye_mark = types.ReplyKeyboardMarkup(True, True)
        button_phone = types.KeyboardButton(text='Отправить номер телефона', request_contact=True)
        replye_mark.add(button_phone)
        await bot.send_message(message.chat.id, 'Вначале пройдите небольшую регистрацию,'
                                          ' просто нажмите на "Отправить номер телефона"'
                                          ' телефон отправится автоматически и вы зарегистрируетесь.',
                         reply_markup=replye_mark)

    else:
        user_markup = types.ReplyKeyboardMarkup(True, True)
        user_markup.row('Вызвать мастера')
        #тут главное меню
        await bot.send_message(message.chat.id, 'И снова сдрасте!', reply_markup=user_markup)



#@dp.message_handler(content_types=['contact'])
# Clients.select().where(Clients.chat_id == message.chat.id, Clients.status == 'waiting_tel').count() > 0)
async def client_number_registration(message):
    # обрабатываем контакт
    if message.contact.user_id != message.chat.id:
        await bot.send_message(message.chat.id, 'Отправьте пожалуйста свои контакты')
    else:
        client_tel = Clients.update(tel_number=message.contact.phone_number, status='waiting')\
            .where(Clients.chat_id == message.chat.id, Clients.status == 'waiting_tel')
        client_tel.execute()
        user_markup = types.ReplyKeyboardMarkup(True, True)
        user_markup.row('Вызвать мастера')
        await bot.send_message(message.chat.id, 'Спасибо за телефон', reply_markup=user_markup)



#@dp.message_handler(func=lambda message: message.text == 'Вызвать мастера')
async def vizvat_mastera(message):
    # может впервый раз, а может раньше уже делал заявки
    #max_client = Clients.select(fn.MAX(Clients.zakaz_id))
    # для первого раза сделаем вначале
    print('Fuck')
    check_client = Clients.select().where(Clients.chat_id == message.chat.id)
    # БЛЯЯ!!!!!!!!! !! !!! !!
    for f in check_client:
        #пролемная функция, сцука решение не верное
        if f.status == "open":
            await bot.send_message(message.chat.id, 'Вы уже отправили заявку, ожидайте назначения мастера')
        elif f.status == 'complete':
            number_tel = f.tel_number
            date_now = datetime.datetime.now()
            new_zay = Clients(chat_id=message.chat.id, status='input_zayavka', tel_number=number_tel,
                              date_1=date_now)
            new_zay.save()
            await bot.send_message(message.chat.id, 'Опишите задание для мастера')
            # новая строка тут делается
        elif f.status == 'waiting': # т.е. в ожидании чего то)
            date_now = datetime.datetime.now()
            upd_zay = Clients.update(chat_id=message.chat.id, status='input_zayavka', date_1=date_now)\
                .where(Clients.chat_id == message.chat.id, Clients.status == 'waiting')
            upd_zay.execute()
            await bot.send_message(message.chat.id, 'Опишите задание для мастера')

        break


#@dp.message_handler(func=lambda message: Clients.select()
 #                    .where(Clients.chat_id == message.chat.id,
  #                          Clients.status == 'input_zayavka').count()>0)
async def input_adres(message):
    print('FUCK')
    new_adres = Clients.update(Zayavka=message.text, status='input_adres').where(Clients.chat_id == message.chat.id,
                                                                       Clients.status == 'input_zayavka')
    new_adres.execute()
    await bot.send_message(message.chat.id, 'Укажите улицу и номер дома, куда приехать мастеру')



#@dp.message_handler(func=lambda message: Clients.select()
#                    .where(Clients.chat_id == message.chat.id,
#                          Clients.status == 'input_adres').count() > 0)
# функция принимает адрес меняет статус заявки на open
async def waiting_for(message):
    print('FUCK yeah')
    new_open = Clients.update(adres=message.text, status='open').where(Clients.chat_id == message.chat.id,
                                                                       Clients.status == 'input_adres')
    new_open.execute()
    await bot.send_message(message.chat.id, "Спасибо за вашу заявку, ожидайте назначения ближайшего мастера")



@dp.async_task
async def master_take():
    while check:
        try:
            print('WOOOW ')
            search_status_m = Clients.select().where(Clients.status == 'master_take')
            search_status_w = Clients.select().where(Clients.status == 'work_complete')
            await asyncio.sleep(5)
            print(search_status_m, search_status_w)
            for f in search_status_m:
                print(f.status)
                new_status = Clients.update(status='in_work').where(Clients.chat_id == f.chat_id, Clients.status == 'master_take')
                new_status.execute()
                await bot.send_message(f.chat_id, 'Мастер назначен, скоро он с вами свяжется')
            for f in search_status_w:
                money = f.summ
                print(f.status)
                new_status = Clients.update(status='complete').where(Clients.chat_id == f.chat_id, Clients.status == 'work_complete')
                new_status.execute()
                await bot.send_message(f.chat_id,
                                       f'Сумма всех работ, которые выполнил мастер: {money}, спасибо, что обратились к нам.')

        except:
            print('Error')
            await asyncio.sleep(5)











loop.run_until_complete(master_take())

#loop.close()


#loop2 = asyncio.get_event_loop()
#
#wait_tasks = asyncio.wait(tasks)
#loop2.run_until_complete(wait_tasks)

# тут мы прописываем все наши функции
async def on_startup(app):
    # Demonstrate one of the available methods for registering handlers
    # This command available only in main state (state=None)
    dp.register_message_handler(handle_start, commands=['start'])

    # This handler is available in all states at any time.
    dp.register_message_handler(client_number_registration, content_types=['contact'])
    dp.register_message_handler(vizvat_mastera, func=lambda message: message.text == 'Вызвать мастера')
    dp.register_message_handler(input_adres, func=lambda message: Clients.select()
                     .where(Clients.chat_id == message.chat.id,
                            Clients.status == 'input_zayavka').count()>0)
    dp.register_message_handler(waiting_for, func=lambda message: Clients.select()
                     .where(Clients.chat_id == message.chat.id,
                            Clients.status == 'input_adres').count() > 0)


    # Get current webhook status
    webhook = await bot.get_webhook_info()
    print(webhook, 'vasyaaa')

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

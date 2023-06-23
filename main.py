''' The main file of the FaceFoundBot bot.
Take a look at config.py and write your tokens (Telegram and QiWI),
as well as MySQL server authorization data.
And also change the list of administrators (ADMINS_LIST) '''
import datetime
import logging

from aiogram import Bot, types
from aiogram.utils import executor
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import *
from DB import DataBase
from Payments import Payments
from FaceFound import FaceFound
from keyboards import *
from states import *

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

db = DataBase('db.db')
# pay = Payments(QiWiTOKEN, db)

face_found = FaceFound(db=db, tmp_dir=TMP_IMG_DIR, save_dir=SAVE_IMG_DIR)

# -------------logs------------
logging.basicConfig(
    filename="all_log.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s -%(message)s')
warning_log = logging.getLogger("warning_log")
warning_log.setLevel(logging.WARNING)
fh = logging.FileHandler("warning_log.log")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
warning_log.addHandler(fh)
# -------------logs-------------


def check_user_status(user_id):
    status = {
        'is_reg': True,
        'is_ban': False,
        'are_attempts_available': True
    }
    user = db.get_user(user_id)

    if user[1] is None:
        status['is_reg'] = False
        return status
    else:
        if user[1][5] == -1:
            status['is_ban'] = True

    # if user isn`t an admin or vip and his number of requests is less than the maximum
    if not user[1][5] in [1, 2] and db.get_count_requests(user_id)[1] >= COUNT_OF_USERS_REQUESTS:
        status['are_attempts_available'] = False
    return status


# -------------commands-------------
@dp.message_handler(commands=['start'], state='*')
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    hello_mess = f"Приветствую тебя {message.from_user.first_name}.\n" \
                 f"Данный бот умеет искать людей по присланной фотографии в своей базе данных." \
                 f"Пришлите фотографию или введите /s\n"
    if not check_user_status(message.from_user.id)['is_reg']:  # if the user exists in DB
        hello_mess += f"Но для начала, укажите день свего рождения.\nФормат: д.м.г"
        await bot.send_message(message.from_user.id, hello_mess)
        await state.set_state(RegUserStates.choosing_date_of_birth)
    else:
        await bot.send_message(message.from_user.id, hello_mess)


@dp.message_handler(state=RegUserStates.choosing_date_of_birth, content_types=['text'])
async def get_user_date_of_birth(message, state: FSMContext):

    date_of_birth = datetime.datetime.strptime(message.text, "%d.%m.%Y").date()
    if (datetime.datetime.now().date() - date_of_birth).days > 6570:
        await state.update_data(date_of_birth=date_of_birth)
        with open('licence.txt', 'r') as f:
            await bot.send_document(
                message.from_user.id,
                caption="Отлично, теперь, прочитайте и согласитесь с условиями использования",
                document=f,
                reply_markup=make_inline_keyboard(
                    [{'text': "Я согласен(на)", 'url': "", 'callback': "user_accept_the_license"}]
                )
            )
        await state.set_state(RegUserStates.choosing_confirmation_acceptance)
    else:
        await bot.send_message(message.from_user.id, "Бот доступен только пользователям старше 18 лет")
        db.add_user(message.from_user.id, message.from_user.first_name, message.from_user.username, str(date_of_birth), status=-1)


@dp.callback_query_handler(text="user_accept_the_license", state=RegUserStates.choosing_confirmation_acceptance)
async def create_user(call: types.CallbackQuery, state):
    state_data = await state.get_data()
    db.add_user(
        call.from_user.id,
        call.from_user.first_name,
        call.from_user.username,
        str(state_data.get('date_of_birth'))
    )
    await state.reset_state()
    await bot.send_message(call.from_user.id, "Отлично, я зарегитсрировал Ваш аккаунт, приятного пользования🙃")
    await call.answer()


@dp.message_handler(commands=['help'], state='*')
async def help(message: types.Message, state: FSMContext):
    await bot.send_message(
        message.from_user.id,
        f"Данный бот помогает найти человека по фотографии.\n"
        f"Пришлите мне фото человека с отчетливо видимым лицом и я попробую найти его в своей базе.\n"
        f"Также Вам доступен список команд:\n"
        f"/start - Начальная команда, бот попросит ввести дату рождения и согласиться с условиями использования,\n"
        f"/s - начать поиск по фотографии, введите данную команду и отправьте фото или отправьте фото без ввода команды,\n"
        f"/del - удалить свой аккаунт из базы,\n/help - вывести сообщение помощи.\n"
        f"Если у Вас возникли проблемы, обратитесь к администратору @{ADMIN_USERNAME}")  # look config.py


async def search_photo_in_db(message: types.Message) -> (bool, ()):

    db.add_request(message.from_user.id)
    photo = message.photo[-1]
    photo_file = await photo.download(destination_dir=TMP_IMG_DIR)
    matches_found = face_found.find_face(photo_file.name)
    os.remove(photo_file.name)
    if not matches_found:
        return False, ()
    mess = "Совпадения найдены! Список:\n"
    images = []
    peoples_found = db.get_face_encodings_data_by_id(matches_found)
    if peoples_found[0]:
        for people in peoples_found[1]:
            mess += (people[0] or "") + "\n"  # source_url
            images.append(people[1])  # image_url
    else:
        await bot.send_message(message.from_user.id, "Извините, произошла ошибка, попробуйте еще раз. /help")
        return False
    mess += "Это не означает, что человек на Вашем фото и найденный(е) это один и тот же человек!"
    return True, (mess, images)


@dp.message_handler(content_types=['photo'], state="*")
async def photo(message: types.Message, state: FSMContext):
    text = message.caption
    if text:
        text = text.split()
    else:
        await search(message, state)
        return

    if text[0] == '/s' or text[0] == '/search':
        await search(message, state)
        return
    if text[0] == '/add':
        await add(message, state)
        return


@dp.message_handler(commands=['s', 'search'], state='*')
async def search(message: types.Message, state: FSMContext):

    user_status = check_user_status(message.from_user.id)

    if user_status['is_ban']:
        await bot.send_message(message.from_user.id, "Вы забанены!")
        return

    if not user_status['is_reg']:
        await start(message, state)
        return

    if not user_status['are_attempts_available']:
        await bot.send_message(message.from_user.id, f"В день доступно {COUNT_OF_USERS_REQUESTS} поисков.")
        return

    if message.photo:
        matches = await search_photo_in_db(message)
        if matches[0]:
            media = types.MediaGroup()
            for coincidence in matches[1][1]:
                media.attach_photo(types.InputFile(coincidence))
            await bot.send_message(message.from_user.id, matches[1][0])
            await bot.send_media_group(message.from_user.id, media=media)
        else:
            await bot.send_message(message.from_user.id, "Совпадения не найдены")
        await state.reset_state()
        return
    await bot.send_message(message.from_user.id, "Пришли мне фото человека.\n"
                                                 "На фото должно быть отчётливо видно лицо.\n"
                                                 "Внимание! Категоричеки запрещается присылать фотографии несовершеннолетних или"
                                                 " фотографии содержащие материалы, противоречащие законодательству РФ, в том числе "
                                                 "фото- и видеоматериалы порнографического характера.")


@dp.message_handler(commands=['del'], state='*')
async def delete(message: types.Message, state: FSMContext):
    user_status = check_user_status(message.from_user.id)
    if user_status['is_ban']:
        await bot.send_message(message.from_user.id, "Вы забанены! Удаление аккаунта недоступно(")
        return
    await bot.send_message(message.from_user.id,
                           "Вы пытаетесь удалить свой акаунт. Это действие невозможно отменить, вы уверены?\n"
                           "Вы потеряете свой vip-статус, если он имеется.",
                           reply_markup=make_inline_keyboard([
                               {'text': "Я согласен(на)", 'url': "", 'callback': "dell_acc_yes"},
                               {'text': "Отмена", 'url': "", 'callback': "dell_acc_cancel"}
                           ]))


@dp.callback_query_handler(text="dell_acc_yes", state='*')
async def dell_acc_yes(call: types.CallbackQuery, state: FSMContext):

    if db.del_user(call.from_user.id):
        await bot.send_message(call.from_user.id, "Аккаунт удалён")
        await call.message.delete()
    else:
        await bot.send_message(call.from_user.id, "Произошла ошибка. /help")
    await call.answer()


@dp.callback_query_handler(text="dell_acc_cancel", state='*')
async def dell_acc_cancel(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.answer()

async def add(message: types.Message, state: FSMContext):

    if not message.from_user.id in ADMINS_LIST:
        await bot.send_message(message.from_user.id, "Вы не имеете доступа к данной команде ❌")
        return
    photo_file = None
    if message.photo:
        photo_file = await message.photo[-1].download(destination_dir=TMP_IMG_DIR)

    text = message.caption.split()
    source = None
    if len(text) == 2:
        source = text[1]

    if photo_file:
        if face_found.add_face_in_db(photo_file.name, source):
            await bot.send_message(message.from_user.id, "Добавление прошло успешно ✅")
        else:
            await bot.send_message(message.from_user.id, "Произошла ошибка ❌")
    else:
        await bot.send_message(message.from_user.id, "Формат: фотография + /add [ссылка на источник]")


# @dp.message_handler(commands=['vip'], state='*')
# @dp.message_handler(lambda message: message.text == 'vip', state='*')
# async def vip(message):
#     id = message.from_user.id
#     if db.is_vip(id):
#         await bot.send_message(id, "Вы уже VIP, спасибо!")
#     else:
#         keyBoard = InlineKeyboardMarkup()
#         keyBoard.add(
#             InlineKeyboardButton(text="Хочу быть VIP💎", callback_data="buy_vip")
#         )
#         await bot.send_message(id, "<b>VIP пользователи</b> могут: могут использователь бот неограниченное количество раз",
#                                parse_mode=ParseMode.HTML,
#                                reply_markup=make_inline_keyboard([
#                                    {'text': "Хочу быть VIP💎", 'callback': "buy_vip"}
#                                ]))
#
# @dp.callback_query_handler(text="buy_vip")
# async def buy_vip(call: types.CallbackQuery):
#     if db.is_vip(call.from_user.id):
#         await call.answer(text="Вы уже VIP 🙃", show_alert=True)
#         return False
#     bill = pay.get_bill(COST_OF_VIP, call.from_user.id)
#     pay_murkup = InlineKeyboardMarkup(row_width=2)
#     pay_btn = InlineKeyboardButton("Оплатить \U0001F4B0", url=bill.pay_url)
#     check_btn = InlineKeyboardButton("Проверть платёж \U00002705", callback_data=f"check_pay_{bill.bill_id}")
#     cancel_btn = InlineKeyboardButton("Я передумал(а)", callback_data=f"cancel_buy_vip_{bill.bill_id}")
#     pay_murkup.add(pay_btn, check_btn, cancel_btn)
#     await bot.send_message(call.from_user.id,
#                            f"Стоимость VIP доступа: {COST_OF_VIP}руб.\n"
#                            f"Ссылка для оплаты {bill.pay_url}\n"
#                            f"<b>Совет: </b> оплачивайте с QIWI-кошелька без комиссии",
#                            reply_markup=pay_murkup,
#                            parse_mode="HTML")
#     await call.answer()
#
# @dp.callback_query_handler(text_contains="check_pay_")
# async def check_pay(call):
#     if call.data[:10] == "check_pay_":
#         resp = pay.check_bill(call.data[10:])
#         if resp == 0:
#             await bot.send_message(call.message.chat.id,
#                                    "Вы не делали запрос на оплату \U0000274C\nИли счёт уже оплачен \U00002705")
#         elif resp == 1:
#             await bot.send_message(call.message.chat.id,
#                                    f"Вы не оплатили счёт. Ошибка? свяжитесь с администратором {ADMIN_USERNAME}, предоставьте свой id телеграм аккаунта и скриншот оплаты\n")
#         elif resp == 2:
#             db.give_vip(call.from_user.id)
#             await bot.send_message(call.from_user.id, "Спасибо за оплату! \U0001F389")
#             db.delete_check(call.data[10:])
#             await bot.delete_message(call.from_user.id, call.message.message_id)
#     await call.answer()
#
# @dp.callback_query_handler(text_contains="cancel_buy_vip_")
# async def cancel_pay(call):
#     if call.data[:15] == "cancel_buy_vip_":
#         db.delete_check(call.data[15:])
#         await bot.delete_message(call.from_user.id, call.message.message_id)
#         await call.answer(text="Счёт удалён", show_alert=True)
# -------------commands-------------


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, )

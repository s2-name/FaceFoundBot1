from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def make_reply_keyboard(buttons: list) -> ReplyKeyboardMarkup | None:
    if len(buttons) == 0:
        return None

    keyboard = ReplyKeyboardMarkup()
    for butt in buttons:
        keyboard.add(KeyboardButton(butt))
    return keyboard


def make_inline_keyboard(buttons: [dict]) -> InlineKeyboardMarkup | None:
    if len(buttons) == 0:
        return None

    keyboard = InlineKeyboardMarkup()
    for butt in buttons:
        keyboard.add(InlineKeyboardButton(butt['text'], url=butt['url'], callback_data=butt['callback']))
    return keyboard

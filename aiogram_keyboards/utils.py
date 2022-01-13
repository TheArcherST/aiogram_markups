from typing import Union

import hashlib

from aiogram.types import Message, CallbackQuery


def _hash_text(string: str) -> str:
    """Hash text function

    Hashing use to detect buttons from callback_data.
    Target is compress button text and identify button
    after script restart, even if keyboards changed.
    It need to save functional of already exists in
    telegram buttons.

    return : str
        Text, hashed by algorithm `MD5`, hex value

    """

    hash_ = hashlib.md5(string.encode('utf-8'))
    result = hash_.hexdigest()

    return result


contain_chat_id_alias = Union[Message, CallbackQuery, int, str]


def get_chat_id(obj: contain_chat_id_alias):
    """ Get chat id function """

    if isinstance(obj, str):
        return obj

    if isinstance(obj, int):
        return str(obj)

    if isinstance(obj, Message):
        return obj.chat.id

    if isinstance(obj, CallbackQuery):
        return obj.message.chat.id

    raise KeyError(f"Cant get `chat_id` of object {obj}")

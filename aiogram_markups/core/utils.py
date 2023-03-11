from typing import Optional

import hashlib

from aiogram.dispatcher.filters import Filter


def hash_text(string: Optional[str]) -> str:
    """Hash text function

    Hashing use to detect buttons from callback_data.
    Target is compress button text and identify button
    after script restart, even if keyboards changed.
    It need to save functional of already exists in
    telegram buttons.

    return : str
        Text, hashed by algorithm `MD5`, hex value

    """

    if string is None:
        return '0'

    hash_ = hashlib.md5(string.encode('utf-8'))
    result = hash_.hexdigest()

    return result


class BoolFilter(Filter):
    def __init__(self, boolean: bool):
        self.boolean = boolean

    async def check(self, *args) -> bool:
        return self.boolean

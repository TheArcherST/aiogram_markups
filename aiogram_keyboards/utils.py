import hashlib


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

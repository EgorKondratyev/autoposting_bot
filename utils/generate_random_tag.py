import random
import string
from hashlib import md5


async def generate_random_tag_md5() -> str:
    random_text = ''
    words = string.ascii_letters
    digits = string.digits
    for i in range(1, 100):
        random_text += random.choice(words)
        random_text += random.choice(digits)

    hash_text = md5(random_text.encode())
    tag = hash_text.hexdigest()
    return tag

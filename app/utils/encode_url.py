"""
Generates a unique short URL ID by converting a MongoDB ObjectId 
to a compact Base62-encoded string.

Steps:
1. Create a new MongoDB ObjectId (which is globally unique).
2. Convert the ObjectId’s 24-character hex string to an integer.
3. Encode this integer into a Base62 string using digits, uppercase,
   and lowercase letters for compactness.

The resulting short ID is unique, collision-free, and shorter than
the original ObjectId representation, suitable for URL shortening.
"""

from  bson import ObjectId
from app import settings

class ShortIdGenerator:
    @classmethod
    def encode_base62(cls, num:int) -> str:
        if num == 0:
            return settings.BASE62[0]
        base62 = []
        while num:
            num, rem = divmod(num, 62)
            base62.append(settings.BASE62[rem])
        return ''.join(reversed(base62))
    

    @classmethod
    def generate(cls):
        obj = ObjectId()
        obj_id_int = int(str(obj), 16)
        return cls.encode_base62(obj_id_int)
    


import hashlib

def hasher(data):
    hashObj= hashlib.blake2b(digest_size= 32)
    hashObj.update(data)
    return hashObj.hexdigest()

from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.Cipher import PKCS1_OAEP

#Generate private and public keys
random_generator = Random.new().read
def prkey_generate(size): return RSA.generate(size, random_generator)

def prkey_load(filepath):
    with open(str(filepath) + ".prkey", "rb") as file:
        key = file.read()
        
        return RSA.import_key(key)

def prkey_export(filepath, size):
    with open(str(filepath) + ".prkey", "wb") as file:
        file.write(prkey_generate(size).export_key())

pukey = lambda prkey: prkey.publickey()

encryptor = lambda pukey: PKCS1_OAEP.new(pukey)
class Enc:
    def __init__(self, encryptor): self.encryptor = encryptor

    def enc(self, text): return self.encryptor.encrypt(text)

decryptor = lambda prkey: PKCS1_OAEP.new(prkey)
class Dec:
    def __init__(self, decryptor): self.decryptor = decryptor

    def dec(self, ciphertext): return self.decryptor.decrypt(ciphertext)

""" class Encryption:
    def __init__(self, size: int):
        self.prkey = RSA.generate(size, Random.new().read)
        self.pukey = self.prkey.publickey()
        self.encryptor = PKCS1_OAEP.new(self.pukey)
        self.decryptor = PKCS1_OAEP.new(self.prkey)

    def enc(self, text: str): """
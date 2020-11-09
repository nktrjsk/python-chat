# -*- coding: utf-8 -*-

import random
import db_tools as dt
import time
start = time.time()
import asymencrypt as ae
import os

"""
characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.-_1234567890+*"
getRandom = lambda rang: "".join(random.choice(characters) for i in range(rang))

print(getRandom(16))
"""

#for i in range(32): dt.generate_reg_key()

#ae.prkey_export("private_serv")
#ae.prkey_load("private")

#end = time.time() - start
#print(f"Čas: {end}")

#print(len("".encode("utf-8")))

start = time.time()

for i in range(1000): print("kkt" * i)

end = time.time() - start

print(end)
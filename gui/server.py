import socket
from threading import Thread
import threading
import time
import json
import db_tools as dt
import asymencrypt as ae
import pickle
import checksumdir
import os

with open("conf.json", "r", encoding="utf-8") as soubor:

    sett = json.load(soubor)

IP = sett["IP"]
PORT = sett["PORT"]
SOCKET = (IP, PORT)
OPEN = sett["OPEN"]
REG_KEY = sett["REG_KEY"]
NAME = sett["NAME"]
DESCRIPTION = sett["DESCRIPTION"]
RSA = sett["RSA"]
RSA_LENGHT = sett["RSA_LENGHT"]

if OPEN == True: authshow = "O"
elif OPEN == False: authshow = "P"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(SOCKET)
server.listen()

print(
f"""IP: {IP}:{PORT}
Open: {OPEN}
Regkey: {REG_KEY}
Jméno: {NAME}
Popisek: {DESCRIPTION}
RSA: {RSA}, {RSA_LENGHT}
"""
)

ROOMS = {}
ROOMS_CLIENT = []
CLIENTS = []
NAMES = []
BANNED_NAMES = ["", "ROOMS", "SERVER"]

ROOMS["Start"] = [0, "", "SERVER", []]
ROOMS_CLIENT.append(["Start", 0, "SERVER"])

emotes = {}

for i in [i for i in os.listdir("emotes/")]:

    with open("emotes/" + i, "rb") as soubor:

        print(i)
        
        emotes[i] = soubor.read()

hash_emote = checksumdir.dirhash(os.getcwd() + "//emotes")
print(len(emotes), hash_emote)

class Client:
    def join_room(self, name):       
        if self.room != str():
            if self.room in ROOMS:
                ROOMS[self.room][3].remove(
                    [self.conn, self.pu_key_client, self.name]
                    )
                broadcast(
                    ["CLIENTS", "rem-cl", self.name],
                    ROOMS[self.room][3], "SERVER"
                    )

        broadcast(["CLIENTS", "add-cl", self.name], ROOMS[name][3], "SERVER")
        ROOMS[name][3].append([self.conn, self.pu_key_client, self.name])
        self.room = name
        print(ROOMS[self.room][3])
        self.sened(["joined-room", self.room])
        broadcast(
            ["CLIENTS",
            "init-cl",
            [ROOMS[self.room][3][i][2] for i in range(len(ROOMS[self.room][3]))]
            ],
            [[self.conn, self.pu_key_client, self.name]],
            "SERVER"
            )

    def __init__(self, conn, address):
        self.conn = conn
        self.address = address

        conn.send(pickle.dumps([NAME, DESCRIPTION, authshow, RSA, REG_KEY]))

        if RSA == True:            
            key = conn.recv(1024)
            self.pu_key_client = ae.RSA.import_key(key)

            pr_key_ser = ae.prkey_generate(1024)
            pu_key_ser = ae.pukey(pr_key_ser)

            conn.send(pu_key_ser.export_key())

            encryptor = ae.encryptor(self.pu_key_client)
            enc = ae.Enc(encryptor).enc
            
            decryptor = ae.decryptor(pr_key_ser)
            dec = ae.Dec(decryptor).dec

            def sened(data):
                text = pickle.dumps(data) + b"/END#"

                while True:
                    if text == b"": break
                    conn.sendall(enc(text[:50]))
                    text = text[50:]
            
            def recev():
                text = bytes()
    
                while True:
                    if text.endswith(b"/END#"): break
                    text += dec(conn.recv(128))

                return pickle.loads(text[:-4])
        
        else:
            self.pu_key_client = None

            def sened(data):
                text = pickle.dumps(data) + b"/END#"

                while True:
                    if text == b"": break
                    conn.sendall(text[:50])
                    text = text[50:]

            def recev():
                text = bytes()
    
                while True:
                    if text.endswith(b"/END#"): break
                    text += conn.recv(128)

                return pickle.loads(text[:-4])
        
        self.sened = sened
        self.recev = recev

        while True:
            try: auth = recev()
            except (ConnectionResetError, ValueError): return

            if auth[0] == "log":
                if OPEN == True:
                    if auth[1] in NAMES or auth[1] in BANNED_NAMES:                       
                        sened("#conn-name-0")
                        continue                    
                    else:                        
                        NAMES.append(auth[1])
                        CLIENTS.append([conn, self.pu_key_client, auth[1]])
                        sened("#conn-1")
                        break

                if OPEN == False:
                    if auth[1] in NAMES: sened("#conn-name-0"); break
                    if dt.check_user(auth[1], auth[2]) == True:
                        NAMES.append(auth[1])
                        CLIENTS.append([conn, self.pu_key_client, auth[1]])
                        sened("#conn-1")
                        break

                    else: sened("#conn-0"); continue
            
            elif auth[0] == "reg":
                reg_stav = True

                if auth[1] in BANNED_NAMES: sened("#username-taken")
                if REG_KEY == True:
                    if dt.check_reg_key(auth[3]) == False:      
                        sened("#reg-0-key")
                        reg_stav = False
                        continue
                
                if dt.check_name(auth[1]) == True:                  
                    sened("#username-taken")
                    reg_stav = False
                    continue

                if reg_stav == True:                    
                    dt.add_user(auth[1], auth[2])
                    sened("#reg-1")
                

        print(f"Připojen: {auth[1]}")

        try:

            self.name = auth[1]
            self.room = str()

            self.sened(["ROOMS", "init-room", ROOMS_CLIENT])

            while True:

                text = recev()

                if text[0] == "create-room":
                    create_room(text[1], text[2], text[3], text[4])
                    continue
                if text[0] == "remove-room":
                    remove_room(text[1], text[2])
                    continue

                elif text[0] == "join-room": 
                    if self.room != text[1]:                       
                        self.join_room(text[1])
                        continue

                elif text == "!rooms":
                    sened([self.name, str(ROOMS), cas()])
                    continue
                elif text == "ping":
                    sened(["server", "pong", cas()])
                    continue
                elif text == "!name":
                    sened(["server", str(NAMES), cas()])
                    continue
                elif text[0] == "emotes":
                    if text[1] != hash_emote:
                        sened(["semotes"])
                        #time.sleep(1)
                        for i in emotes:
                            sened(["emote", [i, emotes[i]]])
                        #time.sleep(1)
                        sened(["eemotes"])
                    
                    continue
                
                else:                   
                    try:
                        print("clients", len(ROOMS[self.room][3]))
                        broadcast(text, ROOMS[self.room][3], self.name)
                    except KeyError: print("chyba")

        except ConnectionResetError:           
            if self.room != str():               
                ROOMS[self.room][3].remove([conn, self.pu_key_client, self.name])
                broadcast(
                    ["CLIENTS", "rem-cl", self.name],
                    ROOMS[self.room][3], "SERVER"
                    )

            try: CLIENTS.remove([conn, self.pu_key_client, self.name])
            except ValueError: pass
            NAMES.remove(self.name)
            print(f"Odpojen: {self.name}")
            print(threading.active_count())

def broadcast(data, clients, name):       
    if type(data) == str: text = pickle.dumps([name, data, cas()])
    else: text = pickle.dumps(data)
    text = text + b"/END#"

    if RSA == True:       
        for i in clients:
            send_text = text

            while True:
                if send_text == b"": break
                part = send_text[:50]
                i[0].send(ae.Enc(ae.encryptor(i[1])).enc(part))
                send_text = send_text[50:]
    
    else:
        for i in clients:
            send_text = text
            
            while True:
                if send_text == b"": break
                part = send_text[:50]
                i[0].send(part)
                send_text = send_text[50:]

def cas():
    cas = time.localtime()

    hodiny = cas[3]
    minuty = cas[4]

    if int(minuty) < 10: minuty = f"0{minuty}"

    return f"{hodiny}:{minuty}"

def create_room(name, auth, password, creator):
    if name not in ROOMS:
        ROOMS[name] = [auth, password, creator, []]
        ROOMS_CLIENT.append([name, auth, creator])

        broadcast(["ROOMS", "add-room", [name, auth, creator]], CLIENTS, "SERVER")

def remove_room(name, user):
    auth = ROOMS[name][0]
    creator = ROOMS[name][2]

    print("klient věc", ROOMS_CLIENT)

    if ROOMS[name][2] == user:
        print("klient věc", [name, auth, creator])

        broadcast(["ROOMS", "rem-room", [name, auth, creator]], CLIENTS, "SERVER")
        broadcast("Roomka byla odstraněna.", ROOMS[name][3], "SERVER")
        
        ROOMS.pop(name)
        ROOMS_CLIENT.remove([name, auth, creator])

        print(f"roomka {name} gon")

while True:
    conn, address = server.accept()
    Thread(target=Client, args=(conn, address)).start()
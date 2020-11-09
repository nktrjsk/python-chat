import socket
from threading import Thread
import threading
import time
import sys
import json
import sqlite3 as sql
import db_tools as dt
import asymencrypt as ae

with open("conf.json", "r", encoding="utf-8") as file:

    sett = json.load(file)

ROOMS = []
CLIENTS = []

IP = sett["IP"]
PORT = sett["PORT"]
SOCKET = (IP, PORT)
FORMAT = sett["FORMAT"]
OPEN = sett["OPEN"]
REG_KEY = sett["REG_KEY"]
GEN_KEY = sett["GEN_KEY"]
NAME = sett["NAME"]
DESCRIPTION = sett["DESCRIPTION"]

# Vygenerování public a private klíčů
if GEN_KEY == True:

    print("Generuji RSA klíč...")
    pr_key_ser = ae.prkey_generate(1024)
    pu_key_ser = ae.pukey(pr_key_ser)

else:

    print("Načítám RSA klíč...")
    pr_key_ser = ae.prkey_load("private_serv")
    pu_key_ser = ae.pukey(pr_key_ser)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(SOCKET)
server.listen()

print(f"[STAV] Server byl spuštěn.\n\nIP: {IP}\nPORT: {PORT}\nFORMAT: {FORMAT}\nOPEN: {OPEN}\nNAME: {NAME}\nDESCRIPTION: {DESCRIPTION}")

while True:

    # Přijímá připojení od klienta
    conn, address = server.accept()

    # Výměna public klíčů
    conn.send(pu_key_ser.export_key())

    pu_key_client = ae.RSA.import_key(conn.recv(1024))

    encryptor = ae.encryptor(pu_key_client)
    enc = ae.Enc(encryptor).enc
    decryptor = ae.decryptor(pr_key_ser)
    dec = ae.Dec(decryptor).dec

    #
    #CLIENTS[conn] = 
    
    # Odeslání informací o serveru
    conn.send(enc(bytes(f"{OPEN};{REG_KEY};{NAME};{DESCRIPTION}", FORMAT)))

    # Nezabezpečený server
    if OPEN == True:

        try: name = dec(conn.recv(1024)).decode(FORMAT)
        except: continue

        if name not in [i[0] for i in CLIENTS]:

            conn.send(enc(bytes("200", FORMAT)))
            CLIENTS.append([name, conn, pu_key_client])
        
        else:

            conn.send(enc(bytes("403", FORMAT)))

    # Zabezpečený server, ke kterému je nutné mít účet
    else:

        while True:

            try: yes = dec(conn.recv(1024)).decode(FORMAT)
            except: conn.close(); break

            request = yes.split(";")
            
            # Registrace
            if request[0] == "reg":
                
                user, passw, key = request[1:4]

                dt.c.execute("SELECT username FROM clients")
                user_db = dt.c.fetchall()

                userTaken = False

                for i in range(len(user_db)):

                    if user_db[i][0] == user:

                        userTaken = True
                        break

                if userTaken == False:
                    
                    if REG_KEY == True:

                        if dt.check_reg_key(key) == "200":

                            dt.add_user(user, passw)
                            conn.send(enc(bytes("reg200", FORMAT)))
                            continue

                        else:

                            conn.send(enc(bytes("reg403", FORMAT)))
                            continue

                    else:

                        dt.add_user(user, passw)
                        conn.send(enc(bytes("reg200", FORMAT)))
                        continue

                else:

                    conn.send(enc(bytes("user-taken", FORMAT)))
                    continue
            
            # Přihlášení
            elif request[0] == "log":

                user, passw = request[1:3]

                dt.c.execute("SELECT * FROM clients WHERE username=:user AND password=:pass", {"user": user, "pass": passw})
                db_output = dt.c.fetchall()

                if len(db_output) == 1:

                    conn.send(enc(bytes("login200", FORMAT)))
                    name = user
                    CLIENTS.append([name, conn, pu_key_client])
                    name = str()
                    break

                else:

                    conn.send(enc(bytes("login403", FORMAT)))
                    continue
            
            else: print("Něco gone wrong"); continue

    def client_work(conn, address, pukey, name):

        global CLIENTS
        global ROOMS
        conaddrpukey = [name, conn, pu_key_client]

        print("Aktivnich uživatelů: " + str(threading.activeCount() - 2))

        def delete_name(name):

            for i in range(len(CLIENTS)):

                if CLIENTS[i][0] == name:

                    CLIENTS.remove(CLIENTS[i])

        def chatting(clients, room):

            def broadcast(msg):

                for i in clients:
                    if conn != i[1]:

                        while True:

                            part = msg[:50]
                            if part == "": break
                            msg = msg.replace(part, "")
                            i[1].send(ae.Enc(ae.encryptor(i[2])).enc(bytes(part, FORMAT)))

            print(f"[SYSTEM] \"{name}\" () connected.")
            broadcast(f"[SYSTEM] \"{name}\" connected./END#")

            conn.send(enc(bytes("conn/END#", FORMAT)))

            while True:

                msg = str()

                while True:

                    try:

                        msg_part = dec(conn.recv(128)).decode(FORMAT)

                    except:

                        print(f"[SYSTEM] \"{name}\" () disconnected.")
                        broadcast(f"[SYSTEM] \"{name}\" disconnected./END#")
                        clients.remove(conaddrpukey)
                        delete_name(name)
                        print("Aktivnich uživatelů: " + str(threading.activeCount() - 2))
                        sys.exit()

                    msg += msg_part
                    if "/END#" in msg: break

                if "!active-users" in msg:

                    jmena = str()
                    NAMES = [i[0] for i in clients]
                    NAMES.sort()

                    for i in NAMES: jmena += f"{i}, "

                    msg = f"Momentálně je aktivních {len(NAMES)} uživatelů.\nJména: {jmena}./END#"

                    while True:

                        part = chatrooms_list[:50]
                        if part == "": break
                        chatrooms_list = chatrooms_list.replace(part, "")
                        conn.send(enc(bytes(part, FORMAT)))
                
                elif "!quit" in msg:
                    
                    print(f"[SYSTEM] \"{name}\"  disconnected.")
                    broadcast(f"[SYSTEM] \"{name}\" disconnected./END#")
                    clients.remove(conaddrpukey)
                    delete_name(name)
                    break

                else:

                    broadcast(msg)
        
        while True:

            try:

                chatrooms_list = f"info%Jste připojeni k serveru.\nJméno: {name}\nChatroomy:\n\n"

                for room in ROOMS:

                    print(room[2])

                    if room[2] == "": status = "*OPEN*"
                    else: status = "*PASSWORD*"

                    chatrooms_list += f"    {room[0]} - {status}\n"# - {room[1]} *{room[2]}*\n"
                
                chatrooms_list += "\nCommandy:\n!create-room;<název roomky>\n!remove-room;<název roomky>\n\nZadejte název roomky:/END#"

                while True:

                    part = chatrooms_list[:50]
                    if part == "": break
                    chatrooms_list = chatrooms_list.replace(part, "")
                    conn.send(enc(bytes(part, FORMAT)))

                room = dec(conn.recv(128)).decode(FORMAT)
                print(name)
                room = room.replace(f"{name}: ", "")
                room = room.replace("/END#", "")

                print(ROOMS)

                if room.startswith("!create-room"):

                    if len(ROOMS) < 10:

                        roomm = room.split(";")

                        ROOMS.append([roomm[1], [], "", name]) #název, uživatelé, heslo, zakladatel
                        
                        #roomm[1] = roomm[1].replace("/END#", "")
                        conn.send(enc(bytes("create-room200/END#", FORMAT)))

                        continue

                    else:

                        conn.send(enc(bytes("create-room403/END#", FORMAT)))

                        continue

                if room.startswith("!remove-room"):
                    
                    print("yeetus deletus")
                    roomm = room.split(";")
                    roomm.append(name)

                    for i in ROOMS:

                        if roomm[1] == i[0]:

                            if roomm[2] == i[3]:

                                ROOMS.remove(i)

                                for ii in i[1]:

                                    print(ii)

                                    ii[1].send(ae.Enc(ae.encryptor(ii[2])).enc(bytes("[SYSTEM] Tato roomka byla odstraněna a již není k dispozici v seznamu chatroomek./END#", FORMAT)))

                                conn.send(enc(bytes("remove-room200/END#", FORMAT)))
                                break

                            else:

                                conn.send(enc(bytes("remove-room403/END#", FORMAT)))
                                break

                    continue

                elif room.startswith("!refresh"): continue

                elif room.startswith("!quit"): conn.send(enc(bytes("quit-server/END#", FORMAT)))

                find_room = False

                for i in ROOMS:

                    if i[0] == room:

                        clients = i[1]
                        i[1].append(conaddrpukey)
                        find_room = True
                        chatting(clients, room)
                        break
                
                if find_room == False: conn.send(enc(bytes("invalid-room/END#", FORMAT)))

            except (ConnectionResetError, ConnectionAbortedError):

                delete_name(name)
                print("Aktivnich uživatelů: " + str(threading.activeCount() - 2))
                sys.exit()

    try: Thread(target=client_work, args=(conn, address, pu_key_client, name)).start()
    except NameError: pass
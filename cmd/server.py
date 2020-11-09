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

NAMES = []
ROOMS = []
CLIENTS = {}

IP = sett["IP"]
PORT = sett["PORT"]
SOCKET = (IP, PORT)
FORMAT = sett["FORMAT"]
OPEN = sett["OPEN"]
REG_KEY = sett["REG_KEY"]
NAME = sett["NAME"]
DESCRIPTION = sett["DESCRIPTION"]

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(SOCKET)
server.listen()

print(f"[STAV] Server byl spuštěn.\n\nIP: {IP}\nPORT: {PORT}\nFORMAT: {FORMAT}\nOPEN: {OPEN}\nNAME: {NAME}\nDESCRIPTION: {DESCRIPTION}")

while True:

    # Přijímá připojení od klienta
    conn, address = server.accept()
    
    # Odeslání informací o serveru
    conn.send(bytes(f"{OPEN};{REG_KEY};{NAME};{DESCRIPTION}", FORMAT))

    # Nezabezpečený server
    if OPEN == True:

        try: name = conn.recv(1024).decode(FORMAT)
        except: continue

        if name not in NAMES:

            conn.send(bytes("200", FORMAT))
            NAMES.append(name)
        
        else:

            conn.send(bytes("403", FORMAT))

    # Zabezpečený server, ke kterému je nutné mít účet
    else:

        while True:

            try: yes = conn.recv(1024).decode(FORMAT)
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
                            conn.send(bytes("reg200", FORMAT))
                            continue

                        else:

                            conn.send(bytes("reg403", FORMAT))
                            continue

                    else:

                        dt.add_user(user, passw)
                        conn.send(bytes("reg200", FORMAT))
                        continue

                else:

                    conn.send(bytes("user-taken", FORMAT))
                    continue
            
            # Přihlášení
            elif request[0] == "log":

                user, passw = request[1:3]

                dt.c.execute("SELECT * FROM clients WHERE username=:user AND password=:pass", {"user": user, "pass": passw})
                db_output = dt.c.fetchall()

                if len(db_output) == 1:

                    conn.send(bytes("login200", FORMAT))
                    name = user
                    NAMES.append(name)
                    break

                else:

                    conn.send(bytes("login403", FORMAT))
                    continue
            
            else: print("Něco gone wrong"); continue
        
    def client_work(conn, address, name, ROOMS):

        global NAMES

        print("Aktivnich uživatelů: " + str(threading.activeCount() - 2))

        def chatting(clients, room):

                def broadcast(msg, clients):

                    for i in clients:
                        if conn != i:
                            i.send(bytes(msg, FORMAT))

                print(f"[SYSTEM] \"{name}\" () connected./END#")
                broadcast(f"[SYSTEM] \"{name}\" connected./END#", clients)

                conn.send(bytes("conn/END#", FORMAT))

                while True:

                    msg = str()

                    while True:

                        try:

                            msg_part = conn.recv(64).decode(FORMAT)

                        except:

                            print(f"[SYSTEM] \"{name}\" () disconnected./END#")
                            broadcast(f"[SYSTEM] \"{name}\" disconnected./END#", clients)
                            clients.remove(conn)
                            NAMES.remove(name)
                            print("Aktivnich uživatelů: " + str(threading.activeCount() - 2))
                            sys.exit()

                        msg += msg_part
                        if "/END#" in msg: break

                    #print(msg)

                    if "!active-users/END#" in msg:

                        jmena = str()
                        NAMES.sort()

                        for i in NAMES: jmena += f"{i}, "

                        conn.send(bytes(f"Momentálně je aktivních {len(NAMES)} uživatelů.\nJména: {jmena}./END#", FORMAT))
                    
                    if "!quit/END#" in msg:
                        
                        print(f"[SYSTEM] \"{name}\"  disconnected./END#")
                        broadcast(f"[SYSTEM] \"{name}\" disconnected./END#", clients)
                        clients.remove(conn)
                        NAMES.remove(name)
                        #conn.send(bytes("disconn/END#", FORMAT))
                        break

                    else:

                        broadcast(msg, clients)
        
        while True:

            try:

                chatrooms_list = f"info%Jste připojeni k serveru.\nJméno: {name}\nChatroomy:\n\n"

                for room in ROOMS:

                    chatrooms_list += f"    {room[0]}\n"# - {room[1]} *{room[2]}*\n"
                
                chatrooms_list += "\nCommandy:\n!create-room;<název roomky>\n!remove-room;<název roomky>\n\nZadejte název roomky:"
                chatrooms_list += "/END#"

                conn.send(bytes(chatrooms_list, FORMAT))

                room = conn.recv(64).decode(FORMAT)
                room = room.replace("/END#", "")
                room = room.replace(f"{name}: ", "")

                if room.startswith("!create-room"):

                    if len(ROOMS) < 10:

                        roomm = room.split(";")

                        ROOMS.append([roomm[1], [], name])

                        conn.send(bytes("create-room200/END#", FORMAT))

                        continue

                    else:

                        conn.send(bytes("create-room403/END#", FORMAT))

                        continue

                if room.startswith("!remove-room"):

                    roomm = room.split(";")
                    roomm.append(name)

                    for i in ROOMS:

                        if roomm[1] == i[0]:

                            if roomm[2] == i[2]:

                                ROOMS.remove(i)

                                for ii in i[1]:

                                    ii.send(bytes("[SYSTEM] Tato roomka byla odstraněna a již není k dispozici v seznamu chatroomek./END#", FORMAT))

                                conn.send(bytes("remove-room200/END#", FORMAT))
                                break

                            else:

                                conn.send(bytes("remove-room403/END#", FORMAT))
                                break

                    continue

                elif room.startswith("!refresh"): continue

                elif room == "!quit": conn.send(bytes("quit-server/END#", FORMAT))

                find_room = False

                for i in ROOMS:

                    if i[0] == room:

                        clients = i[1]
                        i[1].append(conn)
                        find_room = True
                        chatting(clients, room)
                        break
                
                if find_room == False: conn.send(bytes("invalid-room/END#", FORMAT))

            except ConnectionResetError:

                NAMES.remove(name)
                print("Aktivnich uživatelů: " + str(threading.activeCount() - 2))
                sys.exit()

    try: Thread(target=client_work, args=(conn, address, name, ROOMS)).start()
    except NameError: pass
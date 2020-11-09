import socket
from threading import Thread
import os
import sys
import time
from getpass import getpass
import asymencrypt as ae

clr = lambda: os.system("cls")
FORMAT = "utf-8"

logged = False
quit_server = True

while True:

    if quit_server == True:

        if logged == True: break
        quit_server = False

        clr()
        print("Python - Chat")
        CONNECT = "localhost"#input("Zadejte IP: ")
        PORT = 8080#int(input("Zadejte port: "))
        clr()

        if CONNECT not in "123456789.": IP = socket.gethostbyname(CONNECT)

        else: IP = CONNECT

        try:

            SOCKET = (IP, PORT)
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(SOCKET)

        except:

            print("K serveru nebylo možné se připojit.")
            input("\n\nStiskněte ENTER pro pokračování...")
            clr()
            quit_server = True
            continue

        else:

            # Získání informací ze strany serveru


            print("Připojení k serveru bylo úspěšné.\n")

            info = client.recv(1024).decode(FORMAT)
            info = info.split(";")

            if info[0] == "True":

                while True:

                    print(f"Připojili jste se k otevřenému serveru.\nIP: {CONNECT}\nNázev: {info[2]}\nPopisek: {info[3]}\n\n")

                    name = input("Zadejte jméno: ")
                    clr()

                    client.send(bytes(name, FORMAT))
                    response = client.recv(1024).decode(FORMAT)

                    if response != "200":
                        
                        print("Toto jméno už je zabrané.")
                        input()
                        clr()
                        continue
                
                break
            
            else:

                def register():

                    request = "reg"
                    name = input("Zadejte jméno: ")
                    password = input("Zadejte heslo: ")
                    if info[1] == "True": reg_key = input("Zadejte registrační klíč: ")
                    else: reg_key = "None"
                    clr()

                    client.send(bytes(f"{request};{name};{password};{reg_key}", FORMAT))

                    auth = client.recv(1024).decode(FORMAT)

                    if auth == "reg200":

                        clr()
                        print("Registrace proběhla úspěšně.\nPočkejte 2 sekundy.")
                        time.sleep(2)
                        clr()

                    elif auth == "reg403":

                        clr()
                        print("Registrace se nezdařila. Zadali jste buď špatný klíc nebo je zadané jméno zabrané.\nPočkejte 6 sekundy.")
                        time.sleep(6)
                        clr()

                    elif auth == "user-taken":

                        clr()
                        print("Uživatelské jméno je zabrané.\nPočkejte 2 sekundy.")
                        time.sleep(2)
                        clr()

                def login():

                    request = "log"
                    name = input("Zadejte jméno: ")
                    password = input("Zadejte heslo: ")
                    clr()

                    client.send(bytes(f"{request};{name};{password}", FORMAT))

                    auth = client.recv(1024).decode(FORMAT)

                    if auth == "login200":

                        return name

                    else:
                        
                        print("Zadali jste špatné přihlašovací údaje.")
                        time.sleep(2)
                        clr()
                        return "403"

                while True:

                    print(f"Připojili jste se k serveru vyžadující autorizaci.\nIP: {CONNECT}\nNázev: {info[2]}\nPopisek: {info[3]}\n\n")

                    print("1. Přihlášení\n2. Registrace\n")
                    volba = input("Zadejte možnost: ")

                    if volba == "1":
                        
                        clr()
                        name = login()

                        if name != "403": logged = True; break
                        else: continue

                    elif volba == "2":
                        
                        clr()
                        register()

        # Modul přijímající stavové zprávy a zprávy od ostatních uživatelů
        def rcv():

                global quit_server
                global logged

                while True:

                    msg = str()

                    while True:

                        try: msg_part = client.recv(64).decode(FORMAT)
                        except ConnectionResetError:
                            
                            print("Připojení k serveru bylo ztraceno.\nStiskněte ENTER pro pokračování.")
                            quit_server = True
                            logged = False
                            return
                        
                        msg += msg_part
                        if "/END#" in msg: msg = msg.replace("/END#", ""); break
    
                    if msg == "conn":

                        clr()
                        print("Jste připojeni v chatu.\n")

                    elif msg == "quit-server":

                        print("Opustili jste tento server.\nStiskněte ENTER pro pokračování.")
                        quit_server = True
                        sys.exit()

                    elif msg == "create-room200":

                        clr()
                        print("Roomka byla úspěšně vytvořena.\nPočkejte 2 sekundy.")
                        time.sleep(2)

                    elif msg == "create-room403":

                        clr()
                        print("Bylo dosáhnuto limitu roomek.\nPočkejte 2 sekundy.")
                        time.sleep(2)

                    elif msg == "remove-room200":

                        clr()
                        print("Roomka byla odebrána.\nPočkejte 2 sekundy.")
                        time.sleep(2)

                    elif msg == "remove-room403":
                        
                        clr()
                        print("Roomka nebyla odebrána, protože nejste její zakladatel.\nPočkejte 2 sekundy.")
                        time.sleep(2)

                    elif msg == "invalid-room":

                        clr()
                        print("Zadali jste název neplatné roomky.\nPočkejte 2 sekundy.")
                        time.sleep(2)

                    elif msg.startswith("info"):

                        msg = msg.split("%")
                        clr()
                        print(msg[1])
                        continue

                    else:
                        
                        print(msg)

    Thread(target=rcv).start()
        
    # Modul odesílajicí zprávy
    while True:

        if quit_server == True: break

        msg_up = input()

        for i in msg_up.split():

            if i.startswith(":") and i.endswith(":"):

                i = i[1:len(i)-1]
                print(f"Pytle = {i}")
                
        if msg_up == "": continue
        msg_up += "/END#"
        msg_up = f"{name}: {msg_up}"
        client.send(bytes(msg_up, FORMAT))
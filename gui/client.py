import tkinter as tk
from tkinter import messagebox as mb
import socket
import asymencrypt as ae
import threading
import pickle
from PIL import Image, ImageTk
import os
import checksumdir
import hashlib

IPs = []

class Login:
    def connect(self, event=str()):
        if self.ip_entry.get() not in IPs:
            def connect():
                try:
                    def login(event=str()):
                        name = jmeno.get()

                        if len(name) > 32:
                            mb.showerror(message="Moc dlouhé jméno.")

                        sened(["log", name, heslo.get()])

                        resp = recev()

                        if resp == "#conn-name-0":
                            mb.showerror(message="Jméno je již zabrané.")                       
                        elif resp == "#conn-0":
                            mb.showerror(message="Zadali jste špatné uživatelské jméno nebo heslo.")
                        elif resp == "#conn-1":                               
                            IPs.append(self.ip_entry.get())
                            root.destroy()
                            Chat(sened, recev, self.conn, self.ip_entry.get(),
                                name, name_server, desc, RSA, dec, enc)

                    def register():
                        def send_reg(event=None):
                            sened([
                                "reg",
                                jmeno.get(),
                                heslo.get(),
                                reg_key.get()
                                ])

                            resp = recev()

                            if resp == "#username-taken":
                                mb.showerror(message="Jméno je již zabrané.")
                            elif resp == "#reg-1":
                                mb.showinfo(message="Registrace byla úspěšná.")
                                reg_root.destroy()
                            elif resp == "#reg-0-key":
                                mb.showerror(
                                    message="Zadaný reg. klíč je neplatný.")

                        reg_root = tk.Toplevel(root)

                        reg_root.bind("<Return>", send_reg)

                        tk.Label(reg_root, text="Registrace",
                            font="Arial 20").grid(columnspan=2)

                        tk.Label(reg_root, text="Jméno").grid(row=1, column=0)
                        jmeno = tk.Entry(reg_root)
                        jmeno.grid(row=1, column=1)

                        tk.Label(reg_root, text="Heslo").grid(row=2, column=0)
                        heslo = tk.Entry(reg_root, show="*")
                        heslo.grid(row=2, column=1)

                        reg_key = tk.StringVar(reg_root, "0")

                        if REG_KEY == True:
                            tk.Label(reg_root,
                                text="Reg. klíč").grid(row=3, column=0)
                            reg_key = tk.Entry(reg_root, show="*")
                            reg_key.grid(row=3, column=1)

                        tk.Button(reg_root, text="Připojit", font="Arial 15",
                            command=send_reg).grid(row=4, columnspan=3,
                            sticky="wse")

                        reg_root.mainloop()

                    IP, PORT = self.ip_entry.get().split(":")
                    IP = socket.gethostbyname(IP)
                    self.conn = socket.socket(
                        socket.AF_INET,socket.SOCK_STREAM)
                    self.conn.connect((IP, int(PORT)))

                    status_var.set("Připojeno")

                    name_server, desc, auth, RSA, REG_KEY = pickle.loads(
                        self.conn.recv(1024))
      
                    if RSA == True:
                        self.pr_key_client = ae.prkey_generate(1024)
                        pu_key_client = ae.pukey(self.pr_key_client)

                        self.conn.send(pu_key_client.export_key())

                        pu_key_ser = ae.RSA.import_key(self.conn.recv(1024))

                        encryptor = ae.encryptor(pu_key_ser)
                        enc = ae.Enc(encryptor).enc
                        
                        decryptor = ae.decryptor(self.pr_key_client)
                        dec = ae.Dec(decryptor).dec

                        def sened(data):
                            text = pickle.dumps(data) + b"/END#"

                            while True:
                                if text == b"": break
                                self.conn.sendall(enc(text[:50]))
                                text = text[50:]
                    
                        def recev():
                            try:
                                text = bytes()
                    
                                while True:
                                    if text.endswith(b"/END#"): break
                                    text += dec(self.conn.recv(128))
                                
                                return pickle.loads(text[:-4])                            
                            except ConnectionAbortedError: pass

                    else:
                        enc, dec = None, None

                        def sened(data):
                            text = pickle.dumps(data) + b"/END#"

                            while True:
                                if text == b"": break
                                self.conn.sendall(text[:50])
                                text = text[50:]

                        def recev():
                            try:
                                text = bytes()
                    
                                while True:
                                    if text.endswith(b"/END#"): break
                                    text += self.conn.recv(128)

                                return pickle.loads(text[:-4])
                            except ConnectionAbortedError: pass

                    status.destroy()

                    tk.Label(root, text=f"Jméno: {name_server}", bg="#474747",
                        fg="#ffffff").grid(columnspan=2)
                    tk.Label(root, text=f"Popis: {desc}", bg="#474747",
                        fg="#ffffff").grid(columnspan=2)
                    tk.Label(
                        root,
                        text=f"Zabezpečení: " +
                        "Otevřené" if auth == "O" else "Zaheslované",
                        bg="#474747", fg="#ffffff"
                        ).grid(columnspan=2)
                    tk.Label(root,
                        text=f"Šifrováno: " +
                        "Šifrováno" if RSA == True else "Nešifrováno",
                        bg="#474747", fg="#ffffff"
                        ).grid(columnspan=2)

                    tk.Frame(root, height=20,
                        bg="#474747").grid(row=3, column=0)

                    if auth == "O":
                        root.bind("<Return>", login)

                        tk.Label(root, text="Jméno: ", bg="#474747",
                            fg="#ffffff").grid(row=4, column=0)
                        jmeno = tk.Entry(root, bg="#474747", fg="#ffffff")
                        jmeno.grid(row=4, column=1)
                        jmeno.focus()

                        heslo = tk.StringVar(root, "#nopass")

                        tk.Frame(root, height=10, bg="#474747").grid(row=5)

                        tk.Button(
                            root,
                            text="Připojit",
                            font="Arial 15",
                            command=login,
                            bg="#474747",
                            fg="#ffffff"
                            ).grid(row=6, columnspan=3, sticky="wse")

                        root.focus_set()
                    
                    elif auth == "P":
                        root.bind("<Return>", login)

                        tk.Label(root, text="Jméno: ", bg="#474747",
                            fg="#ffffff").grid(row=4, column=0)
                        jmeno = tk.Entry(root)
                        jmeno.grid(row=4, column=1)

                        tk.Label(root, text="Heslo: ", bg="#474747",
                            fg="#ffffff").grid(row=5, column=0)
                        heslo = tk.Entry(root, show="*")
                        heslo.grid(row=5, column=1)

                        tk.Frame(root, height=10, bg="#474747").grid(row=6)

                        tk.Button(
                            root,
                            text="Připojit",
                            font="Arial 15",
                            command=login,
                            bg="#474747",
                            fg="#ffffff"
                            ).grid(row=7, columnspan=3, sticky="wse")

                        tk.Button(
                            root,
                            text="Registrovat",
                            font="Arial 10",
                            command=register,
                            bg="#474747",
                            fg="#ffffff"
                            ).grid(row=8, columnspan=3, sticky="wse")

                        root.focus_set()
                
                except:                   
                    mb.showerror(message="Nebylo možné se připojit k serveru.")
                    root.destroy()

            root = tk.Toplevel(self.root)
            root.config(bg="#474747")

            status_var = tk.StringVar(root)
            status_var.set("Připojování")

            status = tk.Label(root, textvariable=status_var, pady=10, padx=10,
                font="Arial 15", bg="#474747", fg="#ffffff")
            status.grid(row=0, column=0)

            screen_width = int(root.winfo_screenwidth()/2.1)
            screen_height = int(root.winfo_screenheight()/3)

            root.geometry(f"+{screen_width}+{screen_height}")

            root.after(100, connect)

            root.mainloop()
        
        else: mb.showerror(message="Již jste připojen k serveru.")

    def __init__(self):       
        self.root = tk.Tk()
        self.root.config(bg="#474747")

        tk.Label(self.root, text="Chat", font="Arial 30", bg="#474747",
            fg="#ffffff").grid(row=0, column=0, columnspan=3)

        tk.Frame(self.root, height=10,
            bg="#474747").grid(row=2, column=0, columnspan=3)

        tk.Label(self.root, text="IP: ", width=5, anchor="w", bg="#474747",
            fg="#ffffff").grid(row=3, column=0)
        self.ip_entry = tk.Entry(self.root, bg="#474747", fg="#ffffff")
        self.ip_entry.grid(row=3, column=1)
        self.ip_entry.insert("end", "localhost:10498")
        self.ip_entry.focus()

        tk.Button(
            self.root,
            text="Připojit",
            font="Arial 14",
            command=self.connect,
            bg="#474747",
            fg="#ffffff"
            ).grid(row=5, column=0, columnspan=3, sticky="we")
        self.root.bind("<Return>", self.connect)

        for i in range(5): self.root.grid_rowconfigure(i, weight=1)
        
        for i in range(2): self.root.grid_columnconfigure(i, weight=1)

        self.screen_width = int(self.root.winfo_screenwidth()/2.2)
        self.screen_height = int(self.root.winfo_screenheight()/2.9)

        self.root.geometry(f"+{self.screen_width}+{self.screen_height}")

        #self.root.resizable(False, False)
        self.root.mainloop()

class Chat:

    def close(self):
        self.kill = True
        IPs.remove(self.ip)
        self.conn.close()
        self.chat.destroy()

    def delete_chat(self):
        for i in self.messages: i.destroy()

    def join_room(self, name, passw=None):        
        if passw == None:            
            self.sened(["join-room", name])
            self.coord = 0

    def remove_room(self, name): self.sened(["remove-room", name, self.name])
    
    def create_room(self):
        def send():
            self.sened(
                ["create-room",
                roomka.get(),
                heslo_var.get(),
                heslo_e.get(),
                self.name]
                )
            root.destroy()

        def check_def():
            if heslo_var.get() == 0: heslo_e.grid_forget()
            else: heslo_e.grid(row=2, column=0, columnspan=2)

        root = tk.Toplevel(self.chat)

        tk.Label(root, text="Název roomky:").grid(row=0, column=0)
        roomka = tk.Entry(root)
        roomka.grid(row=0, column=1)

        heslo_var = tk.IntVar(root)
        heslo_ch = tk.Checkbutton(root, text="Zaheslovaná", command=check_def,
            variable=heslo_var)
        heslo_ch.grid(row=1, column=0)

        heslo_e = tk.Entry(root)

        send_btn = tk.Button(root, text="Vytvořit roomku", command=send)
        send_btn.grid(row=3, column=0)

    def recv_modul(self):
        self.messages = []

        def refresh_room(typ, data):
            def join_room(i):
                if self.ROOMS[i][1] == 1:
                    root = tk.Toplevel(self.chat)

                    heslo_l = tk.Label(root, text="Zadejte heslo: ")
                    heslo_l.grid(column=0, row=0)
                
                else: self.join_room(self.ROOMS[i][0])

            if typ == "init-room": self.ROOMS = data
            elif typ == "add-room": self.ROOMS.append(data)   
            elif typ == "rem-room": self.ROOMS.remove(data)

            self.room_list_c.delete("all")

            try: self.rooms.destroy()
            except AttributeError: pass

            print("nějaký roomky", self.ROOMS)

            self.rooms = tk.Frame(self.room_list_c, bg="#373737")

            for i in range(len(self.ROOMS)):
                nazev = tk.Label(
                    self.rooms,
                    text=f"{self.ROOMS[i][0]}, {self.ROOMS[i][1]}",
                    fg="#ffffff",
                    bg="#676767"
                    )
                nazev.grid(row=i, column=0, sticky="w")
                nazev.bind("<Button-1>", lambda event, i=i: join_room(i))

                if self.ROOMS[i][2] == self.name:
                    remove_btn = tk.Button(
                        self.rooms,
                        text="Odstranit",
                        command=lambda i=i: self.remove_room(self.ROOMS[i][0])
                        )
                    remove_btn.grid(row=i, column=1)
                
            self.room_list_c.create_window((0, 0), window=self.rooms,
                anchor="nw")
            self.chat.update()
            self.room_list_c.config(scrollregion=self.room_list_c.bbox("all"))

        def refresh_client(typ, data):
            if typ == "init-cl": self.CLIENTS = data
            elif typ == "add-cl": self.CLIENTS.append(data)
            elif typ == "rem-cl":
                print("pičo data", data)
                self.CLIENTS.remove(data)

            self.clients_c.delete("all")

            try: self.clients_frame.destroy(); print("ano")
            except AttributeError: pass

            self.clients_frame = tk.Frame(self.clients_c, bg="#373737")

            for i in range(len(self.CLIENTS)):
                nazev = tk.Label(self.clients_frame, text=self.CLIENTS[i],
                    fg="#ffffff", bg="#676767")
                nazev.grid(row=i, column=0, sticky="w")
                
            self.clients_c.create_window((0, 0), window=self.clients_frame,
                anchor="nw")
            self.chat.update()
            self.clients_c.config(scrollregion=self.clients_c.bbox("all"))

        self.coord = 0
        last_name = str()

        folderhash = hashlib.md5(
            bytes(self.name_server, encoding="utf-8")
            ).hexdigest()
        self.emotes = {}
        self.msg_msg = tk.Text(self.chat)

        def emote_gen():
            print("gaysex")

            if os.path.exists("cl_emotes/" + folderhash): print("funguje")
            else: os.makedirs("cl_emotes/" + folderhash)

            self.sened(
                ["emotes",
                checksumdir.dirhash(os.getcwd() + "/cl_emotes/" + folderhash)
                ])

            for i in [i for i in os.listdir("cl_emotes/" + folderhash)]:
                now_emote = i.split(".")[0]
                if i.split(".")[1] not in ["png", "jpg", "gif"]: continue
                self.emotes[now_emote] = Image.open(f"cl_emotes/{folderhash}/" + i)
                self.emotes[now_emote] = self.emotes[now_emote].resize((16, 16))
                self.emotes[now_emote] = ImageTk.PhotoImage(
                    master=self.msg_msg,
                    image=self.emotes[now_emote]
                    )

        emote_gen()

        while self.kill == False:
            try:
                text = self.recev()
                print(text[0])

                last = True if text[0] == last_name else False

                msg = tk.Frame(self.msgbox_c, bg="#373737")
                self.messages.append(msg)

                if text[0] == "ROOMS":
                    refresh_room(text[1], text[2]); continue
                elif text[0] == "CLIENTS":
                    refresh_client(text[1], text[2]); continue
                elif text[0] == "joined-room":     
                    self.delete_chat()
                    self.coord = 0
                    self.room_text.config(text=text[1])
                    continue                   
                elif text[0] == "semotes":
                    self.emote_root = tk.Toplevel(self.chat)
                    self.emote_root.focus_set()
                    self.emote_root.grab_set()

                    nadpis = tk.Label(self.emote_root, text="Stahování emotů...")
                    nadpis.pack()

                    continue
                elif text[0] == "eemotes":
                    emote_gen()

                    self.emote_root.grab_release()
                    self.emote_root.destroy()
                    self.chat.focus_set()

                    continue
                elif text[0] == "emote":
                    with open(f"cl_emotes/{folderhash}/{text[1][0]}", "wb") as soubor: soubor.write(text[1][1])

                    continue

                if last == True:
                    self.msg_msg = tk.Text(msg, font="Arial 12", width=44, bg="#373737", fg="#ffffff", wrap="word", relief="flat")
                    self.msg_msg.grid(row=1, column=0, sticky="wn")
                    
                    for i in text[1].split():
                        if i in self.emotes: self.msg_msg.image_create("end", image=self.emotes[i])
                        else: self.msg_msg.insert("end", i + " ")

                    self.msg_msg.config(state="disabled")
                    msg.update()
                    self.msg_msg.config(height=int(self.msg_msg.count(1.0, 'end', 'displaylines')[0]))
                else:
                    msg_author = tk.Label(msg, text=f"{text[0]} {text[2]}", font="Arial 13", bg="#373737", fg="#ffffff")
                    msg_author.grid(row=0, column=0, sticky="wn")

                    self.msg_msg = tk.Text(msg, font="Arial 12", width=44, bg="#373737", fg="#ffffff", wrap="word", relief="flat")
                    self.msg_msg.grid(row=1, column=0, sticky="wn")
                    
                    for i in text[1].split():
                        if i in self.emotes: self.msg_msg.image_create("end", image=self.emotes[i])
                        else: self.msg_msg.insert("end", i + " ")                    

                    self.msg_msg.config(state="disabled")
                    msg.update()
                    self.msg_msg.config(height=int(self.msg_msg.count(1.0, 'end', 'displaylines')[0]))

                    last_name = text[0]

                self.msgbox_c.create_window((0, self.coord), window=msg, anchor="nw")
                self.chat.update()
                self.msgbox_c.config(scrollregion=self.msgbox_c.bbox("all"))
                self.msgbox_c.yview_moveto(1.0)

                print(last)
                if last == True: self.coord += msg.winfo_height()
                else: self.coord += msg.winfo_height() + 4
            
            except ConnectionResetError:
                mb.showerror(message="Připojení k serveru bylo ztraceno.")
                self.close()
                return

        else: return

    def send(self, event=None, send=str()):
        if send == "send":
            if str(event.widget) == ".!text":               
                text = self.textos.get(1.0, "end")
                self.textos.delete(1.0, "end")
                text = text.replace("\n\n", "")

                if text == "": return

                self.sened(text)

                self.textos.delete(1.0, "end")
        
        elif send == "enter":
            if str(event.widget) == ".!text":
                text = self.textos.get(1.0, "end")
                text = text.replace("\n\n", "")

                if text == "": self.textos.delete(1.0, "end")

    def __init__(self, sened, recev, conn, ip, name, name_server, desc, RSA,
        dec, enc):

        self.sened = sened
        self.recev = recev
        self.kill = False
        self.conn = conn
        self.ip = ip
        self.name = name
        self.name_server = name_server
        self.desc = desc
        self.RSA = RSA
        self.dec = dec
        self.enc = enc

        self.chat = tk.Tk()
        self.chat.config(bg="#474747")

        tk.Label(self.chat, text="Chat", font="Arial 20", bg="#474747",
            fg="#ffffff").grid(row=0, column=0, columnspan=2)

        server_text = f"Server: {self.name_server}\nPopisek: {self.desc}\nŠifrování:" + "Šifrováno " if RSA == True else "Nešifrováno" + f"\n\nJméno: {self.name}"

        self.server_info = tk.Message(self.chat, text=server_text, width=200,
            bg="#474747", fg="#ffffff")
        self.server_info.grid(row=1, column=0, sticky="w")

        self.create_room_b = tk.Button(self.chat, text="Vytvořit roomku",
            command=self.create_room)
        self.create_room_b.grid(row=2, column=0, sticky="ws")

        self.room_list = tk.Frame(self.chat, width=300, height=200,
            bg="#777777", highlightbackground="#474747")
        self.room_list.grid(row=3, column=0, rowspan=2, columnspan=2,
            sticky="w")
        self.room_list_c = tk.Canvas(self.room_list, width=300, height=200,
            bg="#777777", highlightbackground="#474747")
        self.room_list_c.grid(row=0, column=0)
        self.room_list_vs = tk.Scrollbar(self.room_list, orient="vertical",
            command=self.room_list_c.yview)
        self.room_list_vs.grid(row=0, column=1, sticky="ns")
        self.room_list_c.config(yscrollcommand=self.room_list_vs.set)

        self.room_text = tk.Label(self.chat, text="Nepřipojeno", fg="#ffffff",
            bg="#474747", font="Arial 15")
        self.room_text.grid(row=0, column=2, sticky="ws")

        self.msgbox = tk.Frame(self.chat, width=400, height=400, bg="#373737",
            highlightbackground="#474747")
        self.msgbox.grid(row=1, column=2, rowspan=3, sticky="w")
        self.msgbox_c = tk.Canvas(self.msgbox, width=400, height=400,
            bg="#373737", highlightbackground="#474747")
        self.msgbox_c.grid(row=0, column=0)
        self.msgbox_vs = tk.Scrollbar(self.msgbox, orient="vertical",
            command=self.msgbox_c.yview)
        self.msgbox_vs.grid(row=0, column=1, sticky="ns")
        self.msgbox_c.config(yscrollcommand=self.msgbox_vs.set)

        self.clients = tk.Frame(self.chat, width=200, height=460,
            bg="#676767", highlightbackground="#474747")
        self.clients.grid(row=1, column=3, rowspan=4, sticky="w")
        self.clients_c = tk.Canvas(self.clients, width=200, height=460,
            bg="#676767", highlightbackground="#474747")
        self.clients_c.grid(row=0, column=0)
        self.clients_vs = tk.Scrollbar(self.clients, orient="vertical",
            command=self.clients_c.yview)
        self.clients_vs.grid(row=0, column=1, sticky="ns")
        self.clients_c.config(yscrollcommand=self.clients_vs.set)

        self.textos = tk.Text(self.chat, height=3, width=10, bg="#474747",
            fg="#ffffff")
        self.textos.grid(row=4, column=2, sticky="wse")

        self.chat.bind("<Shift-Return>",
            func=lambda event: self.send(event, send="enter"))
        self.chat.bind("<Return>",
            func=lambda event: self.send(event, send="send"))

        self.recv_thread = threading.Thread(target=self.recv_modul)
        self.recv_thread.start()

        for i in range(3): self.chat.grid_rowconfigure(i, weight=1)
        
        for i in range(2): self.chat.grid_columnconfigure(i, weight=1)

        self.chat.protocol("WM_DELETE_WINDOW", self.close)
        self.chat.mainloop()

if __name__ == "__main__":
    Login()
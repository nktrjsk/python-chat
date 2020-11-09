import sqlite3 as sql
import random

con = sql.connect("databaze.db", check_same_thread=False)
c = con.cursor()

c.execute("CREATE TABLE IF NOT EXISTS clients (username text, password text)")
c.execute("CREATE TABLE IF NOT EXISTS chatrooms (name text, security integer, password text, creator text)")
c.execute("CREATE TABLE IF NOT EXISTS reg_keys (key text)")

def add_user(username, password):

    c.execute("INSERT INTO clients VALUES (:username, :password)", {"username": username, "password": password})
    con.commit()

def rem_user(username, password):

    c.execute("DELETE FROM clients WHERE username=:username, password=:password)", {"username": username, "password": password})
    con.commit()

def add_room(name, security, password, creator):

    c.execute("INSERT INTO chatrooms VALUES (:name, :security, :password, :creator)", {"name": name, "security": security, "password": password, "creator": creator})
    con.commit()

def check_reg_key(key):

    c.execute("SELECT * FROM reg_keys WHERE key=:key", {"key": key})
    db_output = c.fetchall()
    print(len(db_output))

    if len(db_output) == 1: 
        
        c.execute("DELETE FROM reg_keys WHERE key=:key", {"key": key})
        generate_reg_key()
        
        return "200"

    else: return "403"

def generate_reg_key():

    characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"

    def getRandom():

        key = str()
        
        for i in range(4):

            key_part = "".join(random.choice(characters) for i in range(4))
            
            if i != 3: key_part += "-"

            key += key_part

        return key

    key = getRandom()

    c.execute("INSERT INTO reg_keys VALUES (:key)", {"key": key})
    con.commit()


#add_user("ne", "ano")
#c.execute("DELETE FROM reg_keys")
#add_room("mickyho díra", "OPEN", None, "buzik")
#print(check_reg_key("piconice"))
#c.execute("INSERT INTO reg_keys VALUES (:key)", {"key": "piconice"})
#con.commit()

if __name__ == "__main__":

    while True:

        command = input("Zadejte command: ")

        if command.startswith("!ru"):

            command = command.split(";")

            c.execute("DELETE FROM clients WHERE username=:username", {"username": command[1]})
            con.commit()

        elif command == "!pu":

            c.execute("SELECT * FROM clients")
            db_output = c.fetchall()

            user_list = str("\n")

            for i in db_output:

                user_list += f"    {i[0]} {i[1]}\n"

            print(user_list)

        elif command.startswith("!cue"):

            command = command.split(";")

            c.execute("SELECT username FROM clients WHERE username=:username", {"username": command[1]})

            if len(c.fetchall()[0]) == 1:

                print("\nUživatel existuje.")

            else:

                print("\nUživatel neexistuje.")

        elif command == "!grk":

            c.execute("SELECT * FROM reg_keys")
            key = c.fetchone()

            print("\n     " + key[0] + "\n")
        
        """
        c.execute("SELECT * FROM clients")
        print(c.fetchall())
        c.execute("SELECT * FROM chatrooms")
        print(c.fetchall())
        c.execute("SELECT * FROM reg_keys")
        print(c.fetchall())
        """
import sqlite3
import time
import getpass

def check_login(username, password):
    conn = sqlite3.connect('database/login.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    user = cursor.fetchone()

    conn.close()

    if user:
        return True
    else:
        print("[Login Failed] Trying again.")
        time.sleep(2)
        return False
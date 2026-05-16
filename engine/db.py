import sqlite3

DB_PATH = r'C:\Users\KIIT\OneDrive\Desktop\APEX\APEX.db'

def searchDB(query):
    try:
        conn   = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT url FROM web_command WHERE LOWER(name) = ?', (query,))
        result = cursor.fetchone()
        if result:
            conn.close()
            return ('web', result[0])
        cursor.execute('SELECT path FROM sys_command WHERE LOWER(name) = ?', (query,))
        result = cursor.fetchone()
        if result:
            conn.close()
            return ('app', result[0])
        cursor.execute('SELECT url FROM web_command WHERE LOWER(name) LIKE ?', ('%' + query + '%',))
        result = cursor.fetchone()
        if result:
            conn.close()
            return ('web', result[0])
        cursor.execute('SELECT path FROM sys_command WHERE LOWER(name) LIKE ?', ('%' + query + '%',))
        result = cursor.fetchone()
        if result:
            conn.close()
            return ('app', result[0])
        conn.close()
    except Exception as e:
        print('[DB Error] ' + str(e))
    return (None, None)

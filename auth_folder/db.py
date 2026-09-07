import sqlite3
conn=sqlite3.connect('auth.db',check_same_thread=False)
cursor=conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT NOT NULL UNIQUE,
password TEXT NOT NULL)''')


def add_user(username,password):
    cursor.execute('INSERT INTO users(username,password) VALUES (?,?)',(username,password))
    conn.commit()
    # print('User added successfully')
def auth_user(username,password):
    cursor.execute('select * from users where username=? and password=?',(username,password))
    result=cursor.fetchone()
    if result:
        return True
    else:
        return False
    print('User authenticated successfully')


# try:
#     add_user('kumar','1234')
# except Exception as e:
#     print(e)

# try:
#     auth_user('kumar','1234')   
# except Exception as e:
#     print(e)
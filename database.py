#Database setup file
#Useful when setting up for first time

import sqlite3

conn = sqlite3.connect("/home/contactbook/website/storage.db")
c = conn.cursor()

#Create tables for users and books
c.execute("DROP TABLE IF EXISTS users;")
c.execute("""
CREATE TABLE IF NOT EXISTS users(
    id integer PRIMARY KEY,
    username text NOT NULL,
    password text NOT NULL,
    pnumber text NOT NULL
);
""")
c.execute("DROP TABLE IF EXISTS books;")
c.execute("""
CREATE TABLE IF NOT EXISTS books(
    id integer PRIMARY KEY,
    time integer NOT NULL,
    bookname text NOT NULL,
    username text NOT NULL,
    public text NOT NULL
);
""")

#Ensure that the tables are created
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
r = c.fetchall()
print(r)

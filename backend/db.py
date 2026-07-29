import mysql.connector

def get_db_connection():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234567787",        # put your MySQL password
        database="yoga_db"
    )
    return db

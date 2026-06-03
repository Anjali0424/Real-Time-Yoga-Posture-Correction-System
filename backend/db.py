import mysql.connector

def get_db_connection():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",        # put your MySQL password
        database="yoga_db"
    )
    return db

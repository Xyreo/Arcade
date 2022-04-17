import bcrypt, time
import mysql.connector as sql

db = sql.connect(
    user="project-work", password="mySQLpass", host="167.71.231.52", database="arcade"
)
cursor = db.cursor()

query = f"SELECT COUNT(8) from user where name='Prami'"
cursor.execute(query)
print(cursor.fetchall())

cursor.close()
db.close()

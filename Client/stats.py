import mysql.connector as msc

db = msc.connect(
    host="167.71.231.52",
    username="project-work",
    password="mySQLpass",
    database="arcade",
)
cursor = db.cursor()
cursor.execute("")
print(cursor.fetchall())
cursor.close()
db.close()

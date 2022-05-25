import csv

import mysql.connector as msc

db = msc.connect(
    host="167.71.231.52",
    username="project-work",
    password="mySQLpass",
    database="arcade",
)
cursor = db.cursor()

# opening the CSV file
with open("board_details.csv", mode="r") as file:
    # reading the CSV file
    csvFile = list(csv.reader(file))
    table = "monopoly_board_values"
    cursor.execute(
        f"create table if not exists {table} (property char(21), position int primary key, colour char(10), hex char(7), price int, rent int, rent_colour int,rent_house_1 int,rent_house_2 int,rent_house_3 int,rent_house_4 int,rent_hotel int,mortgage int,build_cost int)"
    )
    # displaying the contents of the CSV file
    try:
        for lines in csvFile[1:]:
            t = []
            for i in lines:
                if i:
                    try:
                        t.append(f"{int(i)}")
                    except:
                        t.append('"' + str(i) + '"')
                else:
                    t.append("NULL")
            s = ",".join(t)
            cursor.execute(f"insert into {table} values({s})")
        print("Table Created Successfully.")
    except:
        print("Table Already Exists.")
cursor.close()
db.commit()

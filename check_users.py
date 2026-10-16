import sqlite3

connection = sqlite3.connect("data/mumbai_safety.db")
cursor = connection.cursor()

cursor.execute("PRAGMA table_info(incident_report)")

columns = cursor.fetchall()

print("\nINCIDENT_REPORT COLUMNS")
print("---------------------------------------")

for column in columns:
    print(
        "Column:",
        column[1],
        "| Type:",
        column[2]
    )

connection.close()
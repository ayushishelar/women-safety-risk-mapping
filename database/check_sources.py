from mysql_connection import get_connection

connection = get_connection()

cursor = connection.cursor(
    dictionary=True
)

cursor.execute(
    "SELECT DATABASE() AS db"
)

print(
    "Python database:",
    cursor.fetchone()["db"]
)

cursor.execute("""
    SELECT
        source_id,
        source_name,
        source_type
    FROM data_source
""")

rows = cursor.fetchall()

print("\nData sources found by Python:")

for row in rows:

    print(
        row["source_id"],
        "|",
        repr(row["source_name"]),
        "|",
        row["source_type"]
    )

print(
    "\nTotal sources:",
    len(rows)
)

cursor.close()
connection.close()
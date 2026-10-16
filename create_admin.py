import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "data" / "mumbai_safety.db"

# Admin details
ADMIN_NAME = "Admin"
ADMIN_EMAIL = "admin@womensafety.com"
ADMIN_PASSWORD = "Admin@123"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# Check if admin already exists
cursor.execute(
    "SELECT user_id FROM users WHERE email = ?",
    (ADMIN_EMAIL,)
)

existing_admin = cursor.fetchone()

if existing_admin:
    # If account exists, make sure its role is admin
    cursor.execute(
        "UPDATE users SET role = 'admin' WHERE email = ?",
        (ADMIN_EMAIL,)
    )

    connection.commit()
    print("Admin account already exists.")
    print("Admin role updated successfully.")

else:
    hashed_password = generate_password_hash(ADMIN_PASSWORD)

    cursor.execute("""
        INSERT INTO users
        (full_name, email, password, role)
        VALUES (?, ?, ?, ?)
    """, (
        ADMIN_NAME,
        ADMIN_EMAIL,
        hashed_password,
        "admin"
    ))

    connection.commit()

    print("Admin account created successfully!")

connection.close()

print("--------------------------------")
print("Admin Email:", ADMIN_EMAIL)
print("Admin Role: admin")
print("--------------------------------")
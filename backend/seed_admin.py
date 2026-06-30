"""Creates a default admin account. Run once after schema.sql has been loaded."""
import db
from auth_utils import hash_password

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin@1234"
ADMIN_EMAIL = "admin@stress-support.local"


def main():
    existing = db.query_one("SELECT user_id FROM users WHERE username = %s", (ADMIN_USERNAME,))
    if existing:
        print("Admin user already exists.")
        return
    db.execute(
        """
        INSERT INTO users (username, password_hash, email, full_name, role)
        VALUES (%s, %s, %s, %s, 'admin')
        """,
        (ADMIN_USERNAME, hash_password(ADMIN_PASSWORD), ADMIN_EMAIL, "System Administrator"),
    )
    print(f"Admin user created: username='{ADMIN_USERNAME}' password='{ADMIN_PASSWORD}'")
    print("Change this password after first login.")


if __name__ == "__main__":
    main()

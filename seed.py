from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db
from models import User

TEST_USERS = [
    {"email": "client@avishu.app", "password": "client123", "role": "client"},
    {"email": "franchisee@avishu.app", "password": "franchisee123", "role": "franchisee"},
    {"email": "production@avishu.app", "password": "production123", "role": "production"},
]


def seed_users():
    app = create_app()
    with app.app_context():
        db.create_all()

        created_count = 0
        for user_data in TEST_USERS:
            existing_user = User.query.filter_by(email=user_data["email"]).first()
            if existing_user:
                continue

            user = User(
                email=user_data["email"],
                password=generate_password_hash(user_data["password"]),
                role=user_data["role"],
            )
            db.session.add(user)
            created_count += 1

        db.session.commit()
        print(f"Seed complete. Created {created_count} users.")
        for user_data in TEST_USERS:
            print(f"- {user_data['role']}: {user_data['email']} / {user_data['password']}")


if __name__ == "__main__":
    seed_users()

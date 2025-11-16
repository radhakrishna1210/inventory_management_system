# FILE: create_admin.py
from app import create_app, db
from app.models import User
from getpass import getpass

app = create_app()

with app.app_context():
    print("Creating a new admin user...")
    username = input("Enter admin username: ")

    if User.query.filter_by(username=username).first():
        print(f"User '{username}' already exists. Aborting.")
    else:
        password = getpass("Enter admin password: ")
        confirm_password = getpass("Confirm admin password: ")

        if password != confirm_password:
            print("Passwords do not match. Aborting.")
        else:
            admin_user = User(username=username)
            admin_user.set_password(password)
            db.session.add(admin_user)
            db.session.commit()
            print(f"Admin user '{username}' created successfully!")
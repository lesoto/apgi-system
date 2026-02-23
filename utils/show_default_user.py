#!/usr/bin/env python3
"""
Display default user credentials.

This script retrieves and displays the default user credentials from the database.
Useful for development and testing when you need to know the login credentials.
"""

import sys
from pathlib import Path

from api.database.connection import SessionLocal
from api.database.models import User
from sqlalchemy import select

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def display_default_user():
    """Display default user credentials."""
    db = SessionLocal()
    try:
        # Look for default user
        stmt = select(User).where(User.username.like("default_%"))
        result = db.execute(stmt)
        users = result.scalars().all()

        if not users:
            print("No default user found in database.")
            print("Please restart the API server to create a default user.")
            return

        print("\n" + "=" * 70)
        print("DEFAULT USER CREDENTIALS")
        print("=" * 70)

        for user in users:
            print(f"\nUsername: {user.username}")
            print(f"Email: {user.email}")
            print(f"User ID: {user.user_id}")
            print(f"Roles: {', '.join(user.roles)}")
            print(f"Created: {user.created_at}")
            print(f"Last Login: {user.last_login or 'Never'}")

        print("\n" + "=" * 70)
        print("NOTE: You will need the password to log in.")
        print("If you don't have the password, check the server logs")
        print("or restart the server to generate new credentials.")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"Error retrieving default user: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    display_default_user()

"""Admin tools for classroom management.

Usage:
  python admin_tools.py create-students students.txt
  python admin_tools.py create-students --count 30 --prefix student
  python admin_tools.py reset
  python admin_tools.py list-users
"""

import asyncio
import csv
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from auth import get_password_hash
from database import Base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/church_bulletin")


def generate_password(length: int = 8) -> str:
    """Generate a simple readable password."""
    import random
    import string
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=length))


async def create_students_from_file(filepath: str):
    """Create student accounts from a text file (one username per line, or CSV: username,password,role)."""
    engine = create_async_engine(DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    from models.user import User

    accounts = []
    lines = Path(filepath).read_text().strip().splitlines()

    async with session_factory() as session:
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = [p.strip() for p in line.split(",")]
            username = parts[0]
            password = parts[1] if len(parts) > 1 else generate_password()
            role = parts[2] if len(parts) > 2 else "editor"

            # Check if already exists
            result = await session.execute(select(User).where(User.username == username))
            if result.scalar_one_or_none():
                print(f"  SKIP {username} (already exists)")
                continue

            user = User(username=username, hashed_password=get_password_hash(password), role=role)
            session.add(user)
            accounts.append((username, password, role))
            print(f"  ADD  {username} / {password} ({role})")

        await session.commit()

    await engine.dispose()
    return accounts


async def create_students_numbered(count: int, prefix: str = "student", role: str = "editor"):
    """Create numbered student accounts: student01, student02, etc."""
    engine = create_async_engine(DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    from models.user import User

    accounts = []
    async with session_factory() as session:
        for i in range(1, count + 1):
            username = f"{prefix}{i:02d}"
            password = generate_password()

            result = await session.execute(select(User).where(User.username == username))
            if result.scalar_one_or_none():
                print(f"  SKIP {username} (already exists)")
                continue

            user = User(username=username, hashed_password=get_password_hash(password), role=role)
            session.add(user)
            accounts.append((username, password, role))
            print(f"  ADD  {username} / {password} ({role})")

        await session.commit()

    await engine.dispose()
    return accounts


async def reset_database():
    """Drop all data and re-seed the database."""
    print("Resetting database...")

    # Import and run seed
    from seed import seed
    await seed()

    print("Database reset complete. All student accounts have been removed.")
    print("Only admin/admin123 and editor/editor123 remain.")


async def list_users():
    """List all users in the database."""
    engine = create_async_engine(DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    from models.user import User

    async with session_factory() as session:
        result = await session.execute(select(User).order_by(User.id))
        users = result.scalars().all()

        print(f"\n{'ID':<5} {'Username':<20} {'Role':<10} {'Active':<8}")
        print("-" * 45)
        for u in users:
            print(f"{u.id:<5} {u.username:<20} {u.role:<10} {u.active!s:<8}")
        print(f"\nTotal: {len(users)} users")

    await engine.dispose()


def save_accounts_csv(accounts: list, filename: str = "student_accounts.csv"):
    """Save generated accounts to a CSV file for distribution."""
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Username", "Password", "Role", "Login URL"])
        for username, password, role in accounts:
            writer.writerow([username, password, role, "http://<server>:8001/docs"])
    print(f"\nAccounts saved to {filename}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "create-students":
        if "--count" in sys.argv:
            idx = sys.argv.index("--count")
            count = int(sys.argv[idx + 1])
            prefix = "student"
            if "--prefix" in sys.argv:
                prefix = sys.argv[sys.argv.index("--prefix") + 1]
            print(f"Creating {count} student accounts with prefix '{prefix}'...")
            accounts = asyncio.run(create_students_numbered(count, prefix))
        elif len(sys.argv) > 2:
            filepath = sys.argv[2]
            print(f"Creating students from {filepath}...")
            accounts = asyncio.run(create_students_from_file(filepath))
        else:
            print("Usage: python admin_tools.py create-students <file.txt>")
            print("       python admin_tools.py create-students --count 30 --prefix student")
            sys.exit(1)

        if accounts:
            save_accounts_csv(accounts)
            print(f"\n{len(accounts)} accounts created successfully.")
        else:
            print("\nNo new accounts created.")

    elif command == "reset":
        confirm = input("This will DELETE all data and re-seed. Are you sure? (yes/no): ")
        if confirm.lower() == "yes":
            asyncio.run(reset_database())
        else:
            print("Cancelled.")

    elif command == "list-users":
        asyncio.run(list_users())

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()

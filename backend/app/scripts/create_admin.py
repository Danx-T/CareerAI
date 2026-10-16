"""Standalone CLI script to create or promote an admin user in CareerAI."""

import argparse
import asyncio
import getpass
import sys
from pathlib import Path
from typing import Optional, Tuple

# Ensure backend directory is in sys.path when executed directly
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal, engine, Base
from app.models import User
from app.core.security import get_password_hash


def validate_credentials(email: str, password: str) -> Tuple[str, str]:
    """Validate and normalize admin credentials."""
    normalized_email = email.strip().lower()
    parts = normalized_email.split("@")
    if len(parts) != 2 or not parts[0] or not parts[1] or "." not in parts[1] or parts[1].startswith(".") or parts[1].endswith("."):
        raise ValueError("Invalid email format.")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")

    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Password must be at most 72 bytes (bcrypt limit).")

    return normalized_email, password


async def create_or_upgrade_admin(
    email: str,
    password: str,
    full_name: str = "Admin",
    session: Optional[AsyncSession] = None,
) -> Tuple[User, bool]:
    """
    Query User by normalized email.
    If exists: upgrade is_admin=True, is_active=True.
    If not exists: create active admin user.
    Returns (user, is_created).
    """
    normalized_email, validated_pwd = validate_credentials(email, password)

    async def _execute(db_session: AsyncSession) -> Tuple[User, bool]:
        stmt = select(User).where(User.email == normalized_email)
        result = await db_session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.is_admin = True
            user.is_active = True
            await db_session.commit()
            await db_session.refresh(user)
            return user, False
        else:
            hashed_pwd = get_password_hash(validated_pwd)
            new_user = User(
                email=normalized_email,
                full_name=full_name or "Admin",
                hashed_password=hashed_pwd,
                is_active=True,
                is_admin=True,
            )
            db_session.add(new_user)
            await db_session.commit()
            await db_session.refresh(new_user)
            return new_user, True

    if session is not None:
        return await _execute(session)

    async with AsyncSessionLocal() as db_session:
        return await _execute(db_session)


async def init_tables() -> None:
    """Ensure database tables are created."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def async_main() -> int:
    """CLI entrypoint runner."""
    parser = argparse.ArgumentParser(description="CareerAI Admin User Creation CLI")
    parser.add_argument("--email", "-e", type=str, help="Admin email address")
    parser.add_argument("--password", "-p", type=str, help="Admin password")
    parser.add_argument("--full-name", "-n", type=str, default="Admin", help="Full name (default: Admin)")
    args = parser.parse_args()

    email = args.email
    if not email:
        email = input("Enter admin email: ")

    password = args.password
    if not password:
        password = getpass.getpass("Enter admin password: ")

    try:
        # Validate before initializing DB or attempting transactions
        validate_credentials(email, password)

        # Ensure database tables exist
        await init_tables()

        user, is_created = await create_or_upgrade_admin(
            email=email,
            password=password,
            full_name=args.full_name or "Admin",
        )
        if is_created:
            print(f"[SUCCESS] Admin user '{user.email}' created successfully.")
        else:
            print(f"[SUCCESS] User '{user.email}' upgraded to admin and activated.")
        return 0
    except ValueError as err:
        print(f"[ERROR] Validation failed: {err}", file=sys.stderr)
        return 1
    except Exception as err:
        print(f"[ERROR] Database operation failed: {err}", file=sys.stderr)
        return 1
    finally:
        await engine.dispose()


def main():
    try:
        exit_code = asyncio.run(async_main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(130)


if __name__ == "__main__":
    main()

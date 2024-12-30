"""Script to reset admin password."""

import argparse
import asyncio
from loguru import logger

from qubit.services.auth import AuthService
from qubit.core.config import load_config
from qubit.database.users import UsersDB


def validate_password(password: str, confirm: str) -> bool:
    """Validate password and confirm password."""
    return password == confirm


async def reset_admin(new_password: str) -> None:
    """Reset admin password with proper hashing."""
    config = load_config()
    db = UsersDB(config)

    mock_request = type(
        "Request",
        (),
        {"app": type("App", (), {"state": type("State", (), {"config": config})()})()},
    )
    auth_service = AuthService(db, mock_request)

    try:
        password_hash = auth_service.get_password_hash(new_password)

        with db.conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE username = %s RETURNING id",
                (password_hash, "admin"),
            )
            result = cursor.fetchone()
            if not result:
                logger.error("Admin user not found")
                return

            db.conn.commit()

        logger.info("Admin password has been reset successfully")
        logger.info(f"New admin password: {new_password}")

    except Exception as e:
        logger.error(f"Failed to reset admin password: {e}")
        db.conn.rollback()
    finally:
        db.conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Reset admin password",
    )
    parser.add_argument(
        "-p",
        "--password",
        type=str,
        help="New admin password",
        required=True,
    )
    parser.add_argument(
        "-c",
        "--confirm",
        type=str,
        help="Confirm new admin password",
        required=True,
    )
    args = parser.parse_args()

    if not validate_password(args.password, args.confirm):
        logger.error("Passwords do not match")
        exit(1)

    asyncio.run(reset_admin(args.password))

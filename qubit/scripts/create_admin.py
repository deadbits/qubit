"""CLI commands for Qubit."""

import argparse
import os
from pathlib import Path
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from qubit.core.config import load_config
from qubit.models.database import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)


def create_admin(
    username: str, email: str, password: str, config_path: str = "data/config.yaml"
):
    """Create an admin user."""
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            config_file = Path(config_path)
            if not config_file.exists():
                logger.error(f"Config file not found: {config_file}")
                return

            config = load_config(str(config_file))
            database_url = f"postgresql://{config.database.user}:{config.database.password}@{config.database.host}:{config.database.port}/{config.database.name}"

        logger.info(f"Creating admin user: {username}")
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            existing_user = (
                session.query(User)
                .filter((User.username == username) | (User.email == email))
                .first()
            )

            if existing_user:
                logger.warning(
                    f"User with username {username} or email {email} already exists"
                )
                return

            password_hash = hash_password(password)
            admin_user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                is_active=True,
                is_admin=True,
            )

            session.add(admin_user)
            session.commit()
            logger.info(f"Successfully created admin user: {username}")

            return admin_user

        except Exception as e:
            logger.error(f"Failed to create admin user in database: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Failed to initialize admin user creation: {e}")
        raise


def main():
    """Run CLI commands."""
    parser = argparse.ArgumentParser(description="Qubit CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    admin_parser = subparsers.add_parser("create-admin", help="Create an admin user")
    admin_parser.add_argument("--username", required=True, help="Admin username")
    admin_parser.add_argument("--email", required=True, help="Admin email")
    admin_parser.add_argument("--password", required=True, help="Admin password")
    admin_parser.add_argument(
        "--config", default="data/config.yaml", help="Path to config file"
    )

    args = parser.parse_args()

    if args.command == "create-admin":
        create_admin(args.username, args.email, args.password, args.config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

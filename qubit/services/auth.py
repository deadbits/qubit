"""Authentication service."""

from typing import Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from loguru import logger
from fastapi import Request
from pydantic import EmailStr
from starlette.responses import Response

from qubit.models.user import UserCreate, UserDB
from qubit.database.users import UsersDB

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service."""

    def __init__(self, db: UsersDB, request: Request):
        """Initialize auth service with users database."""
        self.db = db
        self.config = request.app.state.config
        self.request = request

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password."""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def get_password_hash(self, password: str) -> str:
        """Get password hash."""
        return pwd_context.hash(password)

    def set_session_cookie(
        self, response: Response, username: str, is_admin: bool = False
    ) -> None:
        """Set secure session cookie."""
        try:
            session_data = {
                "username": username,
                "is_admin": is_admin,
                "exp": (
                    datetime.utcnow()
                    + timedelta(minutes=self.config.auth.access_token_expire_minutes)
                ).timestamp(),
            }

            self.request.session.clear()
            self.request.session.update(session_data)
            logger.info(f"Session created for {username}; admin: {is_admin}")
        except Exception as e:
            logger.error(f"Error setting session: {e}")
            raise

    def clear_session(self, response: Response) -> None:
        """Clear session cookie."""
        try:
            self.request.session.clear()
        except Exception as e:
            logger.error(f"Error clearing session: {e}")

    async def authenticate_user(self, username: str, password: str) -> Optional[UserDB]:
        """Authenticate user."""
        auth_user = await self.db.get_user_by_username(username)
        if not auth_user:
            logger.warning(f"User not found: {username}")
            return None
        if not self.verify_password(password, auth_user.password_hash):
            logger.warning(f"Failed password verification for {username}")
            return None
        logger.debug(f"User authenticated successfully: {username}")
        return UserDB.model_validate(
            {k: v for k, v in auth_user.model_dump().items() if k != "password_hash"}
        )

    async def get_current_user(self) -> Optional[UserDB]:
        """Get current user from session."""
        try:
            session = getattr(self.request, "session", None)
            if not session:
                return None

            username = session.get("username")
            if not username:
                return None

            exp = session.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                self.clear_session(None)
                return None

            user = await self.db.get_user_by_username(username)
            if not user:
                logger.warning(f"User not found: {username}")
                return None

            logger.debug(f"User found in session: {username}")
            return UserDB.model_validate(user)
        except Exception as e:
            logger.warning(f"Session error: {e}")
            return None

    async def check_admin_access(self) -> bool:
        """Check if user has admin access from session."""
        try:
            session = getattr(self.request, "session", None)
            if not session:
                return False

            exp = session.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                self.clear_session(None)
                return False

            result = session.get("is_admin", False)
            return result
        except Exception as e:
            logger.warning(f"Session error during admin check: {e}")
            return False

    async def create_admin_user(
        self,
        username: str,
        email: EmailStr,
        password: str,
        display_name: Optional[str] = None,
    ) -> UserDB:
        """Create admin user."""
        user = UserCreate(
            username=username,
            email=email,
            password=password,
            display_name=display_name or username,
        )
        password_hash = self.get_password_hash(password)
        logger.info(f"Creating admin user: {username}")

        user_db = await self.db.create_user(user, password_hash)
        if not user_db:
            raise ValueError("Failed to create user")

        if not await self.db.set_user_admin(username):
            raise ValueError("Failed to set admin status")

        return user_db

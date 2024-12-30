"""User database operations."""

from typing import Optional

from loguru import logger

from qubit.models.user import UserCreate, UserDB, AuthUser
from qubit.database import Database


class UsersDB(Database):
    """User database operations."""

    async def create_user(
        self, user: UserCreate, password_hash: str
    ) -> Optional[UserDB]:
        """Create a new user."""
        async with self._pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    """
                    INSERT INTO users (username, email, password_hash, display_name, bio)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id, username, email, display_name, bio, is_active, is_admin, created_at, updated_at
                """,
                    user.username,
                    user.email,
                    password_hash,
                    user.display_name,
                    user.bio,
                )

                if row:
                    return UserDB(
                        id=row["id"],
                        username=row["username"],
                        email=row["email"],
                        display_name=row["display_name"],
                        bio=row["bio"],
                        is_active=row["is_active"],
                        is_admin=row["is_admin"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )
                return None

            except Exception as e:
                logger.error(f"Error creating user: {e}")
                return None

    async def get_user_by_username(self, username: str) -> Optional[AuthUser]:
        """Get user by username including password hash."""
        async with self._pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    """
                    SELECT id, username, email, password_hash, display_name, bio,
                           is_active, is_admin, created_at, updated_at
                    FROM users WHERE username = $1
                """,
                    username,
                )

                if not row:
                    return None

                return AuthUser(
                    id=row["id"],
                    username=row["username"],
                    email=row["email"],
                    password_hash=row["password_hash"],
                    display_name=row["display_name"],
                    bio=row["bio"],
                    is_active=row["is_active"],
                    is_admin=row["is_admin"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )

            except Exception as e:
                logger.error(f"Error fetching user: {e}")
                return None

    async def set_user_admin(self, username: str, is_admin: bool = True) -> bool:
        """Set user admin status."""
        async with self._pool.acquire() as conn:
            try:
                result = await conn.execute(
                    """
                    UPDATE users 
                    SET is_admin = $1, updated_at = CURRENT_TIMESTAMP
                    WHERE username = $2
                """,
                    is_admin,
                    username,
                )

                return "UPDATE 1" in result

            except Exception as e:
                logger.error(f"Error setting user admin status: {e}")
                return False

"""Base database."""

from typing import Optional, AsyncGenerator
import asyncpg
from loguru import logger

from qubit.models.config import Config


class Database:
    """Base database manager with connection pooling."""

    _pool: Optional[asyncpg.Pool] = None

    def __init__(self, config: Config):
        """Initialize database configuration."""
        self.config = config
        self.host = config.database.host
        self.port = config.database.port
        self.dbname = config.database.name
        self.user = config.database.user
        self.password = config.database.password

    @classmethod
    async def create_pool(cls, config: Config) -> None:
        """Create database connection pool."""
        if cls._pool is None:
            try:
                cls._pool = await asyncpg.create_pool(
                    host=config.database.host,
                    port=config.database.port,
                    database=config.database.name,
                    user=config.database.user,
                    password=config.database.password,
                    min_size=5,
                    max_size=20,
                )

                logger.info("Database connection pool created successfully")

            except Exception as e:
                logger.error(f"Failed to create database pool: {e}")
                raise

    @classmethod
    async def close_pool(cls) -> None:
        """Close the database connection pool."""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            logger.info("Database connection pool closed")

    async def get_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get a connection from the pool."""
        if self._pool is None:
            await self.create_pool(self.config)

        async with self._pool.acquire() as connection:
            yield connection

    @classmethod
    async def initialize_database(cls, config: Config):
        """Initialize database schema. Should only be called once at startup."""
        db = cls(config=config)
        await cls.create_pool(config)
        await db._setup_database()

    async def _setup_database(self) -> None:
        """Initialize database schema."""
        if self._pool is None:
            raise RuntimeError("Database pool not initialized")

        async with self._pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
                """
                )

                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        display_name VARCHAR(100),
                        bio TEXT,
                        is_active BOOLEAN DEFAULT true,
                        is_admin BOOLEAN DEFAULT false,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS posts (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        title VARCHAR(255) NOT NULL,
                        content TEXT NOT NULL,
                        content_html TEXT NOT NULL,
                        slug VARCHAR(255) NOT NULL,
                        published BOOLEAN DEFAULT false,
                        published_at TIMESTAMP,
                        author_id INTEGER REFERENCES users(id) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS feed_posts (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        content TEXT NOT NULL,
                        author_id INTEGER REFERENCES users(id) NOT NULL,
                        author_name VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tags (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) UNIQUE NOT NULL,
                        description VARCHAR(200),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS post_tags (
                        post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
                        tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
                        PRIMARY KEY (post_id, tag_id)
                    )
                """
                )

                await conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_posts_slug ON posts(slug);
                    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
                    CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);
                    CREATE INDEX IF NOT EXISTS idx_feed_posts_created_at ON feed_posts(created_at DESC);
                """
                )

                logger.info("Database schema initialized successfully")

            except Exception as e:
                logger.error(f"Database setup error: {e}")
                raise

"""Common utilities."""

import re
from typing import Generator
from contextlib import contextmanager
from unidecode import unidecode

from fastapi import Request

from qubit.database import Database
from qubit.database.users import UsersDB
from qubit.database.posts import PostsDB
from qubit.database.feed import FeedDB


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = unidecode(text)
    text = text.lower()
    text = re.sub(r"[\s]+", "-", text)
    text = re.sub(r"[^\w\-]", "", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    return text


@contextmanager
def get_db_context(request: Request) -> Generator[Database, None, None]:
    """Get database connection as a context manager."""
    config = request.app.state.config
    db = Database(config=config)
    yield db


def get_db(request: Request) -> Database:
    """Get database connection directly."""
    config = request.app.state.config
    return Database(config=config)


def get_users_db(request: Request) -> UsersDB:
    """Get users database connection."""
    config = request.app.state.config
    return UsersDB(config=config)


def get_posts_db(request: Request) -> PostsDB:
    """Get posts database connection."""
    config = request.app.state.config
    return PostsDB(config=config)


def get_feed_db(request: Request) -> FeedDB:
    """Get feed database connection."""
    config = request.app.state.config
    return FeedDB(config=config)

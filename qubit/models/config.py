"""Configuration models."""

from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """Database configuration."""

    host: str
    port: int
    name: str
    user: str
    password: Optional[str] = None


class AuthorConfig(BaseModel):
    """Author configuration."""

    name: str
    short_name: str
    bio: str
    github: str
    website: str


class AuthConfig(BaseModel):
    """Authentication configuration."""

    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    secret_key: Optional[str] = None


class Config(BaseSettings):
    """Application configuration."""

    database: DatabaseConfig
    author: AuthorConfig
    auth: AuthConfig

    auth_secret_key: str = Field(default=..., env="AUTH_SECRET_KEY")
    db_password: str = Field(default=..., env="DB_PASSWORD")

    admin_username: str = Field(default=..., env="ADMIN_USERNAME")
    admin_email: str = Field(default=..., env="ADMIN_EMAIL")
    admin_password: str = Field(default=..., env="ADMIN_PASSWORD")

    class Config:
        """Config."""

        env_file = ".env"
        env_file_encoding = "utf-8"

    def model_post_init(self, *args, **kwargs):
        """Post initialization hook to set environment values."""
        super().model_post_init(*args, **kwargs)
        self.auth.secret_key = self.auth_secret_key
        self.database.password = self.db_password

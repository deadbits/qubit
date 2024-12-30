"""Main application module."""

import argparse
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

from qubit.api import posts, auth, feed
from qubit.web import routes
from qubit.api.middleware import admin_required
from qubit.api.utils import APIError, handle_api_error
from qubit.database import Database
from qubit.core.config import load_config, Config


def create_app(config: Config) -> FastAPI:
    """Create FastAPI application."""
    load_dotenv()

    app = FastAPI(
        title="Qubit",
        description="A minimalist blogging platform",
        version="0.1.0",
    )

    app.state.config = config

    # Add exception handlers
    app.add_exception_handler(APIError, handle_api_error)
    
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.mount("/static", StaticFiles(directory="qubit/templates/static"), name="static")
    templates = Jinja2Templates(directory="qubit/templates")

    templates.env.globals["config"] = config
    app.state.templates = templates

    app.middleware("http")(admin_required)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if not config.auth.secret_key:
        raise ValueError("AUTH_SECRET_KEY environment variable is required")

    app.add_middleware(
        SessionMiddleware,
        secret_key=config.auth.secret_key,
        https_only=False,
    )

    app.include_router(auth.router, prefix="/api", tags=["auth"])
    app.include_router(posts.router, prefix="/api", tags=["posts"])
    app.include_router(feed.router, prefix="/api", tags=["feed"])

    app.get("/")(routes.list_posts)
    app.get("/feed")(routes.feed)
    app.get("/posts/{post_id}")(routes.view_post)
    app.get("/about")(routes.about)
    app.get("/login")(routes.login)
    app.get("/admin/settings")(routes.admin_settings)
    app.get("/admin/hub")(routes.writer_hub)
    app.get("/admin/hub/write")(routes.hub_new_post)
    app.get("/admin/hub/edit/{post_id}")(routes.hub_edit_post)

    @app.on_event("startup")
    async def startup_event():
        """Initialize database on startup."""
        await Database.initialize_database(config)

    @app.on_event("shutdown")
    async def shutdown_event():
        """Close database connections on shutdown."""
        await Database.close_pool()

    return app


def main():
    """Run the application."""
    parser = argparse.ArgumentParser(
        description="Qubit - A minimalist blogging platform"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to config (default: data/config.yaml)",
        default="data/config.yaml",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return

    config = load_config(str(config_path))
    app = create_app(config)
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

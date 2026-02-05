"""Flask application entry point for Arizona House Hunter."""

import logging
from flask import Flask, send_from_directory
from pathlib import Path

from . import config
from . import database
from .api import api

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        static_folder="static",
        static_url_path="/static"
    )

    # Register API blueprint
    app.register_blueprint(api)

    # Initialize database
    database.init_database()
    logger.info(f"Database initialized at {config.DATABASE_PATH}")

    @app.route("/")
    def index():
        """Serve the main page."""
        return send_from_directory(app.static_folder, "index-new.html")

    @app.route("/old")
    def index_old():
        """Serve the old page for comparison."""
        return send_from_directory(app.static_folder, "index.html")

    @app.route("/favicon.ico")
    def favicon():
        """Serve favicon."""
        return "", 204

    return app


def main():
    """Run the Flask development server."""
    app = create_app()

    logger.info(f"Starting Arizona House Hunter on http://localhost:{config.FLASK_PORT}")
    logger.info("Open the URL in your browser to view listings")
    logger.info("Click 'Refresh Data' to fetch listings from Redfin")

    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )


if __name__ == "__main__":
    main()

from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from .extensions import db
import os
from .models import User
from .routes import api
from .config import Config
from sqlalchemy import inspect, text
from .extra_routes import extra_api

login_manager = LoginManager()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address, default_limits=["300 per hour"])

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__, static_folder="../frontend/build", static_url_path="/")
    app.register_blueprint(extra_api, url_prefix="/api")
    app.config.from_object(Config)
    app.config["ADMIN_EMAIL"] = os.getenv(
        "ADMIN_EMAIL", ""
    ).strip().lower()
    if test_config: app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app); login_manager.init_app(app); migrate.init_app(app, db); limiter.init_app(app)
    CORS(app, supports_credentials=True, origins=app.config["CORS_ORIGINS"])
    app.register_blueprint(api, url_prefix="/api")
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"): return jsonify({"error":"Not found"}),404
        index = Path(app.static_folder) / "index.html"
        if index.exists(): return send_from_directory(app.static_folder, "index.html")
        return jsonify({"message":"Ash Streak API is running. Start React with npm start."})
    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return jsonify({"error":"Internal server error"}),500
    with app.app_context():
        db.create_all()

        # Add sort_order to existing Routine tables without deleting data.
        columns = {
            column["name"]
            for column in inspect(db.engine).get_columns("routine")
        }

        if "sort_order" not in columns:
            db.session.execute(text(
                "ALTER TABLE routine "
                "ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0"
            ))
            db.session.commit()
    return app

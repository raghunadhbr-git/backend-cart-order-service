from flask import Flask, jsonify
from flask_cors import CORS

from .config import Config
from .extensions import db, migrate, jwt
from .api.cart_routes import cart_bp
from .api.checkout_routes import checkout_bp
from .api.orders_routes import orders_bp


def create_app(testing: bool = False):
    app = Flask(__name__)
    app.config.from_object(Config)

    # -------------------------------
    # TESTING OVERRIDES
    # -------------------------------
    if testing:
        app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            JWT_SECRET_KEY="test-secret",
        )

    # -------------------------------
    # EXTENSIONS
    # -------------------------------
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # -------------------------------
    # BLUEPRINTS
    # -------------------------------
    app.register_blueprint(cart_bp, url_prefix="/api/cart")
    app.register_blueprint(checkout_bp, url_prefix="/api/checkout")
    app.register_blueprint(orders_bp, url_prefix="/api/orders")

    # -------------------------------
    # HEALTH CHECK
    # -------------------------------
    @app.get("/")
    def health():
        return jsonify({"status": "Cart-Order-Service UP"}), 200

    return app

# ✅ Why this is correct
# •	Supports production + tests
# •	No environment hacks
# •	Same pattern as auth-service
# •	Works with pytest-flask
# •	Safe for Render / Neon



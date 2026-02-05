import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "cart-secret")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///cart.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key")

    # 🔗 Product Service (inter-service communication)
    PRODUCT_BASE_URL = os.getenv(
        "PRODUCT_BASE_URL",
        "http://127.0.0.1:5002"   # local dev only
    )

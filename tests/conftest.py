import pytest
from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    app = create_app(testing=True)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()

# ✅ Why this is correct
# •	Uses application factory correctly
# •	In-memory DB for speed
# •	Clean DB lifecycle per test
# •	No global state leakage

# # Run tests
# pytest

# # Run coverage
# pytest --cov=app --cov-report=term-missing

# 🧠 Important (you did this right)
# You are now following:
# •	Factory pattern
# •	Test isolation
# •	Microservice-safe testing
# •	CI-ready structure
# This is exactly how real teams do it.






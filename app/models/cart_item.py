from datetime import datetime
from app.extensions import db

class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)

    product_id = db.Column(db.Integer, nullable=False)
    variant_id = db.Column(db.Integer, nullable=False)

    name = db.Column(db.String(200), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

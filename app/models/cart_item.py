from app.extensions import db
from datetime import datetime


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, nullable=False)

    product_id = db.Column(db.Integer, nullable=False)
    variant_id = db.Column(db.Integer, nullable=False)  # 🔥 NEW
    color = db.Column(db.String(50), nullable=False)     # 🔥 NEW

    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(500))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CartItem user={self.user_id} variant={self.variant_id}>"

from app.extensions import db


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, nullable=False)

    product_id = db.Column(db.Integer, nullable=False)
    variant_id = db.Column(db.Integer, nullable=False)   # 🔥 NEW
    color = db.Column(db.String(50), nullable=False)     # 🔥 NEW

    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(500))

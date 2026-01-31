from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
import os

from ..extensions import db
from ..models.cart_item import CartItem
from ..models.order import Order
from ..models.order_item import OrderItem   # ✅ CORRECT

checkout_bp = Blueprint("checkout", __name__)

PRODUCT_BASE_URL = os.getenv(
    "PRODUCT_BASE_URL",
    "http://127.0.0.1:5002"
)

@checkout_bp.post("/")
@jwt_required()
def checkout():
    user_id = get_jwt_identity()
    data = request.get_json()

    cart_items = CartItem.query.filter_by(user_id=user_id).all()

    if not cart_items:
        return jsonify({"error": "Cart is empty"}), 400

    payload = {
        "items": [
            {
                "product_id": c.product_id,
                "variant_id": c.variant_id,
                "quantity": c.quantity
            }
            for c in cart_items
        ]
    }

    resp = requests.post(
        f"{PRODUCT_BASE_URL}/api/v1/products/decrease-stock",
        json=payload,
        headers={
            "Authorization": request.headers.get("Authorization")
        }
    )

    if resp.status_code != 200:
        return jsonify({"error": "Insufficient stock"}), 400

    order = Order(
        user_id=user_id,
        total_price=sum(c.price * c.quantity for c in cart_items),
        contact=data["contact"],
        address=data["address"]
    )

    db.session.add(order)
    db.session.flush()

    for c in cart_items:
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=c.product_id,
            variant_id=c.variant_id,
            quantity=c.quantity,
            price=c.price
        ))
        db.session.delete(c)

    db.session.commit()

    return jsonify({
        "order_id": order.id,
        "status": "placed"
    }), 201

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
import os

from ..extensions import db
from ..models.cart_item import CartItem
from ..models.order import Order
from ..models.order_item import OrderItem

checkout_bp = Blueprint("checkout", __name__)

# 🔗 Product Service Base URL
PRODUCT_BASE_URL = os.getenv(
    "PRODUCT_BASE_URL",
    "http://127.0.0.1:5002"  # local dev only
)

@checkout_bp.post("/")
@jwt_required()
def checkout():
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    # 1️⃣ Fetch cart items
    cart_items = CartItem.query.filter_by(user_id=user_id).all()

    if not cart_items:
        return jsonify({"error": "Cart is empty"}), 400

    # 2️⃣ Prepare payload for Product Service
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

    # 3️⃣ Call Product Service (SAFE + TIMEOUT)
    try:
        resp = requests.post(
            f"{PRODUCT_BASE_URL}/api/v1/products/decrease-stock",
            json=payload,
            headers={
                "Authorization": request.headers.get("Authorization")
            },
            timeout=5  # ⬅️ CRITICAL FIX
        )
    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Product service unavailable"
        }), 503

    if resp.status_code != 200:
        return jsonify({
            "error": "Insufficient stock"
        }), 400

    # 4️⃣ Create Order
    order = Order(
        user_id=user_id,
        total_price=sum(c.price * c.quantity for c in cart_items),
        contact=data.get("contact"),
        address=data.get("address")
    )

    db.session.add(order)
    db.session.flush()  # get order.id

    # 5️⃣ Create Order Items & clear cart
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

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
import os

from ..extensions import db
from ..models.cart import CartItem
from ..models.order import Order, OrderItem

checkout_bp = Blueprint("checkout", __name__)

PRODUCT_BASE_URL = os.getenv("PRODUCT_BASE_URL", "http://127.0.0.1:5002")


# ============================================================
# CHECKOUT → PLACE ORDER → DECREASE STOCK
# ============================================================
@checkout_bp.post("/")
@jwt_required()
def checkout():
    user_id = get_jwt_identity()
    data = request.get_json()

    contact = data.get("contact")
    address = data.get("address")
    total_price = data.get("total_price")

    if not contact or not address:
        return jsonify({"error": "Missing contact or address"}), 400

    cart_items = CartItem.query.filter_by(user_id=user_id).all()

    if not cart_items:
        return jsonify({"error": "Cart is empty"}), 400

    # --------------------------------------------------
    # BUILD STOCK DECREASE PAYLOAD
    # --------------------------------------------------
    stock_payload = {
        "items": [
            {
                "product_id": item.product_id,
                "variant_id": item.variant_id,
                "quantity": item.quantity
            }
            for item in cart_items
        ]
    }

    # --------------------------------------------------
    # CALL PRODUCT SERVICE (DECREASE STOCK)
    # --------------------------------------------------
    product_resp = requests.post(
        f"{PRODUCT_BASE_URL}/api/v1/products/decrease-stock",
        json=stock_payload,
        headers={
            "Authorization": request.headers.get("Authorization")
        }
    )

    if product_resp.status_code != 200:
        return jsonify({
            "error": "Insufficient stock or product service error"
        }), 400

    # --------------------------------------------------
    # CREATE ORDER
    # --------------------------------------------------
    order = Order(
        user_id=user_id,
        total_price=total_price,
        status="placed",
        contact=contact,
        address=address
    )

    db.session.add(order)
    db.session.flush()  # get order.id

    # --------------------------------------------------
    # CREATE ORDER ITEMS
    # --------------------------------------------------
    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            variant_id=item.variant_id,
            quantity=item.quantity,
            price=item.price
        )
        db.session.add(order_item)
        db.session.delete(item)  # clear cart

    db.session.commit()

    return jsonify({
        "order_id": order.id,
        "status": "placed",
        "message": "Order placed successfully"
    }), 201

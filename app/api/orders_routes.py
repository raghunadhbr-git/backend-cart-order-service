from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
from ..extensions import db
from ..models.order import Order, OrderItem
from ..models.cart import CartItem
import os

orders_bp = Blueprint("orders", __name__)

PRODUCT_BASE_URL = os.getenv("PRODUCT_BASE_URL")

# ============================================================
# CHECKOUT
# ============================================================
@orders_bp.post("/checkout")
@jwt_required()
def checkout():
    user_id = get_jwt_identity()
    cart_items = CartItem.query.filter_by(user_id=user_id).all()

    if not cart_items:
        return jsonify({"error": "Cart empty"}), 400

    # ↓↓↓ DECREASE STOCK ↓↓↓
    payload = {
        "items": [
            {
                "product_id": c.product_id,
                "variant_id": c.variant_id,
                "quantity": c.quantity
            } for c in cart_items
        ]
    }

    r = requests.post(
        f"{PRODUCT_BASE_URL}/api/v1/products/decrease-stock",
        json=payload,
        headers={"Authorization": f"Bearer {requests.headers.get('Authorization')}"}
    )

    if r.status_code != 200:
        return jsonify({"error": "Stock update failed"}), 400

    order = Order(user_id=user_id, status="placed", total_price=sum(c.price * c.quantity for c in cart_items))
    db.session.add(order)
    db.session.flush()

    for c in cart_items:
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=c.product_id,
            variant_id=c.variant_id,
            quantity=c.quantity
        ))
        db.session.delete(c)

    db.session.commit()

    return jsonify({"order_id": order.id, "status": "placed"}), 201


# ============================================================
# GET ORDERS
# ============================================================
@orders_bp.get("/")
@jwt_required()
def get_orders():
    user_id = get_jwt_identity()
    orders = Order.query.filter_by(user_id=user_id).all()

    return jsonify([
        {
            "order_id": o.id,
            "status": o.status,
            "total_price": o.total_price,
            "created_at": o.created_at
        } for o in orders
    ])


# ============================================================
# CANCEL ORDER (RESTORE STOCK)
# ============================================================
@orders_bp.patch("/<int:order_id>/cancel")
@jwt_required()
def cancel_order(order_id):
    user_id = get_jwt_identity()
    order = Order.query.filter_by(id=order_id, user_id=user_id).first_or_404()

    if order.status != "placed":
        return jsonify({"error": "Order cannot be cancelled"}), 400

    items = OrderItem.query.filter_by(order_id=order.id).all()

    payload = {
        "items": [
            {
                "product_id": i.product_id,
                "variant_id": i.variant_id,
                "quantity": i.quantity
            } for i in items
        ]
    }

    requests.post(
        f"{PRODUCT_BASE_URL}/api/v1/products/restore-stock",
        json=payload,
        headers={"Authorization": f"Bearer {requests.headers.get('Authorization')}"}
    )

    order.status = "cancelled"
    db.session.commit()

    return jsonify({"message": "Order cancelled"}), 200

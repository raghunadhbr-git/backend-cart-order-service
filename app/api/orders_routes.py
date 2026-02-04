from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import CORS
import requests
import os

from ..extensions import db
from ..models.order import Order
from ..models.order_item import OrderItem

orders_bp = Blueprint("orders", __name__)
CORS(orders_bp)  # 🔥 IMPORTANT FIX — enables OPTIONS on /<id>

PRODUCT_BASE_URL = os.getenv(
    "PRODUCT_BASE_URL",
    "http://127.0.0.1:5002"
)

# ============================================================
# GET ALL ORDERS
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
        }
        for o in orders
    ]), 200


# ============================================================
# GET SINGLE ORDER (DETAILS)
# ============================================================
@orders_bp.get("/<int:order_id>")
@jwt_required()
def get_order_details(order_id):
    user_id = get_jwt_identity()

    order = Order.query.filter_by(
        id=order_id,
        user_id=user_id
    ).first_or_404()

    items = OrderItem.query.filter_by(order_id=order.id).all()

    return jsonify({
        "order_id": order.id,
        "status": order.status,
        "total_price": order.total_price,
        "created_at": order.created_at,
        "items": [
            {
                "product_id": i.product_id,
                "variant_id": i.variant_id,
                "quantity": i.quantity,
                "price": i.price
            }
            for i in items
        ]
    }), 200


# ============================================================
# CANCEL ORDER → RESTORE STOCK
# ============================================================
@orders_bp.patch("/<int:order_id>/cancel")
@jwt_required()
def cancel_order(order_id):
    user_id = get_jwt_identity()

    order = Order.query.filter_by(
        id=order_id,
        user_id=user_id
    ).first_or_404()

    if order.status != "placed":
        return jsonify({"error": "Order cannot be cancelled"}), 400

    items = OrderItem.query.filter_by(order_id=order.id).all()

    payload = {
        "items": [
            {
                "product_id": i.product_id,
                "variant_id": i.variant_id,
                "quantity": i.quantity
            }
            for i in items
        ]
    }

    resp = requests.post(
        f"{PRODUCT_BASE_URL}/api/v1/products/restore-stock",
        json=payload,
        headers={
            "Authorization": request.headers.get("Authorization")
        }
    )

    if resp.status_code != 200:
        return jsonify({"error": "Stock restore failed"}), 500

    order.status = "cancelled"
    db.session.commit()

    return jsonify({"message": "Order cancelled"}), 200

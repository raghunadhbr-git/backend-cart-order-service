from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests

from app.models.order import Order
from app.models.order_item import OrderItem
from app.extensions import db

orders_bp = Blueprint("orders", __name__)

PRODUCT_RESTORE_URL = (
    "https://backend-product-service.onrender.com/api/v1/products/restore-stock"
)

ML_EVENTS_URL = "https://backend-ml-events-service.onrender.com/api/events"


# ============================================================
# GET MY ORDERS
# ============================================================
@orders_bp.get("/")
@jwt_required()
def get_my_orders():
    user_id = int(get_jwt_identity())

    orders = Order.query.filter_by(user_id=user_id).order_by(
        Order.created_at.desc()
    ).all()

    return jsonify([
        {
            "order_id": o.id,
            "total_price": o.total_price,
            "status": o.status,
            "created_at": o.created_at
        }
        for o in orders
    ]), 200


# ============================================================
# GET ORDER DETAILS
# ============================================================
@orders_bp.get("/<int:order_id>")
@jwt_required()
def get_order_details(order_id):
    user_id = int(get_jwt_identity())

    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return jsonify({"error": "Order not found"}), 404

    items = OrderItem.query.filter_by(order_id=order.id).all()

    return jsonify({
        "order_id": order.id,
        "status": order.status,
        "total_price": order.total_price,
        "items": [
            {
                "product_id": i.product_id,
                "variant_id": i.variant_id,
                "name": i.name,
                "price": i.price,
                "quantity": i.quantity,
                "image": i.image
            }
            for i in items
        ]
    }), 200


# ============================================================
# ❌ CANCEL ORDER → RESTORE STOCK
# ============================================================
@orders_bp.patch("/<int:order_id>/cancel")
@jwt_required()
def cancel_order(order_id):
    user_id = int(get_jwt_identity())

    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order.status != "placed":
        return jsonify({"error": "Order cannot be cancelled"}), 400

    items = OrderItem.query.filter_by(order_id=order.id).all()

    restore_payload = {
        "items": [
            {
                "product_id": i.product_id,
                "variant_id": i.variant_id,
                "quantity": i.quantity
            }
            for i in items
        ]
    }

    # 🔥 RESTORE STOCK
    requests.post(
        PRODUCT_RESTORE_URL,
        json=restore_payload,
        headers={"Authorization": request.headers.get("Authorization")}
    )

    order.status = "cancelled"
    db.session.commit()

    # 🔥 ML EVENT
    requests.post(
        ML_EVENTS_URL,
        json={
            "event_type": "order_cancelled",
            "object_type": "order",
            "object_id": order.id
        }
    )

    return jsonify({"message": "Order cancelled & stock restored"}), 200


# ============================================================
# 🔁 RETURN ORDER → RESTORE STOCK
# ============================================================
@orders_bp.patch("/<int:order_id>/return")
@jwt_required()
def return_order(order_id):
    user_id = int(get_jwt_identity())

    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order.status != "delivered":
        return jsonify({"error": "Only delivered orders can be returned"}), 400

    items = OrderItem.query.filter_by(order_id=order.id).all()

    restore_payload = {
        "items": [
            {
                "product_id": i.product_id,
                "variant_id": i.variant_id,
                "quantity": i.quantity
            }
            for i in items
        ]
    }

    # 🔥 RESTORE STOCK
    requests.post(
        PRODUCT_RESTORE_URL,
        json=restore_payload,
        headers={"Authorization": request.headers.get("Authorization")}
    )

    order.status = "returned"
    db.session.commit()

    return jsonify({"message": "Order returned & stock restored"}), 200


# NOTE:
# Cancel endpoint stays same for now.
# Stock restore logic will be added AFTER Product Service supports increase-stock.
# No breaking changes here yet.
# This is to avoid complications during the ongoing variant/color feature rollout.

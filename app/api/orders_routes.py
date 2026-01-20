from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests

from app.models.order import Order
from app.models.order_item import OrderItem
from app.extensions import db

orders_bp = Blueprint("orders", __name__)

ML_EVENTS_URL = "https://backend-ml-events-service.onrender.com/api/events"


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
                "name": i.name,
                "price": i.price,
                "quantity": i.quantity,
                "image": i.image
            }
            for i in items
        ]
    }), 200


@orders_bp.patch("/<int:order_id>/cancel")
@jwt_required()
def cancel_order(order_id):
    user_id = int(get_jwt_identity())

    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order.status != "placed":
        return jsonify({"error": "Order cannot be cancelled"}), 400

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

    return jsonify({"message": "Order cancelled"}), 200

# NOTE:
# Cancel endpoint stays same for now.
# Stock restore logic will be added AFTER Product Service supports increase-stock.
# No breaking changes here yet.
# This is to avoid complications during the ongoing variant/color feature rollout.

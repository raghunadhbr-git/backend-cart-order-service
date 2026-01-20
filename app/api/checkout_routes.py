from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests

from app.extensions import db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.cart_item import CartItem

checkout_bp = Blueprint("checkout", __name__)

PRODUCT_SERVICE_URL = "https://backend-product-service.onrender.com/api/v1/products/decrease-stock"


@checkout_bp.post("/")
@jwt_required()
def checkout():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify({"error": "Cart is empty"}), 400

    try:
        # 1️⃣ Prepare stock payload FIRST
        items_payload = [
            {
                "variant_id": item.variant_id,
                "quantity": item.quantity
            }
            for item in cart_items
        ]

        # 2️⃣ Call Product Service (STOCK TRUTH)
        resp = requests.post(
            PRODUCT_SERVICE_URL,
            json={"items": items_payload},
            headers={"Authorization": request.headers.get("Authorization")}
        )

        if resp.status_code != 200:
            return jsonify({"error": "Insufficient stock"}), 400

        # 3️⃣ Create Order
        order = Order(
            user_id=user_id,
            contact=data["contact"],
            address=data["address"],
            total_price=data["total_price"]
        )
        db.session.add(order)
        db.session.flush()

        # 4️⃣ Create Order Items
        for item in cart_items:
            db.session.add(OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                color=item.color,
                name=item.name,
                price=item.price,
                quantity=item.quantity,
                image=item.image
            ))

        # 5️⃣ Clear Cart
        CartItem.query.filter_by(user_id=user_id).delete()

        db.session.commit()

        return jsonify({
            "order_id": order.id,
            "status": order.status,
            "message": "Order placed successfully"
        }), 201

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Checkout failed"}), 500

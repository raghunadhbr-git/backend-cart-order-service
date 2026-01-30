from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests

from app.extensions import db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.cart_item import CartItem

checkout_bp = Blueprint("checkout", __name__)

# ============================================================
# 🔁 PRODUCT SERVICE URL (LOCAL FIRST)
# ============================================================

# 👉 LOCAL (USE THIS WHILE TESTING)
PRODUCT_SERVICE_DECREASE_URL = (
    "http://127.0.0.1:5002/api/v1/products/decrease-stock"
)

# 👉 LIVE (COMMENT LOCAL, UNCOMMENT THIS LATER)
# PRODUCT_SERVICE_DECREASE_URL = (
#     "https://backend-product-service.onrender.com/api/v1/products/decrease-stock"
# )


# ============================================================
# 🛒 CHECKOUT → PLACE ORDER → DECREASE STOCK
# ============================================================
@checkout_bp.post("/")
@jwt_required()
def checkout():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify({"error": "Cart is empty"}), 400

    try:
        # ----------------------------------------------------
        # 1️⃣ PREPARE STOCK PAYLOAD (PRODUCT LEVEL)
        # ----------------------------------------------------
        items_payload = [
    {
        "product_id": item.product_id,   # ✅ REQUIRED
        "variant_id": item.variant_id,   # ✅ REQUIRED
        "quantity": item.quantity
    }
    for item in cart_items
]


        # ----------------------------------------------------
        # 2️⃣ CALL PRODUCT SERVICE (STOCK SOURCE OF TRUTH)
        # ----------------------------------------------------
        resp = requests.post(
            PRODUCT_SERVICE_DECREASE_URL,
            json={"items": items_payload},
            headers={
                "Authorization": request.headers.get("Authorization")
            }
        )

        if resp.status_code != 200:
            return jsonify({
                "error": "Insufficient stock or product service error"
            }), 400

        # ----------------------------------------------------
        # 3️⃣ CREATE ORDER
        # ----------------------------------------------------
        order = Order(
            user_id=user_id,
            contact=data["contact"],
            address=data["address"],
            total_price=data["total_price"]
        )
        db.session.add(order)
        db.session.flush()  # get order.id

        # ----------------------------------------------------
        # 4️⃣ CREATE ORDER ITEMS
        # ----------------------------------------------------
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

        # ----------------------------------------------------
        # 5️⃣ CLEAR CART
        # ----------------------------------------------------
        CartItem.query.filter_by(user_id=user_id).delete()

        db.session.commit()

        return jsonify({
            "order_id": order.id,
            "status": order.status,
            "message": "Order placed successfully"
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Checkout failed",
            "details": str(e)
        }), 500

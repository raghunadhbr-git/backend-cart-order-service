from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.cart_item import CartItem

cart_bp = Blueprint("cart", __name__)

# ============================================================
# ADD TO CART
# ============================================================
@cart_bp.post("/")
@jwt_required()
def add_to_cart():
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    item = CartItem(
        user_id=user_id,
        product_id=data["product_id"],     # ✅ FIXED
        variant_id=data["variant_id"],     # ✅ FIXED
        name=data["name"],
        color=data["color"],
        price=data["price"],
        quantity=data["quantity"]
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({"message": "Added to cart"}), 201


# ============================================================
# GET CART
# ============================================================
@cart_bp.get("/")
@jwt_required()
def get_cart():
    user_id = get_jwt_identity()
    items = CartItem.query.filter_by(user_id=user_id).all()

    return jsonify([
        {
            "cart_item_id": i.id,
            "product_id": i.product_id,
            "variant_id": i.variant_id,
            "name": i.name,
            "color": i.color,
            "price": i.price,
            "quantity": i.quantity
        }
        for i in items
    ]), 200

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.cart import CartItem

cart_bp = Blueprint("cart", __name__)

# ============================================================
# ADD TO CART
# ============================================================
@cart_bp.post("/")
@jwt_required()
def add_to_cart():
    user_id = get_jwt_identity()
    data = request.get_json()

    cart_item = CartItem(
        user_id=user_id,
        product_id=data["productId"],
        variant_id=data["variantId"],
        name=data["name"],
        color=data["color"],
        price=data["price"],
        quantity=data["quantity"]
    )

    db.session.add(cart_item)
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
            "id": i.id,
            "product_id": i.product_id,
            "variant_id": i.variant_id,
            "name": i.name,
            "color": i.color,
            "quantity": i.quantity,
            "price": i.price
        } for i in items
    ])

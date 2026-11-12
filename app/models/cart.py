from datetime import datetime
from decimal import Decimal
from app import db


class Cart(db.Model):
    """Shopping cart for authenticated student buyers."""
    __tablename__ = "carts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="cart")
    items = db.relationship("CartItem", back_populates="cart", cascade="all, delete-orphan", lazy="joined")

    @property
    def total_amount(self) -> Decimal:
        return sum((item.subtotal for item in self.items), Decimal("0.00"))

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)

    def clear(self):
        for item in list(self.items):
            db.session.delete(item)

    def __repr__(self):
        return f"<Cart User#{self.user_id} ({self.item_count} items)>"


class CartItem(db.Model):
    """Individual line items within a student's cart."""
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    cart = db.relationship("Cart", back_populates="items")
    product = db.relationship("Product", back_populates="cart_items")

    @property
    def subtotal(self) -> Decimal:
        if self.product:
            return Decimal(str(self.product.price)) * self.quantity
        return Decimal("0.00")

    def __repr__(self):
        return f"<CartItem Cart#{self.cart_id} Product#{self.product_id} x{self.quantity}>"

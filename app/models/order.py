from datetime import datetime
from decimal import Decimal
from app import db


class Order(db.Model):
    """Order placed by a student buyer to purchase one or more items from seller(s)."""
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(40), unique=True, nullable=False, index=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    # Statuses: Pending, Accepted, Ready for Pickup, Completed, Rejected, Cancelled
    status = db.Column(db.String(30), default="Pending", nullable=False, index=True)
    pickup_location = db.Column(db.String(150), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    buyer = db.relationship("User", foreign_keys=[buyer_id], back_populates="orders_placed")
    seller = db.relationship("User", foreign_keys=[seller_id], back_populates="orders_received")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    transaction = db.relationship("Transaction", back_populates="order", uselist=False, cascade="all, delete-orphan")
    complaints = db.relationship("Complaint", back_populates="order", cascade="all, delete-orphan")
    ratings = db.relationship("Rating", back_populates="order", cascade="all, delete-orphan")

    @property
    def status_badge_class(self) -> str:
        mapping = {
            "Pending": "bg-warning text-dark",
            "Accepted": "bg-primary",
            "Ready for Pickup": "bg-info text-dark",
            "Completed": "bg-success",
            "Rejected": "bg-danger",
            "Cancelled": "bg-secondary",
        }
        return mapping.get(self.status, "bg-secondary")

    @property
    def can_be_cancelled(self) -> bool:
        return self.status in ["Pending", "Accepted"]

    @property
    def can_be_rated(self) -> bool:
        return self.status == "Completed" and not self.ratings

    def __repr__(self):
        return f"<Order {self.order_number} ({self.status})>"


class OrderItem(db.Model):
    """Line items belonging to an order."""
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product", back_populates="order_items")

    def __repr__(self):
        return f"<OrderItem Order#{self.order_id} Product#{self.product_id} x{self.quantity}>"

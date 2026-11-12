from datetime import datetime
from app import db


class Inventory(db.Model):
    """Inventory model linked to products for ERP stock tracking and audit."""
    __tablename__ = "inventory"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), unique=True, nullable=False, index=True)
    stock_quantity = db.Column(db.Integer, default=1, nullable=False)
    low_stock_threshold = db.Column(db.Integer, default=2, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    product = db.relationship("Product", back_populates="inventory")

    @property
    def is_low_stock(self) -> bool:
        return 0 < self.stock_quantity <= self.low_stock_threshold

    @property
    def is_out_of_stock(self) -> bool:
        return self.stock_quantity <= 0

    @property
    def stock_status(self) -> str:
        if self.stock_quantity <= 0:
            return "Out of Stock"
        if self.stock_quantity <= self.low_stock_threshold:
            return "Low Stock"
        return "In Stock"

    def __repr__(self):
        return f"<Inventory Product#{self.product_id}: {self.stock_quantity} left>"

from datetime import datetime
from app import db


class Transaction(db.Model):
    """Financial transaction audit log tied to orders in the ERP system."""
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    transaction_number = db.Column(db.String(40), unique=True, nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), unique=True, nullable=False, index=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50), default="Campus UPI", nullable=False)  # 'Campus UPI', 'Cash on Pickup', 'Campus Card'
    payment_status = db.Column(db.String(30), default="Completed", nullable=False)  # 'Completed', 'Pending', 'Refunded'
    is_simulated = db.Column(db.Boolean, default=True, nullable=False)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    order = db.relationship("Order", back_populates="transaction")
    buyer = db.relationship("User", foreign_keys=[buyer_id])
    seller = db.relationship("User", foreign_keys=[seller_id])

    @property
    def status_badge_class(self) -> str:
        mapping = {
            "Completed": "bg-success",
            "Pending": "bg-warning text-dark",
            "Refunded": "bg-info text-dark",
            "Failed": "bg-danger",
        }
        return mapping.get(self.payment_status, "bg-secondary")

    def __repr__(self):
        return f"<Transaction {self.transaction_number} (₹{self.amount} - {self.payment_status})>"

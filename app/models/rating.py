from datetime import datetime
from app import db


class Rating(db.Model):
    """Product reviews and ratings submitted by student buyers."""
    __tablename__ = "ratings"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True, index=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False)  # 1 to 5
    review_text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    product = db.relationship("Product", back_populates="ratings")
    order = db.relationship("Order", back_populates="ratings")
    buyer = db.relationship("User", foreign_keys=[buyer_id], back_populates="ratings")

    def __repr__(self):
        return f"<Rating Product#{self.product_id} Score:{self.score}/5>"

from datetime import datetime
from app import db


class Complaint(db.Model):
    """Complaints and dispute tickets lodged by students."""
    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(40), unique=True, nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    subject = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default="Pending", nullable=False)  # 'Pending', 'Under Review', 'Resolved', 'Rejected'
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    order = db.relationship("Order", back_populates="complaints")
    student = db.relationship("User", foreign_keys=[student_id], back_populates="complaints")

    @property
    def status_badge_class(self) -> str:
        mapping = {
            "Pending": "bg-warning text-dark",
            "Under Review": "bg-info text-dark",
            "Resolved": "bg-success",
            "Rejected": "bg-danger",
        }
        return mapping.get(self.status, "bg-secondary")

    def __repr__(self):
        return f"<Complaint {self.ticket_number} ({self.status})>"

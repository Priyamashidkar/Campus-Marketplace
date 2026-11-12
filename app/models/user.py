from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    """User model representing students (buyers & sellers) and administrators."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(30), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    campus_block = db.Column(db.String(100), nullable=True)  # e.g., "Hostel H-3, Room 204"
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    products = db.relationship("Product", back_populates="seller", cascade="all, delete-orphan", lazy="dynamic")
    orders_placed = db.relationship("Order", foreign_keys="Order.buyer_id", back_populates="buyer", lazy="dynamic")
    orders_received = db.relationship("Order", foreign_keys="Order.seller_id", back_populates="seller", lazy="dynamic")
    cart = db.relationship("Cart", back_populates="user", uselist=False, cascade="all, delete-orphan")
    complaints = db.relationship("Complaint", foreign_keys="Complaint.student_id", back_populates="student", lazy="dynamic")
    ratings = db.relationship("Rating", foreign_keys="Rating.buyer_id", back_populates="buyer", lazy="dynamic")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def role_title(self) -> str:
        if self.is_admin:
            return "Administrator"
        return "Student"

    def __repr__(self):
        return f"<User {self.email} ({self.student_id})>"

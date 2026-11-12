from datetime import datetime
from app import db


class Category(db.Model):
    """Category model for marketplace product classification."""
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    slug = db.Column(db.String(60), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)
    icon = db.Column(db.String(50), default="bi-tag")
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    products = db.relationship("Product", back_populates="category", lazy="dynamic")

    def __repr__(self):
        return f"<Category {self.name}>"


class Product(db.Model):
    """Product model for items listed by student sellers."""
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    condition = db.Column(db.String(30), default="Good")  # 'Brand New', 'Like New', 'Good', 'Fair'
    image_url = db.Column(db.String(255), default="default_product.png")
    status = db.Column(db.String(20), default="active", nullable=False)  # 'active', 'out_of_stock', 'deactivated'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    seller = db.relationship("User", back_populates="products")
    category = db.relationship("Category", back_populates="products")
    inventory = db.relationship("Inventory", back_populates="product", uselist=False, cascade="all, delete-orphan")
    cart_items = db.relationship("CartItem", back_populates="product", cascade="all, delete-orphan")
    order_items = db.relationship("OrderItem", back_populates="product")
    ratings = db.relationship("Rating", back_populates="product", cascade="all, delete-orphan")

    @property
    def stock_quantity(self) -> int:
        return self.inventory.stock_quantity if self.inventory else 0

    @property
    def is_available(self) -> bool:
        return self.status == "active" and self.stock_quantity > 0

    @property
    def average_rating(self) -> float:
        if not self.ratings:
            return 0.0
        scores = [r.score for r in self.ratings]
        return round(sum(scores) / len(scores), 1)

    @property
    def total_reviews(self) -> int:
        return len(self.ratings) if self.ratings else 0

    def __repr__(self):
        return f"<Product {self.title} (₹{self.price})>"

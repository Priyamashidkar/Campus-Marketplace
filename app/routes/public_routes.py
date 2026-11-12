from flask import Blueprint, render_template
from app.models.product import Product, Category
from app.models.rating import Rating

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def index():
    """Landing page showcasing campus marketplace, featured items, and statistics."""
    categories = Category.query.filter_by(is_active=True).all()
    featured_products = (
        Product.query.filter_by(status="active")
        .order_by(Product.created_at.desc())
        .limit(8)
        .all()
    )
    latest_reviews = (
        Rating.query.order_by(Rating.created_at.desc())
        .limit(4)
        .all()
    )
    return render_template(
        "public/index.html",
        categories=categories,
        featured_products=featured_products,
        latest_reviews=latest_reviews,
    )


@public_bp.route("/about")
def about():
    """About Campus Marketplace, university safety policies, and ERP operations."""
    return render_template("public/about.html")

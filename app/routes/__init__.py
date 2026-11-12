from app.routes.auth_routes import auth_bp
from app.routes.public_routes import public_bp
from app.routes.student_routes import student_bp
from app.routes.seller_routes import seller_bp
from app.routes.admin_routes import admin_bp

__all__ = [
    "auth_bp",
    "public_bp",
    "student_bp",
    "seller_bp",
    "admin_bp",
]

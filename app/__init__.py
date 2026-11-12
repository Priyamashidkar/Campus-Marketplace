from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_name="default"):
    """Application factory for Campus Marketplace."""
    from config import config_by_name

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Ensure uploads folder exists
    upload_path = Path(app.config["UPLOAD_FOLDER"])
    upload_path.mkdir(parents=True, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    # User loader callback
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Context processors for global template variables (e.g., cart count, categories)
    @app.context_processor
    def inject_global_data():
        from flask_login import current_user
        from app.models.product import Category
        from app.models.cart import Cart

        cart_count = 0
        if current_user.is_authenticated and not current_user.is_admin:
            cart = Cart.query.filter_by(user_id=current_user.id).first()
            if cart:
                cart_count = cart.item_count

        nav_categories = Category.query.filter_by(is_active=True).all()
        return dict(
            cart_count=cart_count,
            nav_categories=nav_categories,
        )

    # Register Blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.public_routes import public_bp
    from app.routes.student_routes import student_bp
    from app.routes.seller_routes import seller_bp
    from app.routes.admin_routes import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(seller_bp, url_prefix="/seller")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    return app

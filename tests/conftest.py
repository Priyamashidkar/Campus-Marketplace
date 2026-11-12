import pytest
from decimal import Decimal
from datetime import datetime
from app import create_app, db
from app.models.user import User
from app.models.product import Category, Product
from app.models.inventory import Inventory
from app.models.cart import Cart
from app.services.inventory_service import InventoryService


@pytest.fixture
def app():
    """Create test application instance with in-memory database."""
    app = create_app("testing")

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test HTTP client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture
def admin_user(app):
    """Administrator fixture."""
    admin = User(
        student_id="ADMIN001",
        full_name="System Administrator",
        email="admin@campus.edu",
        is_admin=True,
        is_active=True,
    )
    admin.set_password("Admin@123")
    db.session.add(admin)
    db.session.commit()
    return admin


@pytest.fixture
def student_seller(app):
    """Student seller fixture."""
    seller = User(
        student_id="CS2024001",
        full_name="Aarav Seller",
        email="seller@campus.edu",
        campus_block="Hostel H-3",
        is_admin=False,
        is_active=True,
    )
    seller.set_password("Student@123")
    db.session.add(seller)
    db.session.flush()

    cart = Cart(user_id=seller.id)
    db.session.add(cart)
    db.session.commit()
    return seller


@pytest.fixture
def student_buyer(app):
    """Student buyer fixture."""
    buyer = User(
        student_id="CS2024002",
        full_name="Priya Buyer",
        email="buyer@campus.edu",
        campus_block="Hostel H-5",
        is_admin=False,
        is_active=True,
    )
    buyer.set_password("Student@123")
    db.session.add(buyer)
    db.session.flush()

    cart = Cart(user_id=buyer.id)
    db.session.add(cart)
    db.session.commit()
    return buyer


@pytest.fixture
def sample_category(app):
    """Category fixture."""
    cat = Category(name="Textbooks", slug="textbooks", description="Academic course books", icon="bi-book", is_active=True)
    db.session.add(cat)
    db.session.commit()
    return cat


@pytest.fixture
def sample_product(app, student_seller, sample_category):
    """Product fixture with 3 units of stock."""
    prod = Product(
        seller_id=student_seller.id,
        category_id=sample_category.id,
        title="Engineering Mathematics Test Edition",
        description="Textbook in great condition for second semester.",
        price=Decimal("400.00"),
        condition="Good",
        image_url="default_product.png",
        status="active",
    )
    db.session.add(prod)
    db.session.flush()

    InventoryService.initialize_inventory(prod, initial_quantity=3, low_threshold=1)
    db.session.commit()
    return prod

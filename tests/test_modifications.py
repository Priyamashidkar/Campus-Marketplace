from app import db
from app.models.user import User
from app.models.product import Product
from app.models.order import Order


def test_change1_admin_login_credentials_box_removed(client, admin_user):
    """CHANGE 1: Verify default administrator credentials box is removed from admin login page."""
    resp = client.get("/auth/admin-login")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    # The visible default credentials box must be completely removed
    assert "Default Administrator Credentials" not in html
    assert "Admin@123" not in html
    assert "Default Administrator Credentials:" not in html

    # Existing form elements must remain intact
    assert "Administrator Email" in html
    assert "Administrator Password" in html
    assert "Access ERP Control Center" in html
    assert "name=\"email\"" in html
    assert "name=\"password\"" in html

    # Admin authentication must continue to function properly
    login_resp = client.post("/auth/admin-login", data={
        "email": admin_user.email,
        "password": "Admin@123",
    }, follow_redirects=True)
    assert login_resp.status_code == 200
    assert "ERP Control Center & Analytics" in login_resp.data.decode("utf-8")


def test_change2_dashboard_dispute_tickets_section_removed(client, admin_user, sample_product):
    """CHANGE 2: Verify Recent Dispute Tickets section is removed from ERP dashboard."""
    client.post("/auth/admin-login", data={
        "email": admin_user.email,
        "password": "Admin@123",
    })

    dash_resp = client.get("/admin/dashboard")
    assert dash_resp.status_code == 200
    html = dash_resp.data.decode("utf-8")

    # Recent Dispute Tickets section, its heading, and Review All button must be removed from dashboard
    assert "Recent Dispute Tickets" not in html
    assert "Review All" not in html

    # Other ERP dashboard sections must remain intact
    assert "ERP Control Center & Analytics" in html
    assert "Monthly Marketplace Trends" in html
    assert "Category Distribution" in html
    assert "Recent Marketplace Orders" in html
    assert "Low-Stock Inventory Alerts" in html

    # Complaints route itself must remain intact and functional
    comp_resp = client.get("/admin/complaints")
    assert comp_resp.status_code == 200
    assert "Complaint & Dispute Ticket Center" in comp_resp.data.decode("utf-8")


def test_change3_dark_mode_applied_across_pages(client, student_buyer, admin_user, sample_product):
    """CHANGE 3: Verify dark mode is applied across pages and centralized CSS variables exist."""
    # 1. Base template has data-bs-theme="dark"
    pages_to_check = [
        "/",
        "/about",
        "/auth/login",
        "/auth/register",
        "/auth/admin-login",
        "/student/marketplace",
        f"/student/product/{sample_product.id}",
    ]

    for page in pages_to_check:
        resp = client.get(page)
        assert resp.status_code == 200, f"Failed loading {page}"
        html = resp.data.decode("utf-8")
        assert 'data-bs-theme="dark"' in html, f"data-bs-theme='dark' missing from {page}"
        assert 'custom.css' in html, f"custom.css link missing from {page}"

    # 2. Authenticated Student Pages
    client.post("/auth/login", data={"email": student_buyer.email, "password": "Student@123"})
    # Add an item to cart so /student/checkout does not redirect
    client.post(f"/student/cart/add/{sample_product.id}", data={"quantity": 1})

    student_pages = [
        "/student/cart",
        "/student/checkout",
        "/student/my-orders",
        "/student/profile",
        "/student/complaints",
        "/seller/dashboard",
        "/seller/products",
        "/seller/products/add",
        "/seller/orders",
        "/seller/sales-history",
    ]
    for page in student_pages:
        resp = client.get(page)
        assert resp.status_code == 200, f"Failed loading {page}"
        html = resp.data.decode("utf-8")
        assert 'data-bs-theme="dark"' in html, f"data-bs-theme='dark' missing from {page}"

    client.get("/auth/logout")

    # 3. Authenticated Admin Pages
    client.post("/auth/admin-login", data={"email": admin_user.email, "password": "Admin@123"})
    admin_pages = [
        "/admin/dashboard",
        "/admin/inventory",
        "/admin/orders",
        "/admin/transactions",
        "/admin/users",
        "/admin/products",
        "/admin/categories",
        "/admin/complaints",
        "/admin/reports",
    ]
    for page in admin_pages:
        resp = client.get(page)
        assert resp.status_code == 200, f"Failed loading {page}"
        html = resp.data.decode("utf-8")
        assert 'data-bs-theme="dark"' in html, f"data-bs-theme='dark' missing from {page}"


def test_dark_mode_css_palette():
    """Verify that custom.css defines the requested color palette."""
    with open("app/static/css/custom.css", "r") as f:
        css = f.read()

    expected_colors = [
        ("#0F1117", "Main page background"),
        ("#161B22", "Secondary background"),
        ("#1C2330", "Cards and panels"),
        ("#252D3A", "Input backgrounds"),
        ("#F1F5F9", "Primary text"),
        ("#AAB4C3", "Secondary text"),
        ("#303B4B", "Borders"),
        ("#3B82F6", "Primary accent"),
        ("#14B8A6", "Secondary accent"),
        ("#22C55E", "Success"),
        ("#F59E0B", "Warning"),
        ("#EF4444", "Error"),
    ]

    for color, name in expected_colors:
        assert color in css or color.lower() in css.lower(), f"Expected color {color} ({name}) not found in custom.css"

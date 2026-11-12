from app.models.product import Product


def test_product_listing_and_inventory_init(client, student_seller, sample_category, app):
    """Verify seller can add a product and linked inventory is created."""
    client.post("/auth/login", data={"email": student_seller.email, "password": "Student@123"})

    response = client.post("/seller/products/add", data={
        "title": "Digital Electronics Lab Manual",
        "category_id": sample_category.id,
        "price": "180.00",
        "quantity": "4",
        "condition": "Like New",
        "description": "Lab manual with verified circuit diagrams.",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"listed successfully" in response.data

    with app.app_context():
        p = Product.query.filter_by(title="Digital Electronics Lab Manual").first()
        assert p is not None
        assert p.price == 180.00
        assert p.stock_quantity == 4
        assert p.inventory.low_stock_threshold == 2
        assert p.status == "active"


def test_product_searching(client, sample_product):
    """Test keyword searching in marketplace."""
    # Search for matching keyword
    resp_match = client.get("/student/marketplace?q=Mathematics")
    assert b"Engineering Mathematics Test Edition" in resp_match.data

    # Search for non-matching keyword
    resp_no_match = client.get("/student/marketplace?q=AstronomyRocketScience")
    assert b"No products match your criteria" in resp_no_match.data


def test_category_and_price_filtering(client, sample_product, sample_category):
    """Test filtering by category slug and price bounds."""
    # Filter by category
    resp_cat = client.get(f"/student/marketplace?category={sample_category.slug}")
    assert b"Engineering Mathematics Test Edition" in resp_cat.data

    # Filter with price bound that includes product (price=400)
    resp_price_in = client.get("/student/marketplace?min_price=100&max_price=500")
    assert b"Engineering Mathematics Test Edition" in resp_price_in.data

    # Filter with price bound that excludes product
    resp_price_out = client.get("/student/marketplace?min_price=500&max_price=1000")
    assert b"No products match your criteria" in resp_price_out.data


def test_product_detail_view(client, sample_product):
    """Test product detail page rendering with seller and stock information."""
    resp = client.get(f"/student/product/{sample_product.id}")
    assert resp.status_code == 200
    assert b"Engineering Mathematics Test Edition" in resp.data
    assert b"Student ID:" in resp.data
    assert b"In Stock" in resp.data

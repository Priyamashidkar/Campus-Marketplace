from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func, desc
from app import db
from app.models.user import User
from app.models.product import Product, Category
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem
from app.models.transaction import Transaction
from app.models.complaint import Complaint
from app.models.rating import Rating


class ERPService:
    """Service providing aggregate analytics, KPI calculations, and data for the ERP dashboard."""

    @staticmethod
    def get_summary_kpis() -> dict:
        """Fetch summary KPIs for the ERP Executive Dashboard."""
        total_students = User.query.filter_by(is_admin=False).count()
        active_students = User.query.filter_by(is_admin=False, is_active=True).count()

        # Count distinct sellers (students with at least 1 product listed)
        total_sellers = db.session.query(func.count(func.distinct(Product.seller_id))).scalar() or 0

        total_products = Product.query.count()
        active_products = Product.query.filter_by(status="active").count()

        total_orders = Order.query.count()
        pending_orders = Order.query.filter_by(status="Pending").count()
        completed_orders = Order.query.filter_by(status="Completed").count()
        cancelled_orders = Order.query.filter(Order.status.in_(["Cancelled", "Rejected"])).count()

        # Total transaction value (from completed or all non-refunded transactions)
        total_txn_val = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.payment_status.in_(["Completed", "Pending"])
        ).scalar() or Decimal("0.00")

        # Inventory health
        low_stock_count = Inventory.query.filter(
            Inventory.stock_quantity <= Inventory.low_stock_threshold,
            Inventory.stock_quantity > 0
        ).count()
        out_of_stock_count = Inventory.query.filter(Inventory.stock_quantity <= 0).count()

        # Complaints summary
        total_complaints = Complaint.query.count()
        pending_complaints = Complaint.query.filter(Complaint.status.in_(["Pending", "Under Review"])).count()

        return {
            "total_students": total_students,
            "active_students": active_students,
            "total_sellers": total_sellers,
            "total_products": total_products,
            "active_products": active_products,
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "completed_orders": completed_orders,
            "cancelled_orders": cancelled_orders,
            "total_transaction_value": float(total_txn_val),
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "total_complaints": total_complaints,
            "pending_complaints": pending_complaints,
        }

    @staticmethod
    def get_monthly_order_trends(months: int = 6) -> dict:
        """
        Aggregate order counts and sales amounts over the past months for Chart.js.
        Works across SQLite and MySQL.
        """
        end_date = datetime.utcnow()
        # Create monthly buckets
        labels = []
        counts = []
        values = []

        for i in range(months - 1, -1, -1):
            target_date = end_date - timedelta(days=i * 30)
            month_label = target_date.strftime("%b %Y")
            labels.append(month_label)

            month_start = datetime(target_date.year, target_date.month, 1)
            if target_date.month == 12:
                next_month = datetime(target_date.year + 1, 1, 1)
            else:
                next_month = datetime(target_date.year, target_date.month + 1, 1)

            month_orders = Order.query.filter(
                Order.created_at >= month_start,
                Order.created_at < next_month
            ).all()

            order_count = len(month_orders)
            sales_val = sum(o.total_amount for o in month_orders if o.status != "Cancelled" and o.status != "Rejected")

            counts.append(order_count)
            values.append(float(sales_val))

        return {
            "labels": labels,
            "order_counts": counts,
            "sales_values": values,
        }

    @staticmethod
    def get_category_distribution() -> dict:
        """Get product count and gross sales per product category."""
        categories = Category.query.all()
        labels = []
        product_counts = []
        sales_values = []

        for cat in categories:
            labels.append(cat.name)
            p_count = Product.query.filter_by(category_id=cat.id).count()
            product_counts.append(p_count)

            # Sum total sales from order items in this category
            sales_for_cat = (
                db.session.query(func.sum(OrderItem.subtotal))
                .join(Product, OrderItem.product_id == Product.id)
                .join(Order, OrderItem.order_id == Order.id)
                .filter(Product.category_id == cat.id, Order.status == "Completed")
                .scalar()
                or Decimal("0.00")
            )
            sales_values.append(float(sales_for_cat))

        return {
            "labels": labels,
            "product_counts": product_counts,
            "sales_values": sales_values,
        }

    @staticmethod
    def get_inventory_status_breakdown() -> dict:
        """Categorize inventory into Healthy (in stock), Low Stock, and Out of Stock."""
        healthy_count = Inventory.query.filter(Inventory.stock_quantity > Inventory.low_stock_threshold).count()
        low_stock_count = Inventory.query.filter(
            Inventory.stock_quantity <= Inventory.low_stock_threshold,
            Inventory.stock_quantity > 0
        ).count()
        out_of_stock_count = Inventory.query.filter(Inventory.stock_quantity <= 0).count()

        return {
            "labels": ["Healthy Stock", "Low Stock Alert", "Out of Stock"],
            "data": [healthy_count, low_stock_count, out_of_stock_count],
            "colors": ["#10b981", "#f59e0b", "#ef4444"],
        }

    @staticmethod
    def get_top_selling_products(limit: int = 5):
        """Retrieve top products by total units sold."""
        results = (
            db.session.query(
                Product,
                func.sum(OrderItem.quantity).label("units_sold"),
                func.sum(OrderItem.subtotal).label("total_revenue")
            )
            .join(OrderItem, Product.id == OrderItem.product_id)
            .join(Order, OrderItem.order_id == Order.id)
            .filter(Order.status == "Completed")
            .group_by(Product.id)
            .order_by(desc("units_sold"))
            .limit(limit)
            .all()
        )
        return results

    @staticmethod
    def get_recent_activities(limit: int = 6):
        """Fetch latest orders and complaints for the ERP dashboard."""
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(limit).all()
        recent_complaints = Complaint.query.order_by(Complaint.created_at.desc()).limit(limit).all()
        low_stock_items = (
            Inventory.query.join(Product)
            .filter(Inventory.stock_quantity <= Inventory.low_stock_threshold)
            .order_by(Inventory.stock_quantity.asc())
            .limit(limit)
            .all()
        )
        return {
            "recent_orders": recent_orders,
            "recent_complaints": recent_complaints,
            "low_stock_items": low_stock_items,
        }

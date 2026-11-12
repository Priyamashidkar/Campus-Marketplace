from datetime import datetime
from app import db
from app.models.inventory import Inventory
from app.models.product import Product


class InventoryService:
    """Service handling stock mutations, reservation, replenishment, and audits."""

    @staticmethod
    def initialize_inventory(product: Product, initial_quantity: int = 1, low_threshold: int = 2) -> Inventory:
        """Create initial inventory record for a newly listed product."""
        inventory = Inventory(
            product_id=product.id,
            stock_quantity=max(0, initial_quantity),
            low_stock_threshold=low_threshold,
            last_updated=datetime.utcnow(),
        )
        db.session.add(inventory)
        # Update product status according to initial quantity
        if initial_quantity <= 0:
            product.status = "out_of_stock"
        else:
            product.status = "active"
        return inventory

    @staticmethod
    def check_availability(product_id: int, requested_quantity: int) -> tuple[bool, int, str]:
        """Check if requested quantity is available in stock. Returns (available, current_stock, message)."""
        inventory = Inventory.query.filter_by(product_id=product_id).first()
        if not inventory:
            return False, 0, "Product inventory record not found."

        if inventory.stock_quantity < requested_quantity:
            return False, inventory.stock_quantity, f"Only {inventory.stock_quantity} item(s) left in stock."

        return True, inventory.stock_quantity, "Available"

    @staticmethod
    def deduct_stock(product_id: int, quantity: int) -> bool:
        """
        Deduct quantity from product inventory.
        Must be called within an active DB transaction.
        """
        inventory = Inventory.query.filter_by(product_id=product_id).with_for_update().first()
        if not inventory or inventory.stock_quantity < quantity:
            return False

        inventory.stock_quantity -= quantity
        inventory.last_updated = datetime.utcnow()

        # Update product status if stock exhausted
        if inventory.stock_quantity <= 0:
            inventory.product.status = "out_of_stock"

        return True

    @staticmethod
    def restore_stock(product_id: int, quantity: int) -> bool:
        """
        Restore quantity to product inventory upon order cancellation/rejection.
        """
        inventory = Inventory.query.filter_by(product_id=product_id).with_for_update().first()
        if not inventory:
            return False

        inventory.stock_quantity += quantity
        inventory.last_updated = datetime.utcnow()

        # Reactivate product if it was marked out_of_stock
        if inventory.stock_quantity > 0 and inventory.product.status == "out_of_stock":
            inventory.product.status = "active"

        return True

    @staticmethod
    def update_stock(product_id: int, new_quantity: int, new_threshold: int = None) -> bool:
        """Admin or seller update to stock quantity and threshold."""
        inventory = Inventory.query.filter_by(product_id=product_id).first()
        if not inventory:
            return False

        inventory.stock_quantity = max(0, new_quantity)
        if new_threshold is not None and new_threshold >= 0:
            inventory.low_stock_threshold = new_threshold
        inventory.last_updated = datetime.utcnow()

        if inventory.stock_quantity <= 0:
            inventory.product.status = "out_of_stock"
        elif inventory.product.status == "out_of_stock":
            inventory.product.status = "active"

        db.session.commit()
        return True

    @staticmethod
    def get_low_stock_items():
        """Retrieve all inventory items where stock <= threshold and > 0."""
        return (
            Inventory.query.join(Product)
            .filter(Inventory.stock_quantity <= Inventory.low_stock_threshold, Inventory.stock_quantity > 0)
            .all()
        )

    @staticmethod
    def get_out_of_stock_items():
        """Retrieve all inventory items with 0 stock."""
        return Inventory.query.join(Product).filter(Inventory.stock_quantity <= 0).all()

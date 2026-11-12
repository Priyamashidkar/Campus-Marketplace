import uuid
from datetime import datetime
from decimal import Decimal
from collections import defaultdict
from app import db
from app.models.order import Order, OrderItem
from app.models.transaction import Transaction
from app.models.cart import Cart
from app.services.inventory_service import InventoryService


class OrderService:
    """Service orchestrating cart checkout, order placement, transactions, and status workflows."""

    @staticmethod
    def generate_order_number() -> str:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        unique_suffix = uuid.uuid4().hex[:6].upper()
        return f"ORD-{date_str}-{unique_suffix}"

    @staticmethod
    def generate_transaction_number() -> str:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        unique_suffix = uuid.uuid4().hex[:6].upper()
        return f"TXN-{date_str}-{unique_suffix}"

    @classmethod
    def checkout_cart(
        cls,
        buyer_id: int,
        pickup_location: str,
        payment_method: str = "Campus UPI",
        notes: str = "",
    ) -> tuple[bool, list[Order], str]:
        """
        Process checkout from a student buyer's cart.
        Atomically validates inventory, reserves stock, creates orders (grouped per seller),
        and creates simulated transaction records.
        Returns (success, created_orders, message).
        """
        cart = Cart.query.filter_by(user_id=buyer_id).first()
        if not cart or not cart.items:
            return False, [], "Your shopping cart is empty."

        # Group items by seller
        seller_items = defaultdict(list)
        for item in cart.items:
            if not item.product:
                continue

            # Cannot buy own product
            if item.product.seller_id == buyer_id:
                return False, [], f"You cannot buy your own product: '{item.product.title}'."

            # Check stock availability
            avail, current_stock, msg = InventoryService.check_availability(item.product_id, item.quantity)
            if not avail:
                return False, [], f"Cannot place order for '{item.product.title}': {msg}"

            seller_items[item.product.seller_id].append(item)

        created_orders = []

        try:
            for seller_id, items in seller_items.items():
                # Compute seller subtotal
                order_total = sum((Decimal(str(item.product.price)) * item.quantity for item in items), Decimal("0.00"))
                order_num = cls.generate_order_number()

                order = Order(
                    order_number=order_num,
                    buyer_id=buyer_id,
                    seller_id=seller_id,
                    total_amount=order_total,
                    status="Pending",
                    pickup_location=pickup_location,
                    notes=notes,
                    created_at=datetime.utcnow(),
                )
                db.session.add(order)
                db.session.flush()  # obtain order.id

                # Create OrderItems and deduct inventory atomically
                for item in items:
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=item.product_id,
                        quantity=item.quantity,
                        unit_price=item.product.price,
                        subtotal=Decimal(str(item.product.price)) * item.quantity,
                    )
                    db.session.add(order_item)

                    # Deduct stock
                    stock_deducted = InventoryService.deduct_stock(item.product_id, item.quantity)
                    if not stock_deducted:
                        db.session.rollback()
                        return False, [], f"Stock depleted for '{item.product.title}' during checkout. Please adjust quantity."

                # Create Simulated Transaction record
                txn_num = cls.generate_transaction_number()
                payment_status = "Completed" if payment_method in ["Campus UPI", "Campus Card"] else "Pending"
                transaction = Transaction(
                    transaction_number=txn_num,
                    order_id=order.id,
                    buyer_id=buyer_id,
                    seller_id=seller_id,
                    amount=order_total,
                    payment_method=payment_method,
                    payment_status=payment_status,
                    is_simulated=True,
                    transaction_date=datetime.utcnow(),
                )
                db.session.add(transaction)
                created_orders.append(order)

            # Clear buyer's cart after successful order creation
            cart.clear()
            db.session.commit()
            return True, created_orders, f"Successfully placed {len(created_orders)} order(s)!"

        except Exception as e:
            db.session.rollback()
            return False, [], f"Order placement failed: {str(e)}"

    @classmethod
    def update_order_status(cls, order_id: int, new_status: str, actor_id: int, is_admin: bool = False) -> tuple[bool, str]:
        """
        Validate and update order status according to permitted state transitions.
        Restores stock if order is cancelled or rejected.
        """
        order = db.session.get(Order, order_id)
        if not order:
            return False, "Order not found."

        # Authorization: must be seller, buyer (for cancel), or admin
        is_seller = order.seller_id == actor_id
        is_buyer = order.buyer_id == actor_id

        if not (is_admin or is_seller or is_buyer):
            return False, "You do not have permission to modify this order."

        current_status = order.status
        allowed_transitions = {
            "Pending": ["Accepted", "Rejected", "Cancelled"],
            "Accepted": ["Ready for Pickup", "Cancelled"],
            "Ready for Pickup": ["Completed", "Cancelled"],
            "Completed": [],
            "Rejected": [],
            "Cancelled": [],
        }

        # Buyers can only transition to 'Cancelled' while Pending or Accepted
        if is_buyer and not (is_admin or is_seller):
            if new_status != "Cancelled" or current_status not in ["Pending", "Accepted"]:
                return False, "Buyers can only cancel orders that are Pending or Accepted."

        # Sellers can accept, reject, mark ready, or complete
        if is_seller and not is_admin:
            if new_status not in allowed_transitions.get(current_status, []):
                return False, f"Cannot transition order from '{current_status}' to '{new_status}'."

        # Admin can override any transition except completed
        if is_admin and current_status == "Completed" and new_status != "Completed":
            return False, "Completed orders cannot be modified."

        # If transitioning to Cancelled or Rejected, restore inventory
        if new_status in ["Cancelled", "Rejected"] and current_status not in ["Cancelled", "Rejected"]:
            for item in order.items:
                InventoryService.restore_stock(item.product_id, item.quantity)
            if order.transaction:
                order.transaction.payment_status = "Refunded" if order.transaction.payment_status == "Completed" else "Failed"

        # If marked completed, confirm transaction is completed
        if new_status == "Completed" and order.transaction:
            order.transaction.payment_status = "Completed"

        order.status = new_status
        order.updated_at = datetime.utcnow()
        db.session.commit()
        return True, f"Order {order.order_number} status updated to '{new_status}'."

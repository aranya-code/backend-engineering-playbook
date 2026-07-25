"""Celery tasks for background job processing."""

from celery import Celery
from app.config import settings

# Initialize Celery
celery_app = Celery(
    "fastapi_redis_lab",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
)


@celery_app.task(name="send_welcome_email")
def send_welcome_email(email: str, user_name: str) -> dict:
    """
    Send welcome email (simulated).
    
    Args:
        email: User email
        user_name: User name
        
    Returns:
        dict: Task result
    """
    import time
    
    print(f"Sending welcome email to {email}...")
    time.sleep(2)  # Simulate email sending
    
    return {
        "status": "success",
        "email": email,
        "user_name": user_name,
        "message": "Welcome email sent successfully"
    }


@celery_app.task(name="send_order_confirmation")
def send_order_confirmation(email: str, order_id: int, total: float) -> dict:
    """
    Send order confirmation email (simulated).
    
    Args:
        email: User email
        order_id: Order ID
        total: Order total
        
    Returns:
        dict: Task result
    """
    import time
    
    print(f"Sending order confirmation for order #{order_id} to {email}...")
    time.sleep(2)  # Simulate email sending
    
    return {
        "status": "success",
        "email": email,
        "order_id": order_id,
        "total": total,
        "message": f"Order confirmation sent for order #{order_id}"
    }


@celery_app.task(name="process_payment")
def process_payment(order_id: int, amount: float, payment_method: str) -> dict:
    """
    Process payment (simulated).
    
    Args:
        order_id: Order ID
        amount: Payment amount
        payment_method: Payment method
        
    Returns:
        dict: Task result
    """
    import time
    
    print(f"Processing payment for order #{order_id}: ${amount} via {payment_method}...")
    time.sleep(3)  # Simulate payment processing
    
    return {
        "status": "success",
        "order_id": order_id,
        "amount": amount,
        "payment_method": payment_method,
        "transaction_id": f"TXN{order_id}{int(time.time())}",
        "message": "Payment processed successfully"
    }


@celery_app.task(name="generate_report")
def generate_report(report_type: str, date_range: dict) -> dict:
    """
    Generate report (simulated).
    
    Args:
        report_type: Type of report
        date_range: Date range for report
        
    Returns:
        dict: Task result
    """
    import time
    
    print(f"Generating {report_type} report for {date_range}...")
    time.sleep(5)  # Simulate report generation
    
    return {
        "status": "success",
        "report_type": report_type,
        "date_range": date_range,
        "file_url": f"/reports/{report_type}_{int(time.time())}.pdf",
        "message": f"{report_type} report generated successfully"
    }


@celery_app.task(name="update_product_inventory")
def update_product_inventory(product_id: int, quantity: int) -> dict:
    """
    Update product inventory (simulated).
    
    Args:
        product_id: Product ID
        quantity: Quantity to add/subtract
        
    Returns:
        dict: Task result
    """
    import time
    
    print(f"Updating inventory for product #{product_id}: {quantity:+d}...")
    time.sleep(1)  # Simulate inventory update
    
    return {
        "status": "success",
        "product_id": product_id,
        "quantity_changed": quantity,
        "message": f"Inventory updated for product #{product_id}"
    }


@celery_app.task(name="send_notification")
def send_notification(user_id: int, title: str, message: str, notification_type: str = "info") -> dict:
    """
    Send notification (simulated).
    
    Args:
        user_id: User ID
        title: Notification title
        message: Notification message
        notification_type: Type of notification
        
    Returns:
        dict: Task result
    """
    import time
    
    print(f"Sending {notification_type} notification to user #{user_id}: {title}...")
    time.sleep(1)  # Simulate notification sending
    
    return {
        "status": "success",
        "user_id": user_id,
        "title": title,
        "message": message,
        "notification_type": notification_type,
        "sent_at": time.time()
    }


@celery_app.task(name="cleanup_old_carts")
def cleanup_old_carts() -> dict:
    """
    Cleanup old abandoned carts (simulated).
    
    Returns:
        dict: Task result
    """
    import time
    
    print("Cleaning up old abandoned carts...")
    time.sleep(2)  # Simulate cleanup
    
    # In real implementation, this would:
    # 1. Query Redis for old cart keys
    # 2. Delete carts older than X days
    # 3. Return count of cleaned carts
    
    return {
        "status": "success",
        "carts_cleaned": 15,
        "message": "Old carts cleaned successfully"
    }


@celery_app.task(name="sync_cache_with_db")
def sync_cache_with_db() -> dict:
    """
    Sync cache with database (simulated).
    
    Returns:
        dict: Task result
    """
    import time
    
    print("Syncing cache with database...")
    time.sleep(3)  # Simulate sync
    
    return {
        "status": "success",
        "records_synced": 1250,
        "message": "Cache synced with database successfully"
    }

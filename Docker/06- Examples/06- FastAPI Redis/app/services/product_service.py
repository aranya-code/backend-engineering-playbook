import time
from models.product import PRODUCTS
def load_products():
    print("Cache miss.")
    time.sleep(5)
    return PRODUCTS

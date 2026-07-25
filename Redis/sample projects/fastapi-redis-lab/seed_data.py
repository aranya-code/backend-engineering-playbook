"""Seed database with sample data."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models import Product, Base
from app.config import settings

# Sample products
SAMPLE_PRODUCTS = [
    {
        "name": "Gaming Laptop",
        "description": "High-performance laptop with RTX 4080 GPU",
        "price": 2499.99,
        "stock": 15,
        "category": "Electronics"
    },
    {
        "name": "Wireless Mouse",
        "description": "Ergonomic wireless mouse with precision tracking",
        "price": 49.99,
        "stock": 100,
        "category": "Electronics"
    },
    {
        "name": "Mechanical Keyboard",
        "description": "RGB mechanical keyboard with Cherry MX switches",
        "price": 149.99,
        "stock": 50,
        "category": "Electronics"
    },
    {
        "name": "4K Monitor",
        "description": "27-inch 4K UHD monitor with HDR support",
        "price": 449.99,
        "stock": 30,
        "category": "Electronics"
    },
    {
        "name": "USB-C Hub",
        "description": "Multi-port USB-C hub with HDMI and Ethernet",
        "price": 79.99,
        "stock": 75,
        "category": "Electronics"
    },
    {
        "name": "Webcam HD",
        "description": "1080p HD webcam with auto-focus",
        "price": 89.99,
        "stock": 40,
        "category": "Electronics"
    },
    {
        "name": "Desk Lamp",
        "description": "LED desk lamp with adjustable brightness",
        "price": 34.99,
        "stock": 60,
        "category": "Office"
    },
    {
        "name": "Office Chair",
        "description": "Ergonomic office chair with lumbar support",
        "price": 299.99,
        "stock": 20,
        "category": "Office"
    },
    {
        "name": "Standing Desk",
        "description": "Electric height-adjustable standing desk",
        "price": 599.99,
        "stock": 10,
        "category": "Office"
    },
    {
        "name": "Notebook Set",
        "description": "Set of 5 premium notebooks",
        "price": 24.99,
        "stock": 200,
        "category": "Office"
    },
    {
        "name": "Wireless Headphones",
        "description": "Noise-canceling over-ear headphones",
        "price": 199.99,
        "stock": 45,
        "category": "Electronics"
    },
    {
        "name": "Smartphone",
        "description": "Latest flagship smartphone with 5G",
        "price": 999.99,
        "stock": 25,
        "category": "Electronics"
    },
    {
        "name": "Tablet",
        "description": "10-inch tablet with stylus support",
        "price": 449.99,
        "stock": 35,
        "category": "Electronics"
    },
    {
        "name": "Smartwatch",
        "description": "Fitness tracking smartwatch with GPS",
        "price": 249.99,
        "stock": 50,
        "category": "Electronics"
    },
    {
        "name": "External SSD 1TB",
        "description": "Portable SSD with USB 3.2 Gen 2",
        "price": 129.99,
        "stock": 80,
        "category": "Electronics"
    },
    {
        "name": "Power Bank",
        "description": "20000mAh power bank with fast charging",
        "price": 39.99,
        "stock": 150,
        "category": "Electronics"
    },
    {
        "name": "Cable Organizer",
        "description": "Desktop cable management system",
        "price": 19.99,
        "stock": 100,
        "category": "Office"
    },
    {
        "name": "Monitor Stand",
        "description": "Adjustable monitor stand with storage",
        "price": 49.99,
        "stock": 70,
        "category": "Office"
    },
    {
        "name": "Desk Mat",
        "description": "Large gaming desk mat with RGB lighting",
        "price": 34.99,
        "stock": 90,
        "category": "Office"
    },
    {
        "name": "Laptop Stand",
        "description": "Aluminum laptop stand with cooling",
        "price": 44.99,
        "stock": 65,
        "category": "Office"
    }
]


async def seed_database():
    """Seed database with sample products."""
    print("=" * 50)
    print("Seeding Database with Sample Data")
    print("=" * 50)
    
    # Create engine
    engine = create_async_engine(
        settings.database_url,
        echo=False
    )
    
    # Create tables
    print("\n1. Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("   ✓ Tables created")
    
    # Create session
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Add products
    print(f"\n2. Adding {len(SAMPLE_PRODUCTS)} sample products...")
    async with async_session() as session:
        for product_data in SAMPLE_PRODUCTS:
            product = Product(**product_data)
            session.add(product)
        
        await session.commit()
        print(f"   ✓ Added {len(SAMPLE_PRODUCTS)} products")
    
    # Close engine
    await engine.dispose()
    
    print("\n" + "=" * 50)
    print("Database seeding complete!")
    print("=" * 50)
    print("\nYou can now start the application:")
    print("  uvicorn app.main:app --reload")
    print("\nOr test with:")
    print("  curl http://localhost:8000/products")


async def clear_database():
    """Clear all data from database."""
    print("=" * 50)
    print("Clearing Database")
    print("=" * 50)
    
    # Create engine
    engine = create_async_engine(
        settings.database_url,
        echo=False
    )
    
    # Drop and recreate tables
    print("\n1. Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("   ✓ Tables dropped")
    
    print("\n2. Recreating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("   ✓ Tables recreated")
    
    # Close engine
    await engine.dispose()
    
    print("\n" + "=" * 50)
    print("Database cleared!")
    print("=" * 50)


async def show_stats():
    """Show database statistics."""
    from sqlalchemy import select, func
    
    print("=" * 50)
    print("Database Statistics")
    print("=" * 50)
    
    # Create engine
    engine = create_async_engine(
        settings.database_url,
        echo=False
    )
    
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        # Count products
        result = await session.execute(select(func.count(Product.id)))
        total_products = result.scalar()
        
        # Count by category
        result = await session.execute(
            select(Product.category, func.count(Product.id))
            .group_by(Product.category)
        )
        categories = result.all()
        
        # Calculate total inventory value
        result = await session.execute(
            select(func.sum(Product.price * Product.stock))
        )
        total_value = result.scalar() or 0
        
        print(f"\nTotal Products: {total_products}")
        print(f"Total Inventory Value: ${total_value:,.2f}")
        print("\nProducts by Category:")
        for category, count in categories:
            print(f"  - {category}: {count}")
    
    # Close engine
    await engine.dispose()
    
    print("\n" + "=" * 50)


def main():
    """Main function."""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "seed":
            asyncio.run(seed_database())
        elif command == "clear":
            asyncio.run(clear_database())
        elif command == "stats":
            asyncio.run(show_stats())
        else:
            print(f"Unknown command: {command}")
            print("\nAvailable commands:")
            print("  python seed_data.py seed   - Seed database with sample data")
            print("  python seed_data.py clear  - Clear all data from database")
            print("  python seed_data.py stats  - Show database statistics")
    else:
        print("FastAPI Redis Lab - Database Seeder")
        print("\nUsage:")
        print("  python seed_data.py seed   - Seed database with sample data")
        print("  python seed_data.py clear  - Clear all data from database")
        print("  python seed_data.py stats  - Show database statistics")


if __name__ == "__main__":
    main()

"""Human-readable metadata for the synthetic e-commerce product catalogue."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Product:
    """Display metadata for one product used by the recommendation model."""

    item_id: str
    name: str
    category: str


_PRODUCT_NAMES_BY_CATEGORY: dict[str, tuple[str, ...]] = {
    "Electronics": (
        "Wireless Noise-Cancelling Headphones",
        "Smart Fitness Watch",
        "Portable Bluetooth Speaker",
        "65W USB-C Fast Charger",
        "Mechanical Gaming Keyboard",
        "Ergonomic Wireless Mouse",
        "Full HD Webcam",
        "Adjustable Aluminium Laptop Stand",
        "20,000 mAh Power Bank",
        "Smart LED Desk Lamp",
        "True Wireless Earbuds",
        "Dual-Band Wi-Fi 6 Router",
    ),
    "Home & Kitchen": (
        "Insulated Stainless Steel Water Bottle",
        "Digital Air Fryer 4.5L",
        "Ceramic Coffee Mug Set",
        "Temperature-Control Electric Kettle",
        "Pre-Seasoned Cast Iron Skillet",
        "Premium Cotton Bedsheet Set",
        "Memory Foam Support Pillow",
        "Bamboo Chopping Board",
        "Glass Food Storage Container Set",
        "Cordless Handheld Vacuum Cleaner",
        "Digital Kitchen Weighing Scale",
        "Ultrasonic Aroma Diffuser",
    ),
    "Fashion": (
        "Classic Cotton Crew-Neck T-Shirt",
        "Slim Fit Stretch Denim Jeans",
        "Lightweight Running Shoes",
        "Canvas Everyday Backpack",
        "Polarized Aviator Sunglasses",
        "Genuine Leather Bifold Wallet",
        "Linen Blend Casual Shirt",
        "Water-Resistant Windbreaker",
        "Everyday Ankle Socks — Pack of 6",
        "Quilted Crossbody Handbag",
        "Minimalist Analog Wristwatch",
        "Cushioned Comfort Slide Sandals",
    ),
    "Personal Care": (
        "Brightening Vitamin C Face Serum",
        "Aloe Vera Hydrating Gel",
        "Broad-Spectrum SPF 50 Sunscreen",
        "Hydrating Daily Shampoo",
        "Nourishing Hair Conditioner",
        "Velvet Matte Lipstick",
        "Gentle Foaming Face Wash",
        "Floral Eau de Parfum — 50 ml",
        "Complete Beard Grooming Kit",
        "Cordless Precision Hair Trimmer",
        "Shea Butter Body Lotion",
        "Professional Makeup Brush Set",
    ),
    "Fitness & Lifestyle": (
        "Non-Slip Exercise Yoga Mat",
        "Adjustable Dumbbell Set",
        "Leakproof Stainless Steel Lunch Box",
        "Double-Wall Insulated Travel Tumbler",
        "Resistance Training Band Set",
        "Quick-Dry Microfibre Sports Towel",
        "Compact Travel Organiser",
        "Hardcover Weekly Productivity Planner",
        "Recycled Paper Ruled Notebook",
        "Smooth-Flow Gel Pen Set",
        "Minimal Ceramic Indoor Planter Set",
        "Hand-Poured Scented Soy Candle",
    ),
}


def _build_catalog() -> tuple[Product, ...]:
    products: list[Product] = []
    for category, names in _PRODUCT_NAMES_BY_CATEGORY.items():
        for name in names:
            item_id = f"P{len(products) + 1:03d}"
            products.append(Product(item_id=item_id, name=name, category=category))
    return tuple(products)


PRODUCTS = _build_catalog()
PRODUCT_BY_ID = {product.item_id: product for product in PRODUCTS}


def get_product(item_id: str) -> Product:
    """Return known metadata or a readable fallback for an external product ID."""
    return PRODUCT_BY_ID.get(
        item_id,
        Product(item_id=item_id, name=f"Product {item_id}", category="Other"),
    )

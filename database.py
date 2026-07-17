# ============================================================
# database.py – ShopSmart AI
# SQLite database schema, models, and seed data
# ============================================================

import sqlite3
import json
import random
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.join("instance", "shopsmart.db")


# ─────────────────────────────────────────────
# Schema Creation
# ─────────────────────────────────────────────

def get_connection():
    """Return a SQLite connection with row_factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't already exist."""
    os.makedirs("instance", exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
    -- Users table
    CREATE TABLE IF NOT EXISTS users (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        username    TEXT    UNIQUE NOT NULL,
        email       TEXT    UNIQUE NOT NULL,
        budget      REAL    DEFAULT 50000.0,
        preferences TEXT,          -- JSON blob
        created_at  TEXT    DEFAULT (datetime('now'))
    );

    -- Categories
    CREATE TABLE IF NOT EXISTS categories (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        icon TEXT
    );

    -- Brands
    CREATE TABLE IF NOT EXISTS brands (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        name    TEXT UNIQUE NOT NULL,
        country TEXT,
        tier    TEXT   -- Budget / Mid-range / Premium
    );

    -- Products
    CREATE TABLE IF NOT EXISTS products (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT    NOT NULL,
        brand_id        INTEGER REFERENCES brands(id),
        category_id     INTEGER REFERENCES categories(id),
        price           REAL    NOT NULL,
        original_price  REAL,
        rating          REAL    DEFAULT 4.0,
        review_count    INTEGER DEFAULT 0,
        platform        TEXT,
        availability    TEXT    DEFAULT 'In Stock',
        image_url       TEXT,
        specs           TEXT,  -- JSON blob
        description     TEXT,
        eco_score       INTEGER DEFAULT 5,
        is_trending     INTEGER DEFAULT 0,
        created_at      TEXT    DEFAULT (datetime('now'))
    );

    -- Price History
    CREATE TABLE IF NOT EXISTS price_history (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER REFERENCES products(id),
        price      REAL    NOT NULL,
        recorded_at TEXT   DEFAULT (datetime('now'))
    );

    -- Reviews
    CREATE TABLE IF NOT EXISTS reviews (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id      INTEGER REFERENCES products(id),
        user_id         INTEGER REFERENCES users(id),
        rating          INTEGER NOT NULL,
        title           TEXT,
        body            TEXT,
        sentiment_score REAL    DEFAULT 0.0,
        fake_probability REAL   DEFAULT 0.0,
        verified        INTEGER DEFAULT 1,
        created_at      TEXT    DEFAULT (datetime('now'))
    );

    -- Wishlist
    CREATE TABLE IF NOT EXISTS wishlist (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER REFERENCES users(id),
        product_id INTEGER REFERENCES products(id),
        added_at   TEXT    DEFAULT (datetime('now')),
        UNIQUE(user_id, product_id)
    );

    -- Shopping History
    CREATE TABLE IF NOT EXISTS shopping_history (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER REFERENCES users(id),
        product_id INTEGER REFERENCES products(id),
        action     TEXT,   -- viewed / purchased / compared
        created_at TEXT    DEFAULT (datetime('now'))
    );

    -- Recommendations
    CREATE TABLE IF NOT EXISTS recommendations (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER REFERENCES users(id),
        product_id INTEGER REFERENCES products(id),
        score      REAL    DEFAULT 0.0,
        reason     TEXT,
        created_at TEXT    DEFAULT (datetime('now'))
    );

    -- Price Alerts
    CREATE TABLE IF NOT EXISTS price_alerts (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER REFERENCES users(id),
        product_id  INTEGER REFERENCES products(id),
        target_price REAL   NOT NULL,
        triggered   INTEGER DEFAULT 0,
        created_at  TEXT    DEFAULT (datetime('now'))
    );
    """)

    conn.commit()
    conn.close()
    logger.info("Database initialised at %s", DB_PATH)


# ─────────────────────────────────────────────
# Seed Data
# ─────────────────────────────────────────────

CATEGORIES = [
    ("Laptops", "💻"), ("Smartphones", "📱"), ("Headphones", "🎧"),
    ("Smartwatches", "⌚"), ("Cameras", "📷"), ("Tablets", "📟"),
    ("TVs", "📺"), ("Gaming", "🎮"), ("Speakers", "🔊"), ("Accessories", "🔌"),
]

BRANDS = [
    ("Apple", "USA", "Premium"), ("Samsung", "South Korea", "Premium"),
    ("Sony", "Japan", "Premium"), ("OnePlus", "China", "Mid-range"),
    ("Xiaomi", "China", "Budget"), ("Dell", "USA", "Mid-range"),
    ("HP", "USA", "Mid-range"), ("Lenovo", "China", "Mid-range"),
    ("Asus", "Taiwan", "Mid-range"), ("Boat", "India", "Budget"),
    ("JBL", "USA", "Mid-range"), ("Noise", "India", "Budget"),
    ("Nothing", "UK", "Mid-range"), ("Realme", "China", "Budget"),
    ("Oppo", "China", "Mid-range"),
]

PRODUCTS_SEED = [
    # Laptops
    {
        "name": "Apple MacBook Air M2",
        "brand": "Apple", "category": "Laptops",
        "price": 114900, "original_price": 119900,
        "rating": 4.8, "review_count": 2341,
        "platform": "Amazon",
        "specs": {"processor": "Apple M2", "RAM": "8GB", "storage": "256GB SSD",
                  "display": "13.6-inch Liquid Retina", "battery": "18 hrs", "weight": "1.24 kg"},
        "description": "Ultra-thin laptop powered by Apple M2 chip with exceptional battery life.",
        "eco_score": 8, "is_trending": 1,
    },
    {
        "name": "Dell XPS 15",
        "brand": "Dell", "category": "Laptops",
        "price": 109999, "original_price": 124999,
        "rating": 4.6, "review_count": 1087,
        "platform": "Flipkart",
        "specs": {"processor": "Intel Core i7-13700H", "RAM": "16GB DDR5",
                  "storage": "512GB NVMe SSD", "display": "15.6-inch OLED 3.5K",
                  "battery": "13 hrs", "weight": "1.86 kg"},
        "description": "Premium Windows laptop with stunning OLED display.",
        "eco_score": 6, "is_trending": 1,
    },
    {
        "name": "Lenovo ThinkPad X1 Carbon",
        "brand": "Lenovo", "category": "Laptops",
        "price": 139999, "original_price": 149999,
        "rating": 4.7, "review_count": 892,
        "platform": "Amazon",
        "specs": {"processor": "Intel Core i7-1365U", "RAM": "16GB LPDDR5",
                  "storage": "512GB SSD", "display": "14-inch IPS 2.8K",
                  "battery": "15 hrs", "weight": "1.12 kg"},
        "description": "Business ultrabook with legendary durability and keyboard.",
        "eco_score": 7, "is_trending": 0,
    },
    {
        "name": "HP Pavilion Gaming 15",
        "brand": "HP", "category": "Laptops",
        "price": 64999, "original_price": 79999,
        "rating": 4.3, "review_count": 3421,
        "platform": "Flipkart",
        "specs": {"processor": "AMD Ryzen 5 7535H", "RAM": "16GB DDR5",
                  "storage": "512GB SSD", "display": "15.6-inch IPS FHD 144Hz",
                  "GPU": "Nvidia RTX 3050", "battery": "7 hrs", "weight": "2.25 kg"},
        "description": "Value-for-money gaming laptop for casual to mid-level gaming.",
        "eco_score": 5, "is_trending": 1,
    },
    # Smartphones
    {
        "name": "Apple iPhone 15 Pro",
        "brand": "Apple", "category": "Smartphones",
        "price": 134900, "original_price": 134900,
        "rating": 4.9, "review_count": 8742,
        "platform": "Amazon",
        "specs": {"processor": "A17 Pro", "RAM": "8GB", "storage": "256GB",
                  "camera": "48MP Triple", "battery": "3274 mAh", "display": "6.1-inch Super Retina XDR"},
        "description": "Premium flagship with titanium design and USB-C.",
        "eco_score": 7, "is_trending": 1,
    },
    {
        "name": "Samsung Galaxy S24 Ultra",
        "brand": "Samsung", "category": "Smartphones",
        "price": 129999, "original_price": 134999,
        "rating": 4.8, "review_count": 6231,
        "platform": "Flipkart",
        "specs": {"processor": "Snapdragon 8 Gen 3", "RAM": "12GB", "storage": "256GB",
                  "camera": "200MP Quad", "battery": "5000 mAh", "display": "6.8-inch Dynamic AMOLED"},
        "description": "Ultimate Android flagship with S-Pen and 200MP camera.",
        "eco_score": 6, "is_trending": 1,
    },
    {
        "name": "OnePlus 12",
        "brand": "OnePlus", "category": "Smartphones",
        "price": 64999, "original_price": 69999,
        "rating": 4.6, "review_count": 4123,
        "platform": "Amazon",
        "specs": {"processor": "Snapdragon 8 Gen 3", "RAM": "12GB", "storage": "256GB",
                  "camera": "50MP Triple Hasselblad", "battery": "5400 mAh", "display": "6.82-inch LTPO AMOLED"},
        "description": "Flagship killer with Hasselblad cameras and blazing fast charging.",
        "eco_score": 6, "is_trending": 1,
    },
    {
        "name": "Xiaomi Redmi Note 13 Pro+",
        "brand": "Xiaomi", "category": "Smartphones",
        "price": 29999, "original_price": 34999,
        "rating": 4.4, "review_count": 9871,
        "platform": "Flipkart",
        "specs": {"processor": "MediaTek Dimensity 7200 Ultra", "RAM": "12GB", "storage": "256GB",
                  "camera": "200MP Triple", "battery": "5000 mAh", "display": "6.67-inch AMOLED"},
        "description": "Best budget phone with 200MP camera.",
        "eco_score": 5, "is_trending": 1,
    },
    # Headphones
    {
        "name": "Sony WH-1000XM5",
        "brand": "Sony", "category": "Headphones",
        "price": 26990, "original_price": 34990,
        "rating": 4.8, "review_count": 12450,
        "platform": "Amazon",
        "specs": {"type": "Over-ear", "ANC": "Yes", "battery": "30 hrs",
                  "driver": "30mm", "codec": "LDAC, AAC, SBC"},
        "description": "Industry-leading noise cancellation with 30-hour battery.",
        "eco_score": 7, "is_trending": 1,
    },
    {
        "name": "Apple AirPods Pro 2",
        "brand": "Apple", "category": "Headphones",
        "price": 24900, "original_price": 26900,
        "rating": 4.7, "review_count": 8932,
        "platform": "Amazon",
        "specs": {"type": "In-ear TWS", "ANC": "Yes", "battery": "6 hrs (30 with case)",
                  "chip": "H2", "codec": "AAC"},
        "description": "Best ANC earbuds in the Apple ecosystem.",
        "eco_score": 6, "is_trending": 1,
    },
    {
        "name": "Boat Rockerz 550",
        "brand": "Boat", "category": "Headphones",
        "price": 1499, "original_price": 2990,
        "rating": 4.0, "review_count": 54321,
        "platform": "Amazon",
        "specs": {"type": "Over-ear", "ANC": "No", "battery": "20 hrs",
                  "driver": "40mm", "codec": "SBC"},
        "description": "Affordable wireless headphones with powerful bass.",
        "eco_score": 4, "is_trending": 0,
    },
    # Smartwatches
    {
        "name": "Apple Watch Series 9",
        "brand": "Apple", "category": "Smartwatches",
        "price": 41900, "original_price": 44900,
        "rating": 4.8, "review_count": 6742,
        "platform": "Amazon",
        "specs": {"display": "LTPO OLED", "health": "ECG, SpO2, Temperature",
                  "battery": "18 hrs", "chip": "S9", "water_resistance": "WR50"},
        "description": "Most advanced Apple Watch with double tap gesture.",
        "eco_score": 7, "is_trending": 1,
    },
    {
        "name": "Samsung Galaxy Watch 6",
        "brand": "Samsung", "category": "Smartwatches",
        "price": 24999, "original_price": 29999,
        "rating": 4.5, "review_count": 3421,
        "platform": "Flipkart",
        "specs": {"display": "Super AMOLED", "health": "BioActive Sensor",
                  "battery": "40 hrs", "chip": "Exynos W930", "water_resistance": "5ATM"},
        "description": "Feature-packed Android smartwatch with advanced health tracking.",
        "eco_score": 6, "is_trending": 0,
    },
    {
        "name": "Noise ColorFit Ultra 3",
        "brand": "Noise", "category": "Smartwatches",
        "price": 3999, "original_price": 7999,
        "rating": 4.1, "review_count": 28741,
        "platform": "Flipkart",
        "specs": {"display": "AMOLED", "health": "SpO2, Heart Rate",
                  "battery": "7 days", "water_resistance": "IP68"},
        "description": "Budget smartwatch with AMOLED display and 7-day battery.",
        "eco_score": 4, "is_trending": 1,
    },
]

REVIEWS_SEED = [
    "Absolutely love this product! Best purchase I've made this year.",
    "Great value for money. Highly recommend it.",
    "Build quality is excellent. Fast delivery too.",
    "Battery life is amazing. Very satisfied.",
    "Works as described. Good product overall.",
    "A bit overpriced but the quality justifies it.",
    "Decent product for the price range.",
    "Not as good as expected. Average performance.",
    "Had some issues initially but customer support resolved them.",
    "The packaging was damaged but the product works fine.",
    "Excellent camera quality. Photos are stunning.",
    "The display is gorgeous, colours are very vibrant.",
    "Very fast charging, 0 to 100 in under an hour.",
    "Lightweight and comfortable to carry.",
    "Software updates are regular and improve features.",
]


def seed_db():
    """Populate the database with realistic sample data."""
    conn = get_connection()
    cur = conn.cursor()

    # Check if already seeded
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] > 0:
        conn.close()
        logger.info("Database already seeded, skipping.")
        return

    # Seed categories
    for name, icon in CATEGORIES:
        cur.execute("INSERT OR IGNORE INTO categories(name,icon) VALUES(?,?)", (name, icon))

    # Seed brands
    for name, country, tier in BRANDS:
        cur.execute("INSERT OR IGNORE INTO brands(name,country,tier) VALUES(?,?,?)",
                    (name, country, tier))

    # Seed default user
    cur.execute("""INSERT OR IGNORE INTO users(username,email,budget,preferences)
                   VALUES(?,?,?,?)""",
                ("demo_user", "demo@shopsmart.ai", 75000,
                 json.dumps({"themes": ["electronics"], "brands": ["Apple", "Sony"]})))

    # Seed products
    for p in PRODUCTS_SEED:
        cur.execute("SELECT id FROM brands WHERE name=?", (p["brand"],))
        brand_row = cur.fetchone()
        cur.execute("SELECT id FROM categories WHERE name=?", (p["category"],))
        cat_row = cur.fetchone()
        if not brand_row or not cat_row:
            continue
        cur.execute("""
            INSERT INTO products(name,brand_id,category_id,price,original_price,rating,review_count,
                                 platform,specs,description,eco_score,is_trending)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """, (p["name"], brand_row["id"], cat_row["id"], p["price"], p["original_price"],
              p["rating"], p["review_count"], p["platform"],
              json.dumps(p.get("specs", {})), p["description"],
              p["eco_score"], p["is_trending"]))
        product_id = cur.lastrowid

        # Price history – simulate 30 days
        base_price = p["price"]
        for days_ago in range(30, 0, -1):
            fluctuation = random.uniform(-0.08, 0.12)
            hist_price = round(base_price * (1 + fluctuation), 2)
            date_str = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            cur.execute("INSERT INTO price_history(product_id,price,recorded_at) VALUES(?,?,?)",
                        (product_id, hist_price, date_str))

        # Reviews
        for _ in range(min(5, len(REVIEWS_SEED))):
            review_text = random.choice(REVIEWS_SEED)
            rating = random.randint(3, 5)
            sentiment = round(random.uniform(0.5, 1.0) if rating >= 4 else random.uniform(-0.3, 0.5), 3)
            fake_prob = round(random.uniform(0.01, 0.25), 3)
            cur.execute("""INSERT INTO reviews(product_id,user_id,rating,title,body,sentiment_score,fake_probability,verified)
                           VALUES(?,1,?,?,?,?,?,1)""",
                        (product_id, rating, review_text[:60], review_text, sentiment, fake_prob))

        # Wishlist for demo user (random subset)
        if random.random() > 0.6:
            cur.execute("INSERT OR IGNORE INTO wishlist(user_id,product_id) VALUES(1,?)", (product_id,))

    conn.commit()
    conn.close()
    logger.info("Database seeded with %d products.", len(PRODUCTS_SEED))


# ─────────────────────────────────────────────
# Query Helpers
# ─────────────────────────────────────────────

def get_all_products(limit=50):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.*, b.name AS brand_name, b.tier AS brand_tier,
               c.name AS category_name, c.icon AS category_icon
        FROM products p
        LEFT JOIN brands b ON p.brand_id = b.id
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.is_trending DESC, p.rating DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_product_by_id(product_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.*, b.name AS brand_name, b.tier AS brand_tier,
               c.name AS category_name
        FROM products p
        LEFT JOIN brands b ON p.brand_id = b.id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.id = ?
    """, (product_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def search_products(query, category=None, max_price=None, min_rating=None):
    conn = get_connection()
    cur = conn.cursor()
    sql = """
        SELECT p.*, b.name AS brand_name, c.name AS category_name
        FROM products p
        LEFT JOIN brands b ON p.brand_id = b.id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE (p.name LIKE ? OR b.name LIKE ? OR p.description LIKE ?)
    """
    params = [f"%{query}%", f"%{query}%", f"%{query}%"]
    if category:
        sql += " AND c.name = ?"
        params.append(category)
    if max_price:
        sql += " AND p.price <= ?"
        params.append(max_price)
    if min_rating:
        sql += " AND p.rating >= ?"
        params.append(min_rating)
    sql += " ORDER BY p.rating DESC LIMIT 20"
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_price_history(product_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT price, recorded_at FROM price_history WHERE product_id=? ORDER BY recorded_at",
                (product_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_reviews(product_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reviews WHERE product_id=? ORDER BY created_at DESC", (product_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_wishlist(user_id=1):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.*, b.name AS brand_name, c.name AS category_name
        FROM wishlist w
        JOIN products p ON w.product_id = p.id
        LEFT JOIN brands b ON p.brand_id = b.id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE w.user_id = ?
    """, (user_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def toggle_wishlist(user_id, product_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM wishlist WHERE user_id=? AND product_id=?", (user_id, product_id))
    row = cur.fetchone()
    if row:
        cur.execute("DELETE FROM wishlist WHERE user_id=? AND product_id=?", (user_id, product_id))
        action = "removed"
    else:
        cur.execute("INSERT INTO wishlist(user_id,product_id) VALUES(?,?)", (user_id, product_id))
        action = "added"
    conn.commit()
    conn.close()
    return action


def get_categories():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM categories")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def add_price_alert(user_id: int, product_id: int, target_price: float):
    """Set a price alert for a product."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""INSERT OR REPLACE INTO price_alerts(user_id, product_id, target_price, triggered)
                   VALUES(?,?,?,0)""", (user_id, product_id, target_price))
    conn.commit()
    conn.close()


def get_price_alerts(user_id: int):
    """Get all active price alerts for a user."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT pa.*, p.name AS product_name, p.price AS current_price, b.name AS brand_name
        FROM price_alerts pa
        JOIN products p ON pa.product_id = p.id
        LEFT JOIN brands b ON p.brand_id = b.id
        WHERE pa.user_id = ? AND pa.triggered = 0
        ORDER BY pa.created_at DESC
    """, (user_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def delete_price_alert(user_id: int, product_id: int):
    """Remove a price alert."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM price_alerts WHERE user_id=? AND product_id=?", (user_id, product_id))
    conn.commit()
    conn.close()


def check_triggered_alerts(user_id: int = 1):
    """Check which alerts have been triggered (current price <= target)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE price_alerts SET triggered = 1
        WHERE user_id = ? AND triggered = 0
          AND product_id IN (
              SELECT pa.product_id FROM price_alerts pa
              JOIN products p ON pa.product_id = p.id
              WHERE pa.user_id = ? AND pa.triggered = 0 AND p.price <= pa.target_price
          )
    """, (user_id, user_id))
    triggered = cur.rowcount
    conn.commit()
    conn.close()
    return triggered


def log_product_view(user_id: int, product_id: int):
    """Log that a user viewed a product."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO shopping_history(user_id, product_id, action) VALUES(?,?,?)",
                (user_id, product_id, "viewed"))
    conn.commit()
    conn.close()


def get_dashboard_stats():
    conn = get_connection()
    cur = conn.cursor()
    stats = {}
    cur.execute("SELECT COUNT(*) FROM products")
    stats["total_products"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM reviews")
    stats["total_reviews"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM wishlist")
    stats["total_wishlist"] = cur.fetchone()[0]
    cur.execute("SELECT AVG(rating) FROM products")
    stats["avg_rating"] = round(cur.fetchone()[0] or 0, 2)
    cur.execute("""SELECT c.name, COUNT(p.id) as cnt
                   FROM categories c LEFT JOIN products p ON p.category_id=c.id
                   GROUP BY c.name ORDER BY cnt DESC""")
    stats["category_dist"] = [dict(r) for r in cur.fetchall()]
    cur.execute("""SELECT b.name, AVG(p.rating) as avg_rating, COUNT(p.id) as cnt
                   FROM brands b LEFT JOIN products p ON p.brand_id=b.id
                   GROUP BY b.name ORDER BY cnt DESC LIMIT 8""")
    stats["brand_popularity"] = [dict(r) for r in cur.fetchall()]
    cur.execute("""SELECT name, price, rating, is_trending
                   FROM products WHERE is_trending=1 ORDER BY rating DESC LIMIT 6""")
    stats["trending"] = [dict(r) for r in cur.fetchall()]
    conn.close()
    return stats

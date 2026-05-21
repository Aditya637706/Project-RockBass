from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sqlite3
import os
import json 

app = FastAPI(title="RockBass Car Audio Multi-Angle Affiliate API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "images")
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

app.mount("/static", StaticFiles(directory=IMAGE_DIR), name="static")

DB_FILE = "rockbass.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row 
    return conn

# 🚀 NEW: Serve the frontend index.html automatically at the home address "/"
@app.get("/")
def serve_frontend():
    html_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"error": "index.html not found in repository root. Please ensure index3.html was renamed to index.html"}

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT NOT NULL,
            imageAnglesJson TEXT NOT NULL, 
            powerOutput TEXT NOT NULL,
            frequencyResponse TEXT NOT NULL,
            impedance TEXT NOT NULL,
            amazonUrl TEXT DEFAULT '',
            flipkartUrl TEXT DEFAULT '',
            clickCount INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- API ENDPOINTS ---

@app.get("/api/seed")
def seed_database(request: Request):
    """Populates database rows linking dynamically to 4 unique angles based on deployment host."""
    # 🚀 NEW: Automatically calculates your live Render address instead of hardcoding 127.0.0.1
    base_url = str(request.base_url).rstrip('/')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products")
    
    velox_angles = json.dumps([
        f'{base_url}/static/velox_1.jpg',
        f'{base_url}/static/velox_2.jpg',
        f'{base_url}/static/velox_3.jpg',
        f'{base_url}/static/velox_4.jpg'
    ])
    
    core6_angles = json.dumps([
        f'{base_url}/static/core6_1.jpg',
        f'{base_url}/static/core6_2.jpg',
        f'{base_url}/static/core6_3.jpg',
        f'{base_url}/static/core6_4.jpg'
    ])
    
    aero_angles = json.dumps([
        f'{base_url}/static/aero_1.jpg',
        f'{base_url}/static/aero_2.jpg',
        f'{base_url}/static/aero_3.jpg',
        f'{base_url}/static/aero_4.jpg'
    ])
    
    seed_data = [
        (
            'VeloX 12" Subwoofer', 'velox-12-subwoofer', 'Subwoofer', 549.00,
            'Neodymium motor structure throwing pure, clean sub-bass frequencies down to the biological limits of hearing.',
            velox_angles, '1200W RMS / 2400W Peak', '18Hz - 250Hz', 'Dual 4-Ohm',
            'https://amazon.com', 'https://flipkart.com'
        ),
        (
            'Core-6 Components', 'core-6-components', 'Components', 389.00,
            'Carbon-fiber woven matrix mid-bass driver cones delivering lightning-fast transient audio response with zero cone breakup.',
            core6_angles, '150W RMS / 300W Peak', '55Hz - 22kHz', '4-Ohm',
            'https://amazon.com', 'https://flipkart.com'
        ),
        (
            'AeroTweeters', 'aerotweeters', 'Tweeters', 199.00,
            'Pure aerospace silk dome transducers optimized specifically for acoustic reflections inside modern vehicle glass cabins.',
            aero_angles, '80W RMS / 160W Peak', '3.5kHz - 30kHz', '6-Ohm',
            'https://amazon.com', 'https://flipkart.com'
        )
    ]
    
    cursor.executemany("""
        INSERT INTO products (
            name, slug, category, price, description, imageAnglesJson, 
            powerOutput, frequencyResponse, impedance, amazonUrl, flipkartUrl
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, seed_data)
    
    conn.commit()
    conn.close()
    return {"message": "Database configured with dynamic production web assets successfully!"}


@app.get("/api/products")
def get_all_products():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM products ORDER BY price DESC").fetchall()
    conn.close()
    
    result = []
    for row in rows:
        angles_list = json.loads(row["imageAnglesJson"])
        result.append({
            "_id": str(row["id"]),
            "name": row["name"],
            "slug": row["slug"],
            "category": row["category"],
            "price": row["price"],
            "description": row["description"],
            "imageUrl": angles_list[0], 
            "angles": angles_list,       
            "specs": {
                "powerOutput": row["powerOutput"],
                "frequencyResponse": row["frequencyResponse"],
                "impedance": row["impedance"]
            },
            "links": {
                "amazon": row["amazonUrl"],
                "flipkart": row["flipkartUrl"]
            },
            "clickCount": row["clickCount"]
        })
    return result

@app.post("/api/products/{product_id}/track-click")
def track_affiliate_click(product_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM products WHERE id = ?", (product_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Product not found")
        
    cursor.execute("UPDATE products SET clickCount = clickCount + 1 WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return {"success": True}

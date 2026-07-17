# ============================================================
# app.py – ShopSmart AI
# Flask application – routes, API endpoints, and page rendering
# ============================================================

import os
import json
import logging
import traceback
from datetime import datetime
from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, flash, session
)
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()

# ─────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("shopsmart")

# ─────────────────────────────────────────────
# Flask App Configuration
# ─────────────────────────────────────────────
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("SECRET_KEY", "shopsmart-secret-key-2024")
CORS(app)

UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ─────────────────────────────────────────────
# Initialise DB, RAG, and Agent Orchestrator
# ─────────────────────────────────────────────
from database import init_db, seed_db, get_all_products, get_product_by_id
from database import search_products, get_categories, get_wishlist, toggle_wishlist
from database import get_dashboard_stats, get_price_history, get_reviews
from database import add_price_alert, get_price_alerts, delete_price_alert, log_product_view
from rag import init_rag
from orchestrator import orchestrate, shopping_assistant_agent
from shopping_model import is_watsonx_configured, get_token_stats

with app.app_context():
    init_db()
    seed_db()
    try:
        init_rag()
    except Exception as e:
        logger.warning("RAG init warning: %s", e)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ─────────────────────────────────────────────
# Context Processor – inject globals into all templates
# ─────────────────────────────────────────────
@app.context_processor
def inject_globals():
    return {
        "app_name": "ShopSmart AI",
        "current_year": datetime.now().year,
        "watsonx_active": is_watsonx_configured(),
        "dark_mode": session.get("dark_mode", False),
    }


# ─────────────────────────────────────────────
# PAGE ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def home():
    """Home page – trending products and hero section."""
    products = get_all_products(limit=12)
    categories = get_categories()
    return render_template("home.html", products=products, categories=categories)


@app.route("/assistant")
def assistant():
    """Shopping Assistant chat page."""
    return render_template("assistant.html")


@app.route("/comparison")
def comparison():
    """Product Comparison page."""
    products = get_all_products(limit=50)
    categories = get_categories()
    return render_template("comparison.html", products=products, categories=categories)


@app.route("/reviews")
def reviews():
    """Review Analyser page."""
    products = get_all_products(limit=50)
    return render_template("reviews.html", products=products)


@app.route("/recommendations")
def recommendations():
    """Personalised Recommendations page."""
    categories = get_categories()
    return render_template("recommendations.html", categories=categories)


@app.route("/predictor")
def predictor():
    """Price Predictor page."""
    products = get_all_products(limit=50)
    return render_template("predictor.html", products=products)


@app.route("/wishlist")
def wishlist():
    """User Wishlist page."""
    items = get_wishlist(user_id=1)
    return render_template("wishlist.html", wishlist=items)


@app.route("/multimodal")
def multimodal():
    """Multimodal Search page (text/image/voice)."""
    return render_template("multimodal.html")


@app.route("/dashboard")
def dashboard():
    """Analytics Dashboard."""
    stats = get_dashboard_stats()
    products = get_all_products(limit=20)
    return render_template("dashboard.html", stats=stats, products=products)


@app.route("/resources")
def resources():
    """Resources & Shopping Guides."""
    return render_template("resources.html")


@app.route("/about")
def about():
    """About page."""
    return render_template("about.html")


@app.route("/products")
def products_page():
    """Browse all products, optionally filtered by category."""
    category = request.args.get("category", "").strip()
    query = request.args.get("q", "").strip()
    categories = get_categories()
    if query:
        products = search_products(query, category=category or None)
    elif category:
        products = search_products("", category=category)
    else:
        products = get_all_products(limit=50)
    return render_template("products.html",
                           products=products,
                           categories=categories,
                           selected_category=category,
                           search_query=query)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    """Product detail page."""
    product = get_product_by_id(product_id)
    if not product:
        flash("Product not found.", "warning")
        return redirect(url_for("home"))
    reviews_list = get_reviews(product_id)
    price_history = get_price_history(product_id)
    product["specs"] = json.loads(product.get("specs") or "{}")
    alerts = get_price_alerts(user_id=1)
    alert_ids = {a["product_id"] for a in alerts}
    current_alert = next((a for a in alerts if a["product_id"] == product_id), None)
    # Log product view
    try:
        log_product_view(user_id=1, product_id=product_id)
    except Exception:
        pass
    return render_template("product_detail.html",
                           product=product,
                           reviews=reviews_list,
                           price_history=json.dumps(price_history),
                           current_alert=current_alert)


# ─────────────────────────────────────────────
# DARK MODE TOGGLE
# ─────────────────────────────────────────────

@app.route("/alerts")
def alerts_page():
    """Price Alerts management page."""
    alerts = get_price_alerts(user_id=1)
    return render_template("alerts.html", alerts=alerts)


@app.route("/toggle-dark-mode", methods=["POST"])
def toggle_dark_mode():
    session["dark_mode"] = not session.get("dark_mode", False)
    return jsonify({"dark_mode": session["dark_mode"]})


# ─────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """
    Main chat API – routes to the central orchestrator.
    IBM Orchestrate: this is the entry point for automated workflows.
    """
    try:
        data = request.get_json(force=True)
        message = data.get("message", "").strip()
        context_data = data.get("context", {})
        if not message:
            return jsonify({"error": "Empty message"}), 400

        result = orchestrate(message, context_data)
        return jsonify(result)
    except Exception as e:
        logger.error("Chat API error: %s\n%s", e, traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/api/compare", methods=["POST"])
def api_compare():
    """Compare multiple products via the Comparison Agent."""
    try:
        data = request.get_json(force=True)
        product_ids = data.get("product_ids", [])
        if len(product_ids) < 2:
            return jsonify({"error": "Select at least 2 products"}), 400
        result = orchestrate("compare products", {"product_ids": product_ids})
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reviews/<int:product_id>", methods=["GET"])
def api_reviews(product_id):
    """Get AI-analysed reviews for a product."""
    try:
        result = orchestrate("analyse reviews", {"product_id": product_id})
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/predict/<int:product_id>", methods=["GET"])
def api_predict(product_id):
    """Get price prediction for a product."""
    try:
        result = orchestrate("predict price drop", {"product_id": product_id})
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    """Get personalised product recommendations."""
    try:
        data = request.get_json(force=True)
        preferences = data.get("preferences", {})
        result = orchestrate("recommend products", {"preferences": preferences})
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sustainability/<int:product_id>", methods=["GET"])
def api_sustainability(product_id):
    """Get sustainability analysis for a product."""
    try:
        result = orchestrate("eco sustainability analysis", {"product_id": product_id})
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/search", methods=["POST"])
def api_search():
    """Text-based product search."""
    try:
        data = request.get_json(force=True)
        query = data.get("query", "")
        if not query:
            return jsonify({"error": "Empty query"}), 400
        products = search_products(query)
        return jsonify({"products": products, "count": len(products)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/image-search", methods=["POST"])
def api_image_search():
    """Image-based product search (multimodal)."""
    try:
        if "image" not in request.files:
            return jsonify({"error": "No image uploaded"}), 400
        file = request.files["image"]
        if file.filename == "" or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400

        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)

        result = orchestrate("image search", {
            "mode": "image",
            "image_path": save_path,
        })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/voice-search", methods=["POST"])
def api_voice_search():
    """Voice search – accepts transcribed text from browser."""
    try:
        data = request.get_json(force=True)
        voice_text = data.get("voice_text", "")
        result = orchestrate("find product", {
            "mode": "voice",
            "audio_path": None,
            "query": voice_text,
        })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/wishlist/toggle", methods=["POST"])
def api_wishlist_toggle():
    """Add or remove a product from wishlist."""
    try:
        data = request.get_json(force=True)
        product_id = data.get("product_id")
        if not product_id:
            return jsonify({"error": "product_id required"}), 400
        action = toggle_wishlist(user_id=1, product_id=product_id)
        return jsonify({"action": action, "product_id": product_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/products", methods=["GET"])
def api_products():
    """Get all products (paginated)."""
    limit = request.args.get("limit", 20, type=int)
    products = get_all_products(limit=limit)
    return jsonify({"products": products, "count": len(products)})


@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    """Dashboard statistics API."""
    stats = get_dashboard_stats()
    return jsonify(stats)


@app.route("/api/knowledge", methods=["POST"])
def api_knowledge():
    """Shopping knowledge Q&A."""
    try:
        data = request.get_json(force=True)
        question = data.get("question", "")
        result = orchestrate(question, {})
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/price-alert", methods=["POST"])
def api_price_alert_set():
    """Set a price drop alert for a product."""
    try:
        data = request.get_json(force=True)
        product_id = data.get("product_id")
        target_price = data.get("target_price")
        if not product_id or target_price is None:
            return jsonify({"error": "product_id and target_price required"}), 400
        add_price_alert(user_id=1, product_id=int(product_id), target_price=float(target_price))
        return jsonify({"status": "alert_set", "product_id": product_id, "target_price": target_price})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/price-alert/<int:product_id>", methods=["DELETE"])
def api_price_alert_delete(product_id):
    """Remove a price alert."""
    try:
        delete_price_alert(user_id=1, product_id=product_id)
        return jsonify({"status": "alert_removed", "product_id": product_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/price-alerts", methods=["GET"])
def api_price_alerts_list():
    """List all active price alerts for the demo user."""
    try:
        alerts = get_price_alerts(user_id=1)
        return jsonify({"alerts": alerts, "count": len(alerts)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/token-stats", methods=["GET"])
def api_token_stats():
    """Return live IBM Granite token usage since app start."""
    stats = get_token_stats()
    stats["watsonx_active"] = is_watsonx_configured()
    return jsonify(stats)


@app.route("/api/chat/reset", methods=["POST"])
def api_chat_reset():
    """Reset the Shopping Assistant conversation history."""
    try:
        from orchestrator import _assistant_agent
        _assistant_agent.reset_conversation()
        return jsonify({"status": "reset"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────
# Error Handlers
# ─────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="Page not found"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, message="Internal server error"), 500


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    logger.info("Starting ShopSmart AI on port %d", port)
    app.run(host="0.0.0.0", port=port, debug=debug)

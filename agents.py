# ============================================================
# agents.py – ShopSmart AI
# Eight independent AI agents, each with a distinct purpose.
#
# IBM Langflow Integration:
#   Each agent class maps to a Langflow 'Agent' node connected
#   to the central Orchestrator node.
#
# IBM Orchestrate Integration:
#   Each agent is registered as a Skill in IBM Orchestrate,
#   enabling no-code task delegation and multi-agent workflows.
# ============================================================

import json
import logging
import random
from datetime import datetime
from database import (
    search_products, get_product_by_id, get_reviews,
    get_price_history, get_all_products
)
from shopping_model import generate_response
from rag import retrieve_context

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# AGENT 1: Shopping Knowledge Agent
# ─────────────────────────────────────────────

class ShoppingKnowledgeAgent:
    """
    Answers general shopping and technology questions.

    IBM Granite Model: granite-3-8b-instruct
    IBM Langflow Node: 'Knowledge Agent'
    IBM Orchestrate Skill: 'shopping_knowledge_skill'
    """

    NAME = "Shopping Knowledge Agent"

    def run(self, question: str) -> dict:
        logger.info("[KnowledgeAgent] Query: %s", question)

        # RAG: retrieve relevant shopping knowledge
        context = retrieve_context(question, n_results=3)

        prompt = (
            f"A customer is asking a shopping-related question.\n"
            f"Question: {question}\n\n"
            f"Provide a detailed, helpful answer. Include specific product recommendations "
            f"with prices and specs where relevant. Explain technical terms clearly. "
            f"Format with bullet points for readability."
        )

        # IBM Granite call
        answer = generate_response(prompt, context=context)

        return {
            "agent": self.NAME,
            "question": question,
            "answer": answer,
            "context_used": bool(context),
            "timestamp": datetime.now().isoformat(),
        }


# ─────────────────────────────────────────────
# AGENT 2: Product Comparison Agent
# ─────────────────────────────────────────────

class ProductComparisonAgent:
    """
    Compares multiple products across platforms and generates
    structured comparison tables with pros/cons analysis.

    IBM Granite Model: granite-3-8b-instruct
    IBM Langflow Node: 'Comparison Agent'
    IBM Orchestrate Skill: 'product_comparison_skill'
    """

    NAME = "Product Comparison Agent"

    def run(self, product_ids: list) -> dict:
        logger.info("[ComparisonAgent] Comparing products: %s", product_ids)

        products = []
        for pid in product_ids:
            p = get_product_by_id(pid)
            if p:
                products.append(p)

        if len(products) < 2:
            return {"agent": self.NAME, "error": "Need at least 2 products to compare."}

        # Build comparison context
        product_summaries = []
        for p in products:
            specs = json.loads(p.get("specs", "{}"))
            specs_str = " | ".join(f"{k}: {v}" for k, v in specs.items())
            summary = (
                f"Product: {p['name']} | Brand: {p['brand_name']} | "
                f"Price: ₹{p['price']:,.0f} | Rating: {p['rating']}/5 | "
                f"Platform: {p['platform']} | Specs: {specs_str}"
            )
            product_summaries.append(summary)

        comparison_text = "\n".join(product_summaries)
        context = retrieve_context(f"compare {products[0]['category_name']}", n_results=2)

        prompt = (
            f"Compare these {len(products)} products in detail:\n\n"
            f"{comparison_text}\n\n"
            f"Provide:\n"
            f"1. Key specification differences\n"
            f"2. Pros and cons for each product\n"
            f"3. Best Value Pick (with reason)\n"
            f"4. Best Premium Pick (with reason)\n"
            f"5. Best Budget Pick (with reason)\n"
            f"6. Final recommendation based on different use cases\n"
            f"Format your response clearly with headings."
        )

        analysis = generate_response(prompt, context=context)

        # Compute quick stats
        cheapest = min(products, key=lambda x: x["price"])
        highest_rated = max(products, key=lambda x: x["rating"])
        best_value = max(products, key=lambda x: x["rating"] / (x["price"] / 10000))

        return {
            "agent": self.NAME,
            "products": products,
            "analysis": analysis,
            "quick_stats": {
                "cheapest": cheapest["name"],
                "highest_rated": highest_rated["name"],
                "best_value": best_value["name"],
            },
            "timestamp": datetime.now().isoformat(),
        }


# ─────────────────────────────────────────────
# AGENT 3: Review Intelligence Agent
# ─────────────────────────────────────────────

class ReviewIntelligenceAgent:
    """
    Analyses customer reviews: sentiment, fake detection,
    common themes, and satisfaction scoring.

    IBM Granite Model: granite-3-8b-instruct
    IBM Langflow Node: 'Review Intelligence Agent'
    IBM Orchestrate Skill: 'review_analysis_skill'
    """

    NAME = "Review Intelligence Agent"

    def run(self, product_id: int) -> dict:
        logger.info("[ReviewAgent] Analysing reviews for product %d", product_id)

        product = get_product_by_id(product_id)
        reviews = get_reviews(product_id)

        if not reviews:
            return {
                "agent": self.NAME,
                "product": product,
                "error": "No reviews found for this product.",
            }

        # Compute aggregate stats
        avg_sentiment = sum(r["sentiment_score"] for r in reviews) / len(reviews)
        avg_fake_prob = sum(r["fake_probability"] for r in reviews) / len(reviews)
        avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
        verified_count = sum(1 for r in reviews if r["verified"])

        # Prepare review texts for Granite analysis
        review_texts = "\n".join(
            f"[{i+1}] Rating: {r['rating']}/5 – {r['body']}" for i, r in enumerate(reviews[:10])
        )

        context = retrieve_context("review analysis shopping tips fake reviews")

        prompt = (
            f"Analyse these customer reviews for '{product['name'] if product else 'product'}':\n\n"
            f"{review_texts}\n\n"
            f"Provide:\n"
            f"1. Overall summary (2-3 sentences)\n"
            f"2. Top 3 positive aspects customers love\n"
            f"3. Top 3 negative aspects / complaints\n"
            f"4. Fake review indicators (if any)\n"
            f"5. Overall customer satisfaction verdict (Excellent/Good/Average/Poor)\n"
            f"6. Recommendation: Should someone buy this based on reviews?"
        )

        analysis = generate_response(prompt, context=context)

        # Classify fake risk
        if avg_fake_prob < 0.15:
            fake_risk = "Low"
        elif avg_fake_prob < 0.35:
            fake_risk = "Medium"
        else:
            fake_risk = "High"

        return {
            "agent": self.NAME,
            "product": product,
            "review_count": len(reviews),
            "analysis": analysis,
            "metrics": {
                "avg_sentiment": round(avg_sentiment, 3),
                "avg_fake_probability": round(avg_fake_prob, 3),
                "avg_rating": round(avg_rating, 2),
                "verified_count": verified_count,
                "fake_risk": fake_risk,
                "satisfaction_score": round(min(10.0, avg_rating * 2), 1),
            },
            "reviews": reviews[:10],
            "timestamp": datetime.now().isoformat(),
        }


# ─────────────────────────────────────────────
# AGENT 4: Predictive Shopping Agent
# ─────────────────────────────────────────────

class PredictiveShoppingAgent:
    """
    Predicts best time to buy using price history and seasonal trends.
    Generates price trend charts data and buying recommendations.

    IBM Granite Model: granite-3-8b-instruct
    IBM Langflow Node: 'Prediction Agent'
    IBM Orchestrate Skill: 'price_prediction_skill'
    """

    NAME = "Predictive Shopping Agent"

    # Indian festival/sale seasons
    SALE_CALENDAR = {
        1: "Republic Day Sale",
        3: "Holi Sale / End of Financial Year",
        8: "Independence Day Sale",
        9: "Onam Sale",
        10: "Big Billion Days / Great Indian Festival (Diwali)",
        11: "Singles Day / Black Friday",
        12: "Year-End Sale / Christmas",
    }

    def run(self, product_id: int) -> dict:
        logger.info("[PredictionAgent] Predicting price for product %d", product_id)

        product = get_product_by_id(product_id)
        price_history = get_price_history(product_id)

        if not product:
            return {"agent": self.NAME, "error": "Product not found."}

        # Compute trend statistics
        if price_history:
            prices = [ph["price"] for ph in price_history]
            min_price = min(prices)
            max_price = max(prices)
            avg_price = sum(prices) / len(prices)
            recent_avg = sum(prices[-7:]) / min(7, len(prices))
            trend = "Decreasing" if recent_avg < avg_price else "Increasing"
            price_change_pct = round((recent_avg - avg_price) / avg_price * 100, 1)
        else:
            min_price = max_price = avg_price = recent_avg = product["price"]
            trend = "Stable"
            price_change_pct = 0

        current_month = datetime.now().month
        upcoming_sale = self.SALE_CALENDAR.get(current_month) or \
                        self.SALE_CALENDAR.get((current_month % 12) + 1) or \
                        "Check platform for upcoming sales"

        # Buy recommendation logic
        current_price = product["price"]
        original_price = product.get("original_price") or current_price
        discount_pct = round((original_price - current_price) / original_price * 100, 1)

        if discount_pct >= 20 or (min_price > 0 and current_price <= min_price * 1.05):
            recommendation = "BUY NOW"
            reason = "Price is near its historical low or significantly discounted."
        elif trend == "Decreasing":
            recommendation = "WAIT"
            reason = "Price trend is downward. Expect further drops in coming days."
        else:
            recommendation = "MONITOR"
            reason = f"Upcoming sale season ({upcoming_sale}) may offer better deals."

        context = retrieve_context("price drop prediction best time to buy sale season")

        prompt = (
            f"Product: {product['name']} | Current Price: ₹{current_price:,.0f}\n"
            f"Original Price: ₹{original_price:,.0f} | Discount: {discount_pct}%\n"
            f"30-day Price Range: ₹{min_price:,.0f} – ₹{max_price:,.0f}\n"
            f"Price Trend: {trend} ({price_change_pct:+.1f}%)\n"
            f"Upcoming Sale: {upcoming_sale}\n\n"
            f"Provide detailed shopping advice:\n"
            f"1. Is this a good price? Why or why not?\n"
            f"2. When is the best time to buy?\n"
            f"3. Expected price at next major sale?\n"
            f"4. Risk of waiting (stock availability, price increase)?\n"
            f"5. Final verdict: Buy Now / Wait / Monitor"
        )

        advice = generate_response(prompt, context=context)

        return {
            "agent": self.NAME,
            "product": product,
            "price_history": price_history,
            "prediction": {
                "current_price": current_price,
                "min_price_30d": min_price,
                "max_price_30d": max_price,
                "avg_price_30d": round(avg_price, 2),
                "trend": trend,
                "price_change_pct": price_change_pct,
                "discount_from_original": discount_pct,
                "recommendation": recommendation,
                "reason": reason,
                "upcoming_sale": upcoming_sale,
            },
            "advice": advice,
            "timestamp": datetime.now().isoformat(),
        }


# ─────────────────────────────────────────────
# AGENT 5: Recommendation Agent
# ─────────────────────────────────────────────

class RecommendationAgent:
    """
    Generates personalised product recommendations based on
    budget, category, brand preferences, and usage purpose.

    IBM Granite Model: granite-3-8b-instruct
    IBM Langflow Node: 'Recommendation Agent'
    IBM Orchestrate Skill: 'recommendation_skill'
    """

    NAME = "Recommendation Agent"

    def run(self, preferences: dict) -> dict:
        logger.info("[RecommendationAgent] Preferences: %s", preferences)

        budget = preferences.get("budget", 50000)
        category = preferences.get("category", "")
        brand_pref = preferences.get("brand", "")
        purpose = preferences.get("purpose", "general use")
        features = preferences.get("features", [])

        # Query DB for matching products
        query = category or purpose or "electronics"
        all_products = search_products(
            query=query,
            category=category if category else None,
            max_price=budget,
            min_rating=3.5,
        )

        if not all_products:
            all_products = get_all_products(limit=20)

        # Score products by preference match
        scored = []
        for p in all_products:
            score = p.get("rating", 3.0) * 10
            # Budget fit score
            price_ratio = p["price"] / budget if budget > 0 else 1
            if price_ratio <= 0.8:
                score += 20  # well within budget
            elif price_ratio <= 1.0:
                score += 10
            # Brand preference
            if brand_pref and brand_pref.lower() in (p.get("brand_name") or "").lower():
                score += 15
            # Trending bonus
            if p.get("is_trending"):
                score += 10
            p["recommendation_score"] = round(score, 1)
            scored.append(p)

        scored.sort(key=lambda x: x["recommendation_score"], reverse=True)
        top_10 = scored[:10]

        context = retrieve_context(f"recommend {category} {purpose} budget {budget}")

        top_names = ", ".join(p["name"] for p in top_10[:5])
        prompt = (
            f"Generate personalised product recommendations.\n"
            f"Budget: ₹{budget:,.0f} | Category: {category or 'Any'} | "
            f"Brand Preference: {brand_pref or 'None'} | Purpose: {purpose}\n"
            f"Features wanted: {', '.join(features) if features else 'Not specified'}\n"
            f"Top matching products: {top_names}\n\n"
            f"Provide:\n"
            f"1. Top 3 specific recommendations with reasons\n"
            f"2. Best budget option\n"
            f"3. Best premium option within budget\n"
            f"4. Recommended accessories/bundles\n"
            f"5. Products to avoid and why\n"
            f"6. Shopping tips specific to this purchase"
        )

        recommendations = generate_response(prompt, context=context)

        return {
            "agent": self.NAME,
            "preferences": preferences,
            "top_products": top_10,
            "ai_recommendations": recommendations,
            "timestamp": datetime.now().isoformat(),
        }


# ─────────────────────────────────────────────
# AGENT 6: Sustainability Agent
# ─────────────────────────────────────────────

class SustainabilityAgent:
    """
    Evaluates product sustainability: eco score, recyclability,
    energy efficiency, and carbon impact.

    IBM Granite Model: granite-3-8b-instruct
    IBM Langflow Node: 'Sustainability Agent'
    IBM Orchestrate Skill: 'sustainability_skill'
    """

    NAME = "Sustainability Agent"

    ECO_LABELS = {
        "Apple": {"recycled_aluminium": True, "carbon_neutral_pledge": "2030", "repairability": 6},
        "Samsung": {"recycled_materials": True, "carbon_neutral_pledge": "2050", "repairability": 5},
        "Sony": {"green_partner": True, "carbon_neutral_pledge": "2040", "repairability": 5},
        "Dell": {"epeat_gold": True, "carbon_neutral_pledge": "2050", "repairability": 7},
        "HP": {"epeat_registered": True, "carbon_neutral_pledge": "2040", "repairability": 7},
        "Lenovo": {"epeat_registered": True, "carbon_neutral_pledge": "2050", "repairability": 7},
    }

    def run(self, product_id: int) -> dict:
        logger.info("[SustainabilityAgent] Evaluating product %d", product_id)

        product = get_product_by_id(product_id)
        if not product:
            return {"agent": self.NAME, "error": "Product not found."}

        brand = product.get("brand_name", "")
        eco_score = product.get("eco_score", 5)
        brand_info = self.ECO_LABELS.get(brand, {})

        # Compute sustainability dimensions
        energy_efficiency = min(10, eco_score + random.randint(-1, 2))
        recyclability = min(10, eco_score + random.randint(-2, 1))
        packaging_score = random.randint(4, 9)
        carbon_impact = round(random.uniform(20, 80), 1)  # kg CO2e

        context = retrieve_context("eco score green product sustainability electronics")

        prompt = (
            f"Evaluate the sustainability of: {product['name']} by {brand}\n"
            f"Category: {product['category_name']} | Eco Score: {eco_score}/10\n"
            f"Brand sustainability commitments: {json.dumps(brand_info)}\n\n"
            f"Provide:\n"
            f"1. Overall eco rating (Green / Neutral / Concerning)\n"
            f"2. Energy efficiency assessment\n"
            f"3. Recyclability and repairability\n"
            f"4. Packaging sustainability\n"
            f"5. Carbon footprint estimate\n"
            f"6. 3 more sustainable alternatives to consider\n"
            f"7. Green shopping tips for this product category"
        )

        analysis = generate_response(prompt, context=context)

        return {
            "agent": self.NAME,
            "product": product,
            "sustainability": {
                "eco_score": eco_score,
                "energy_efficiency": energy_efficiency,
                "recyclability": recyclability,
                "packaging_score": packaging_score,
                "carbon_impact_kg": carbon_impact,
                "brand_commitments": brand_info,
                "eco_grade": "A" if eco_score >= 8 else "B" if eco_score >= 6 else "C" if eco_score >= 4 else "D",
            },
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
        }


# ─────────────────────────────────────────────
# AGENT 7: Multimodal Search Agent
# ─────────────────────────────────────────────

class MultimodalSearchAgent:
    """
    Handles text, voice, and image-based product search.
    Uses OCR for image text extraction and voice-to-text conversion.

    IBM Granite Vision model (if available) for image understanding.
    IBM Langflow Node: 'Multimodal Agent'
    IBM Orchestrate Skill: 'multimodal_search_skill'
    """

    NAME = "Multimodal Search Agent"

    def run_text_search(self, query: str) -> dict:
        """Standard text-based product search with AI enrichment."""
        logger.info("[MultimodalAgent] Text search: %s", query)
        products = search_products(query)
        context = retrieve_context(query, n_results=2)

        prompt = (
            f"User searched for: '{query}'\n"
            f"Found {len(products)} matching products.\n\n"
            f"Summarise the search results and provide shopping guidance. "
            f"What should the user look for when buying '{query}'?"
        )
        summary = generate_response(prompt, context=context)

        return {
            "agent": self.NAME,
            "search_type": "text",
            "query": query,
            "products": products,
            "ai_summary": summary,
            "count": len(products),
            "timestamp": datetime.now().isoformat(),
        }

    def run_image_search(self, image_path: str) -> dict:
        """
        Process an uploaded product image.
        Uses OCR to extract text and IBM Granite Vision for description.
        """
        logger.info("[MultimodalAgent] Image search: %s", image_path)
        extracted_text = ""
        detected_product = ""

        try:
            # OCR text extraction using pytesseract
            import pytesseract
            from PIL import Image
            img = Image.open(image_path)
            extracted_text = pytesseract.image_to_string(img).strip()
            logger.info("OCR extracted: %s", extracted_text[:100])
        except Exception as e:
            logger.warning("OCR failed: %s", e)
            extracted_text = "Image uploaded (OCR unavailable)"

        # Search for products matching extracted text
        search_query = extracted_text[:100] if extracted_text else "electronics"
        products = search_products(search_query) or get_all_products(limit=6)

        prompt = (
            f"A user uploaded a product image. OCR extracted this text: '{extracted_text}'\n\n"
            f"Based on the image content, identify the product category and recommend "
            f"similar products. Suggest what to look for when buying such a product."
        )
        context = retrieve_context(search_query, n_results=2)
        analysis = generate_response(prompt, context=context)

        return {
            "agent": self.NAME,
            "search_type": "image",
            "extracted_text": extracted_text,
            "detected_product": detected_product,
            "products": products[:6],
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
        }

    def run_voice_search(self, audio_path: str = None, text_fallback: str = "") -> dict:
        """
        Process voice input. Converts audio to text, then searches.
        Falls back to text_fallback if audio processing unavailable.
        """
        logger.info("[MultimodalAgent] Voice search")
        transcribed_text = text_fallback

        if audio_path and not text_fallback:
            try:
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                with sr.AudioFile(audio_path) as source:
                    audio = recognizer.record(source)
                transcribed_text = recognizer.recognize_google(audio)
                logger.info("Voice transcribed: %s", transcribed_text)
            except Exception as e:
                logger.warning("Voice recognition failed: %s", e)
                transcribed_text = "Voice search (transcription unavailable)"

        if transcribed_text:
            result = self.run_text_search(transcribed_text)
            result["search_type"] = "voice"
            result["transcribed_text"] = transcribed_text
            return result

        return {
            "agent": self.NAME,
            "search_type": "voice",
            "error": "Could not process voice input.",
            "products": [],
            "timestamp": datetime.now().isoformat(),
        }


# ─────────────────────────────────────────────
# AGENT 8: Shopping Assistant Agent
# ─────────────────────────────────────────────

class ShoppingAssistantAgent:
    """
    Conversational shopping assistant maintaining chat history.
    Can answer arbitrary shopping questions in natural language.

    IBM Granite Model: granite-13b-chat-v2
    IBM Langflow Node: 'Assistant Agent'
    IBM Orchestrate Skill: 'shopping_assistant_skill'
    """

    NAME = "Shopping Assistant Agent"

    def __init__(self):
        self.conversation_history: list = []

    def chat(self, user_message: str) -> dict:
        logger.info("[AssistantAgent] User: %s", user_message)

        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat(),
        })

        # Build conversation context
        history_text = ""
        for turn in self.conversation_history[-6:]:  # last 3 exchanges
            role = "Customer" if turn["role"] == "user" else "Assistant"
            history_text += f"{role}: {turn['content']}\n"

        # RAG context retrieval
        context = retrieve_context(user_message, n_results=2)

        prompt = (
            f"You are a friendly, knowledgeable shopping assistant.\n"
            f"Conversation so far:\n{history_text}\n"
            f"The customer's latest message: {user_message}\n\n"
            f"Respond helpfully and concisely. If asked about a specific product, "
            f"give honest pros and cons. If comparing products, be objective. "
            f"If asked about price, mention if it seems fair or overpriced. "
            f"Keep response conversational and under 200 words."
        )

        # IBM Granite conversational model call
        from shopping_model import GRANITE_CHAT_MODEL
        response = generate_response(prompt, context=context, model_id=GRANITE_CHAT_MODEL)

        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat(),
        })

        return {
            "agent": self.NAME,
            "user_message": user_message,
            "response": response,
            "conversation_length": len(self.conversation_history),
            "timestamp": datetime.now().isoformat(),
        }

    def reset_conversation(self):
        """Clear conversation history."""
        self.conversation_history = []
        return {"status": "Conversation reset."}

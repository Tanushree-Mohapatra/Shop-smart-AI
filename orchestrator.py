# ============================================================
# orchestrator.py – ShopSmart AI
# Central Orchestrator: routes user requests to the appropriate
# agent(s) and combines results.
#
# IBM Orchestrate Integration:
#   This orchestrator mirrors the IBM Orchestrate task-routing
#   capability. In production, this logic is replaced by
#   IBM Orchestrate's workflow engine which automatically delegates
#   to registered Skills (agents) based on intent detection.
#
# IBM Langflow Integration:
#   The orchestrator is the central node in the Langflow workflow:
#   User Query → Intent Detection → Orchestrator → Agent(s)
#   → RAG → IBM Granite → Response Formatter → Frontend
# ============================================================

import re
import logging
from datetime import datetime

from agents import (
    ShoppingKnowledgeAgent,
    ProductComparisonAgent,
    ReviewIntelligenceAgent,
    PredictiveShoppingAgent,
    RecommendationAgent,
    SustainabilityAgent,
    MultimodalSearchAgent,
    ShoppingAssistantAgent,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Singleton agent instances
# ─────────────────────────────────────────────
_knowledge_agent    = ShoppingKnowledgeAgent()
_comparison_agent   = ProductComparisonAgent()
_review_agent       = ReviewIntelligenceAgent()
_prediction_agent   = PredictiveShoppingAgent()
_recommendation_agent = RecommendationAgent()
_sustainability_agent = SustainabilityAgent()
_multimodal_agent   = MultimodalSearchAgent()
_assistant_agent    = ShoppingAssistantAgent()


# ─────────────────────────────────────────────
# Individual agent wrappers (public API)
# ─────────────────────────────────────────────

def shopping_knowledge_agent(question: str) -> dict:
    """Agent 1: Answer shopping knowledge questions."""
    return _knowledge_agent.run(question)


def comparison_agent(product_ids: list) -> dict:
    """Agent 2: Compare multiple products."""
    return _comparison_agent.run(product_ids)


def review_agent(product_id: int) -> dict:
    """Agent 3: Analyse product reviews."""
    return _review_agent.run(product_id)


def prediction_agent(product_id: int) -> dict:
    """Agent 4: Predict price trends and best buy timing."""
    return _prediction_agent.run(product_id)


def recommendation_agent(preferences: dict) -> dict:
    """Agent 5: Generate personalised recommendations."""
    return _recommendation_agent.run(preferences)


def sustainability_agent(product_id: int) -> dict:
    """Agent 6: Evaluate product sustainability."""
    return _sustainability_agent.run(product_id)


def multimodal_agent(query: str = "", image_path: str = None,
                     audio_path: str = None, mode: str = "text") -> dict:
    """Agent 7: Multimodal search (text / image / voice)."""
    if mode == "image" and image_path:
        return _multimodal_agent.run_image_search(image_path)
    elif mode == "voice":
        return _multimodal_agent.run_voice_search(audio_path, text_fallback=query)
    else:
        return _multimodal_agent.run_text_search(query)


def shopping_assistant_agent(message: str) -> dict:
    """Agent 8: Conversational shopping assistant."""
    return _assistant_agent.chat(message)


# ─────────────────────────────────────────────
# Intent Detection
# ─────────────────────────────────────────────

def detect_intent(query: str) -> str:
    """
    Classify the user's intent to route to the correct agent.

    IBM Orchestrate performs this via NLP-powered intent detection.
    In Langflow, this is an 'Intent Classifier' node connected to
    all downstream agent nodes.
    """
    q = query.lower()

    if any(kw in q for kw in ["compare", "vs ", "versus", "difference between", "which is better"]):
        return "comparison"

    if any(kw in q for kw in ["review", "sentiment", "feedback", "rating", "fake review"]):
        return "review"

    if any(kw in q for kw in ["predict", "price drop", "when to buy", "wait", "discount", "sale"]):
        return "prediction"

    if any(kw in q for kw in ["recommend", "suggest", "best for", "under ₹", "budget", "alternatives"]):
        return "recommendation"

    if any(kw in q for kw in ["eco", "green", "sustain", "carbon", "recycle", "environment"]):
        return "sustainability"

    if any(kw in q for kw in ["search", "find", "image", "voice", "upload", "show me"]):
        return "multimodal"

    if any(kw in q for kw in ["what is", "explain", "how to", "guide", "oled", "amoled", "ssd", "5g"]):
        return "knowledge"

    # Default to conversational assistant
    return "assistant"


# ─────────────────────────────────────────────
# Central Orchestrator
# ─────────────────────────────────────────────

def orchestrate(query: str, context_data: dict = None) -> dict:
    """
    Central orchestration function.

    Determines which agent(s) to invoke based on intent detection,
    executes them, and returns a unified response.

    IBM Orchestrate Integration:
        In a live IBM Orchestrate deployment, this function is replaced
        by the Orchestrate workflow engine. Each agent is a registered
        Skill. Orchestrate handles:
        - Intent-based skill selection
        - Multi-skill chaining
        - Conversation memory management
        - Price alert automation
        - Shopping reminder scheduling

    IBM Langflow Integration:
        This function is the 'Orchestrator' node in the Langflow graph.
        Langflow visually represents the routing logic and allows
        no-code modification of agent selection rules.

    Args:
        query:        Natural-language user input.
        context_data: Optional dict with product_ids, preferences, etc.

    Returns:
        dict containing agent name, result, intent, and timestamp.
    """
    if context_data is None:
        context_data = {}

    logger.info("[Orchestrator] Query: '%s' | Context: %s", query, context_data)

    intent = detect_intent(query)
    logger.info("[Orchestrator] Detected intent: %s", intent)

    result = {}

    try:
        if intent == "comparison":
            product_ids = context_data.get("product_ids", [])
            if not product_ids:
                # Extract IDs from context or use defaults
                product_ids = context_data.get("ids", [1, 2])
            result = comparison_agent(product_ids)

        elif intent == "review":
            product_id = context_data.get("product_id", 1)
            result = review_agent(product_id)

        elif intent == "prediction":
            product_id = context_data.get("product_id", 1)
            result = prediction_agent(product_id)

        elif intent == "recommendation":
            preferences = context_data.get("preferences", {})
            if not preferences:
                preferences = {
                    "budget": context_data.get("budget", 50000),
                    "category": context_data.get("category", ""),
                    "purpose": query,
                }
            result = recommendation_agent(preferences)

        elif intent == "sustainability":
            product_id = context_data.get("product_id", 1)
            result = sustainability_agent(product_id)

        elif intent == "multimodal":
            mode = context_data.get("mode", "text")
            result = multimodal_agent(
                query=query,
                image_path=context_data.get("image_path"),
                audio_path=context_data.get("audio_path"),
                mode=mode,
            )

        elif intent == "knowledge":
            result = shopping_knowledge_agent(query)

        else:  # assistant / default
            result = shopping_assistant_agent(query)

    except Exception as e:
        logger.error("[Orchestrator] Agent error: %s", e)
        result = {
            "agent": "Orchestrator",
            "error": str(e),
            "fallback": shopping_assistant_agent(query),
        }

    return {
        "intent": intent,
        "query": query,
        "result": result,
        "orchestrated_at": datetime.now().isoformat(),
    }
